"""
track_a/measure.py - Measure Empirical VAE & Attack Transfer Function H(band).

Implements Section 6 (A1):
- For every attack x strength x probe annulus (8 bands) x fit image (300 images):
  - delta_in = x_w - x (luminance, after rounding)
  - delta_out = A(x_w) - A(x) (same seed, luminance, after rounding)
  - Compute radial energy of each: E_in(b), E_out(b)
  - H(b) = sqrt(mean_{images} (E_out / E_in))
- Sweeps at PSNR 35, 40, 45 dB
- Writes tidy CSV: results/track_a_transfer.csv
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any

import torch
import numpy as np
import pandas as pd
from tqdm import tqdm
from PIL import Image

from core.radial import rgb_to_luminance, compute_power2d
from core.bands import band_masks
from core.probes import embed_probe
from core.dataset_utils import resolve_image_path
from core.attacks import (
    get_attack_family,
    CompressAIAttack,
    StableDiffusionVAEAttack,
    GaussianNoiseAttack,
    GaussianBlurAttack,
    JPEGAttack,
)


def compute_band_energy(y: torch.Tensor, masks: torch.Tensor) -> torch.Tensor:
    """
    Compute radial energy inside each of the 8 disjoint bands for a 2D luminance signal y.
    y: shape (H, W) or (B, H, W)
    masks: shape (8, H, W)
    Returns: shape (8,) or (B, 8) energy per band
    """
    power = compute_power2d(y)  # centered orthonormal power
    # Multiply power by each band mask and sum
    if power.dim() == 2:
        # (8, H, W) * (1, H, W) -> sum over (-2, -1)
        energies = (masks * power.unsqueeze(0)).sum(dim=(-2, -1))
    else:
        # (B, 1, H, W) * (1, 8, H, W)
        energies = (masks.unsqueeze(0) * power.unsqueeze(1)).sum(dim=(-2, -1))
    return energies


def run_measure_sweep(
    manifest_path: str,
    images_dir: str,
    output_csv: str,
    attack_names: List[str] = ["compressai", "sd_vae"],
    psnr_targets: List[float] = [35.0, 40.0, 45.0],
    device_str: str = "cuda" if torch.cuda.is_available() else "cpu",
    limit_images: int = 64,
    batch_size: int = 16,
):
    device = torch.device(device_str)
    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "r") as f:
        manifest: List[str] = json.load(f)

    if limit_images > 0 and len(manifest) > limit_images:
        manifest = manifest[:limit_images]

    print(f"[Track A] Preloading {len(manifest)} images on {device}...")
    loaded_imgs = []
    for fname in manifest:
        img_path = resolve_image_path(images_dir, fname)
        pil_img = Image.open(img_path).convert("RGB")
        arr = torch.from_numpy(np.array(pil_img, dtype=np.float32) / 255.0).permute(2, 0, 1)
        loaded_imgs.append(arr)
    all_imgs = torch.stack(loaded_imgs, dim=0).to(device)  # (N, 3, 256, 256)
    n_images = len(all_imgs)
    print(f"[Track A] Preloaded {n_images} images. Processing in GPU batches of {batch_size}...")

    # Initialize attack objects
    attack_objects = [get_attack_family(att) for att in attack_names]

    # Pre-generate band masks (8, 256, 256)
    masks = band_masks(256, 256, n_bands=8, r_max=0.5, shifted=True, device=device)

    # Accumulate results
    results = []

    for att in attack_objects:
        print(f"\n[Track A] Measuring attack family: {att.name}")
        for strength in att.strengths:
            for psnr in psnr_targets:
                for band_idx in range(8):
                    e_in_list = []
                    e_out_list = []

                    for start_idx in range(0, n_images, batch_size):
                        end_idx = min(start_idx + batch_size, n_images)
                        batch_x = all_imgs[start_idx:end_idx]
                        seed = 1000 + start_idx

                        # Batched probe embed
                        x_w, _ = embed_probe(
                            batch_x, band_idx=band_idx, psnr_db=psnr, seed=seed, round_8bit=True
                        )

                        # Batched attacks
                        with torch.no_grad():
                            a_x = att(batch_x, strength=strength, seed=seed)
                            a_xw = att(x_w, strength=strength, seed=seed)

                        # Batched luminance deltas
                        delta_in = rgb_to_luminance(x_w - batch_x)    # (B, H, W)
                        delta_out = rgb_to_luminance(a_xw - a_x)      # (B, H, W)

                        # Band energy for the probe band (B, 8) -> extract column band_idx
                        e_in_b = compute_band_energy(delta_in, masks)[:, band_idx].cpu().numpy()
                        e_out_b = compute_band_energy(delta_out, masks)[:, band_idx].cpu().numpy()

                        e_in_list.extend(e_in_b)
                        e_out_list.extend(e_out_b)

                    e_in_arr = np.array(e_in_list)
                    e_out_arr = np.array(e_out_list)

                    valid = e_in_arr > 1e-12
                    h_val = float(np.sqrt(np.mean(e_out_arr[valid] / e_in_arr[valid]))) if np.any(valid) else 0.0

                    row = {
                        "attack": att.name,
                        "strength": str(strength),
                        "psnr_target": psnr,
                        "band": band_idx,
                        "h_measured": h_val,
                        "mean_e_in": float(np.mean(e_in_arr)),
                        "mean_e_out": float(np.mean(e_out_arr)),
                        "n_samples": len(e_in_list),
                    }
                    results.append(row)

                    # Incremental flush to CSV
                    pd.DataFrame(results).to_csv(out_path, index=False)

    print(f"\n[Track A] Finished sweep! Saved {len(results)} rows to {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track A: Transfer Function Measurement")
    parser.add_argument("--manifest", type=str, default="data/manifests/fit_manifest.json")
    parser.add_argument("--images_dir", type=str, default="data/processed/fit")
    parser.add_argument("--out", type=str, default="results/track_a_transfer.csv")
    parser.add_argument("--attacks", nargs="+", default=["compressai", "sd_vae"])
    parser.add_argument("--limit", type=int, default=300)
    args = parser.parse_args()

    run_measure_sweep(
        manifest_path=args.manifest,
        images_dir=args.images_dir,
        output_csv=args.out,
        attack_names=args.attacks,
        limit_images=args.limit,
    )
