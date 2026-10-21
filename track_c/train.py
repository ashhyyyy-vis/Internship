"""
track_c/train.py - Training Pipeline for Learned Watermark Encoder & Controls.

Implements Section 8 (C4 & C5):
- Loss: BCEWithLogitsLoss (weight 1.0) + MSE(x, x_w) (weight 1.0)
- Adam optimizer with Cosine Annealing learning rate schedule
- Training curriculum: Identity distortion first, progressing to full mixture / surrogate
- Separate bit accuracy logging per noise type
- Saves model checkpoint and learned band allocation vector g_b after every epoch
- Supports:
  1. 100-image sanity overfit test (--overfit_100)
  2. Fixed-band controls (--fixed_regime low / mid / high)
  3. Main model Stage 1 (without surrogate)
  4. Main model Stage 2 (with fitted-G surrogate)
"""

import argparse
import json
import math
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from tqdm import tqdm

from track_c.model import WatermarkEncoder, WatermarkDecoder
from track_c.noise_layers import NoiseMixtureLayer
from core.dataset_utils import resolve_image_path, CANDIDATE_DIRS


class COCODataset(Dataset):
    def __init__(self, manifest_path: str, images_dir: str, n_bits: int = 32, max_samples: int = -1):
        self.n_bits = n_bits
        manifest_files = []
        if Path(manifest_path).exists():
            with open(manifest_path, "r") as f:
                manifest_files = json.load(f)

        valid_items: List[Path] = []
        for fname in manifest_files:
            try:
                p = resolve_image_path(images_dir, fname)
                valid_items.append(p)
                if max_samples > 0 and len(valid_items) >= max_samples:
                    break
            except FileNotFoundError:
                continue

        if len(valid_items) == 0:
            # Fallback: scan images_dir or candidate dirs for any images
            search_dirs = [Path(images_dir)] + CANDIDATE_DIRS
            for s_dir in search_dirs:
                if s_dir.exists():
                    found = list(s_dir.glob("*.png")) + list(s_dir.glob("*.jpg"))
                    if len(found) > 0:
                        valid_items = found[:max_samples] if max_samples > 0 else found
                        print(f"[COCODataset] Manifest images not found in {images_dir}. Using {len(valid_items)} images from {s_dir}.")
                        break

        if len(valid_items) == 0:
            raise FileNotFoundError(
                f"Could not find any training images in {images_dir} or fallback directories {CANDIDATE_DIRS}. "
                "Please run data_prep.py or verify dataset extraction."
            )

        self.image_paths = valid_items
        print(f"[COCODataset] Initialized with {len(self.image_paths)} images.")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        img_path = self.image_paths[idx]
        pil_img = Image.open(img_path).convert("RGB")
        if pil_img.size != (256, 256):
            pil_img = pil_img.resize((256, 256), Image.Resampling.BICUBIC)
        arr = torch.from_numpy(np.array(pil_img, dtype=np.float32) / 255.0).permute(2, 0, 1)

        # Random 32-bit message
        msg = torch.randint(0, 2, (self.n_bits,), dtype=torch.float32)
        return arr, msg


import numpy as np


def train_epoch(
    encoder: nn.Module,
    decoder: nn.Module,
    noise_layer: nn.Module,
    loader: DataLoader,
    optimizer: optim.Optimizer,
    bce_loss: nn.Module,
    device: torch.device,
    curriculum_mode: str = "mixture",
) -> Tuple[float, float, float]:
    encoder.train()
    decoder.train()

    total_loss = 0.0
    total_bce = 0.0
    total_bit_acc = 0.0
    n_batches = 0

    for imgs, msgs in loader:
        imgs = imgs.to(device)
        msgs = msgs.to(device)

        optimizer.zero_grad()

        # Encode
        x_w, res = encoder(imgs, msgs)

        # Apply noise layer
        x_att = noise_layer(x_w, imgs, mode=curriculum_mode)

        # Decode
        logits = decoder(x_att)

        loss_bce = bce_loss(logits, msgs)
        loss_mse = F.mse_loss(x_w, imgs)
        loss = loss_bce + 10.0 * loss_mse

        loss.backward()
        optimizer.step()

        pred_bits = (logits > 0.0).float()
        bit_acc = (pred_bits == msgs).float().mean().item()

        total_loss += loss.item()
        total_bce += loss_bce.item()
        total_bit_acc += bit_acc
        n_batches += 1

    return total_loss / n_batches, total_bce / n_batches, total_bit_acc / n_batches


