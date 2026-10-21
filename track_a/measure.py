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
    limit_images: int = 300,
):
    device = torch.device(device_str)
    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "r") as f:
        manifest: List[str] = json.load(f)

    if limit_images > 0 and len(manifest) > limit_images:
        manifest = manifest[:limit_images]

    print(f"[Track A] Loaded {len(manifest)} images from {manifest_path}")

    # Initialize attack objects
    attack_objects = [get_attack_family(att) for att in attack_names]

    # Pre-generate band masks (8, 256, 256)
    masks = band_masks(256, 256, n_bands=8, r_max=0.5, shifted=True, device=device)

    # Accumulate results
    results = []

    for att in attack_objects:
        print(f"\n[Track A] Measuring attack family: {att.name}")
        for strength in att.strengths:
            print(f"  Strength: {strength}")
            for psnr in psnr_targets:
                for band_idx in range(8):
                    e_in_list = []
                    e_out_list = []

                    for idx, fname in enumerate(tqdm(manifest, desc=f"Band {band_idx} @ {psnr}dB", leave=False)):
                        img_path = resolve_image_path(images_dir, fname)

                        # Load 256x256 image in [0, 1]
                        pil_img = Image.open(img_path).convert("RGB")
                        img_tensor = (
                            torch.from_numpy(np.array(pil_img, dtype=np.float32) / 255.0)
                            .permute(2, 0, 1)
                            .unsqueeze(0)
                            .to(device)
                        )

                        # Embed probe
                        seed = 1000 + idx
                        x_w, probe_added = embed_probe(
                            img_tensor, band_idx=band_idx, psnr_db=psnr, seed=seed, round_8bit=True
                        )

                        # Attack both images with exact same seed
                        with torch.no_grad():
                            a_x = att(img_tensor, strength=strength, seed=seed)
                            a_xw = att(x_w, strength=strength, seed=seed)

                        # Compute luminance deltas
                        delta_in = rgb_to_luminance(x_w - img_tensor).squeeze(0)
                        delta_out = rgb_to_luminance(a_xw - a_x).squeeze(0)

                        # Band energy for the probe band
                        e_in_band = compute_band_energy(delta_in, masks)[band_idx].item()
                        e_out_band = compute_band_energy(delta_out, masks)[band_idx].item()

                        e_in_list.append(e_in_band)
                        e_out_list.append(e_out_band)

                    e_in_arr = np.array(e_in_list)
                    e_out_arr = np.array(e_out_list)

                    # Transfer function: H(b) = sqrt(mean(E_out / E_in))
                    valid = e_in_arr > 1e-12
                    if np.any(valid):
                        ratio = e_out_arr[valid] / e_in_arr[valid]
                        h_val = float(np.sqrt(np.mean(ratio)))
                    else:
                        h_val = 0.0

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
                    df = pd.DataFrame(results)
                    df.to_csv(out_path, index=False)

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