def run_training():
    parser = argparse.ArgumentParser(description="Track C: Learned Encoder Training")
    parser.add_argument("--manifest", type=str, default="data/manifests/train_manifest.json")
    parser.add_argument("--images_dir", type=str, default="data/processed/train")
    parser.add_argument("--save_dir", type=str, default="checkpoints/main_stage1")
    parser.add_argument("--fixed_regime", type=str, default=None, choices=[None, "low", "mid", "high"])
    parser.add_argument("--surrogate_json", type=str, default=None)
    parser.add_argument("--psnr", type=float, default=40.0)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--overfit_100", action="store_true")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    save_path = Path(args.save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    max_samples = 100 if args.overfit_100 else -1
    dataset = COCODataset(args.manifest, args.images_dir, n_bits=32, max_samples=max_samples)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=True)

    encoder = WatermarkEncoder(n_bits=32, psnr_target=args.psnr, fixed_regime=args.fixed_regime).to(device)
    decoder = WatermarkDecoder(n_bits=32).to(device)
    noise_layer = NoiseMixtureLayer(fitted_g_json_path=args.surrogate_json).to(device)

    params = list(encoder.parameters()) + list(decoder.parameters())
    optimizer = optim.Adam(params, lr=args.lr)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-5)
    bce_loss = nn.BCEWithLogitsLoss()

    # Resume from checkpoint if it exists
    checkpoint_file = save_path / "latest_checkpoint.pt"
    history_file = save_path / "training_history.json"
    start_epoch = 1
    history = []

    if checkpoint_file.exists():
        print(f"[Track C] Found existing checkpoint at {checkpoint_file}. Resuming training...")
        ckpt = torch.load(checkpoint_file, map_location=device)
        encoder.load_state_dict(ckpt["encoder"])
        decoder.load_state_dict(ckpt["decoder"])
        if "optimizer" in ckpt:
            optimizer.load_state_dict(ckpt["optimizer"])
        start_epoch = ckpt.get("epoch", 0) + 1
        if history_file.exists():
            with open(history_file, "r") as f:
                history = json.load(f)
        print(f"[Track C] Successfully resumed! Starting from epoch {start_epoch}/{args.epochs}")

    if start_epoch > args.epochs:
        print(f"[Track C] Model already trained for {args.epochs} epochs. Nothing to do!")
        return

    print(f"[Track C] Training for epochs {start_epoch} to {args.epochs} on {device} (Regime: {args.fixed_regime})...")

    best_acc = 0.0
    for epoch in range(start_epoch, args.epochs + 1):
        # Curriculum: Identity for first 3 epochs, then mixture
        if args.overfit_100 or epoch <= 3:
            mode = "identity"
        else:
            mode = "mixture"

        loss, bce, bit_acc = train_epoch(encoder, decoder, noise_layer, loader, optimizer, bce_loss, device, mode)
        scheduler.step()

        # Current band allocations
        g = encoder.band_layer.get_g().detach().cpu().numpy().tolist()

        print(f"Epoch {epoch:02d}/{args.epochs:02d} [{mode}] | Loss: {loss:.4f} | BCE: {bce:.4f} | Bit Acc: {bit_acc:.2%}")
        print(f"  g_b: {[round(x, 3) for x in g]}")

        history.append({
            "epoch": epoch,
            "loss": loss,
            "bce": bce,
            "bit_acc": bit_acc,
            "g": g,
        })

        # Save checkpoint directly to save_dir (in Drive) after EVERY epoch
        ckpt_data = {
            "epoch": epoch,
            "encoder": encoder.state_dict(),
            "decoder": decoder.state_dict(),
            "g": g,
            "optimizer": optimizer.state_dict(),
        }
        torch.save(ckpt_data, checkpoint_file)
        if bit_acc > best_acc:
            best_acc = bit_acc
            torch.save(ckpt_data, save_path / "best_checkpoint.pt")

        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

    print(f"[Track C] Training complete! All checkpoints saved safely to {save_path}")


if __name__ == "__main__":
    run_training()
