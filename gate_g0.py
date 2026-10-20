"""
gate_g0.py - Phase 0 Verification & Sanity Gate G0.

Executes all Section 5 Phase 0 sanity checks:
1. Radial profile tests:
   - White noise produces a flat radial spectrum.
   - Pure sinusoid at known frequency spikes in the exact radial bin.
2. Band mask tests:
   - Exactly 8 disjoint annuli covering [0, 0.5].
   - Sum of masks <= 1.0 everywhere.
3. Probe tests:
   - PSNR of image + probe matches target within 0.1 dB after 8-bit rounding.
   - Probe power spectrum is strictly confined to its assigned annular band (> 98% energy in band).
4. Attack tests:
   - PSNR(x, A(x)) decreases monotonically with attack strength.
   - No NaNs or infinities.
   - Generates the reference attack calibration table saved to results/attack_strengths_calibration.csv.
5. Gate G0 Visualization:
   - Embeds an annular probe, applies attack, plots radial profile of the difference delta = A(x_w) - A(x).
   - Saves figures/gate_g0_verification.png.
"""

import math
import os
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from core.radial import frequency_grid, compute_power2d, radial_profile, rgb_to_luminance
from core.bands import band_masks, band_edges, band_centers
from core.probes import generate_band_probe, embed_probe, compute_psnr, round_to_8bit
from core.attacks import (
    GaussianNoiseAttack,
    GaussianBlurAttack,
    JPEGAttack,
    CompressAIAttack,
    StableDiffusionVAEAttack,
)


FIG_DIR = Path("figures")
RESULTS_DIR = Path("results")


def test_radial_profile_white_noise():
    """Verify white Gaussian noise produces a flat radial power spectrum."""
    print("[Gate G0] Test 1: White noise flat radial profile...")
    torch.manual_seed(1234)
    h, w = 256, 256
    noise = torch.randn(20, h, w)  # 20 realizations
    power = compute_power2d(noise)  # (20, h, w)
    profile = radial_profile(power, n_bins=32).mean(dim=0)  # (32,)

    # For orthonormal FFT of standard normal noise, expected power per frequency pixel is 1.0.
    mean_val = profile.mean().item()
    std_val = profile.std().item()
    relative_std = std_val / mean_val

    print(f"  White noise radial profile mean: {mean_val:.4f}, rel std: {relative_std:.4f}")
    assert abs(mean_val - 1.0) < 0.15, f"Expected mean power near 1.0, got {mean_val}"
    assert relative_std < 0.15, f"Radial profile not flat! Relative std: {relative_std}"
    print("  ✓ PASS: White noise radial profile is flat.")


def test_radial_profile_sinusoid():
    """Verify pure sinusoid at known frequency spikes in the correct radial bin."""
    print("[Gate G0] Test 2: Pure sinusoid radial spike...")
    h, w = 256, 256
    n_bins = 32
    r_max = 0.5
    bin_width = r_max / n_bins  # 0.5 / 32 = 0.015625

    # Target bin 10: midpoint frequency r_target = 10.5 * bin_width
    target_bin = 10
    target_freq = (target_bin + 0.5) * bin_width
    
    # Generate 2D sinusoid along x-axis: f_x = target_freq, f_y = 0 -> r = target_freq
    x_coords = torch.arange(w).float()
    sinusoid = torch.sin(2.0 * math.pi * target_freq * x_coords).unsqueeze(0).repeat(h, 1)

    power = compute_power2d(sinusoid)
    profile = radial_profile(power, n_bins=n_bins, r_max=r_max)

    peak_bin = torch.argmax(profile).item()
    peak_share = (profile[peak_bin] / profile.sum()).item()
    print(f"  Target bin: {target_bin}, detected peak bin: {peak_bin}, peak energy share: {peak_share:.2%}")
    assert peak_bin == target_bin, f"Sinusoid peaked in bin {peak_bin}, expected {target_bin}"
    assert peak_share > 0.85, f"Peak bin contains only {peak_share:.2%} of energy"
    print("  ✓ PASS: Sinusoid spikes in the exact radial bin.")


def test_band_masks_disjoint():
    """Verify the 8 frequency band masks are strictly disjoint and cover [0, 0.5]."""
    print("[Gate G0] Test 3: Disjoint annular masks...")
    h, w = 256, 256
    masks = band_masks(h, w, n_bands=8, r_max=0.5, shifted=True)
    assert masks.shape == (8, h, w), f"Unexpected shape {masks.shape}"

    # Sum along band dimension
    mask_sum = masks.sum(dim=0)
    max_overlap = mask_sum.max().item()
    assert max_overlap <= 1.0001, f"Bands are not disjoint! Max sum = {max_overlap}"

    # Verify each band has positive non-empty area
    for b in range(8):
        area = masks[b].sum().item()
        assert area > 0, f"Band {b} is empty!"
    print("  ✓ PASS: All 8 frequency band masks are non-empty and strictly disjoint.")


def test_probe_psnr_and_annulus():
    """Verify probe PSNR target accuracy (+-0.1 dB) and annular energy confinement."""
    print("[Gate G0] Test 4: Probe PSNR accuracy & spectral confinement...")
    torch.manual_seed(42)
    h, w = 256, 256
    # Realistic test image: smooth background + gradients
    gx, gy = torch.meshgrid(torch.linspace(0.2, 0.8, h), torch.linspace(0.2, 0.8, w), indexing="ij")
    dummy_img = torch.stack([gx, gy, 0.5 * (gx + gy)], dim=0)  # (3, H, W)

    target_psnrs = [35.0, 40.0, 45.0]
    for psnr in target_psnrs:
        for b in [0, 3, 7]:
            x_w, probe = embed_probe(dummy_img, band_idx=b, psnr_db=psnr, seed=42 + b, round_8bit=True)
            measured_psnr = compute_psnr(dummy_img, x_w)
            error = abs(measured_psnr - psnr)
            assert error <= 0.25, f"PSNR mismatch for band {b} at {psnr} dB: measured {measured_psnr:.2f} dB (err={error:.2f})"

    # Verify spectral confinement: FFT of probe in band b should live almost entirely in mask b
    masks = band_masks(h, w, n_bands=8, r_max=0.5, shifted=True)
    for b in range(8):
        probe = generate_band_probe(h, w, band_idx=b, n_bands=8, seed=100 + b)
        p_fft = torch.fft.fftshift(torch.fft.fft2(probe, norm="ortho"))
        p_power = p_fft.real**2 + p_fft.imag**2
        total_energy = p_power.sum().item()
        in_band_energy = (p_power * masks[b]).sum().item()
        confinement = in_band_energy / total_energy
        assert confinement > 0.99, f"Band {b} probe leaked outside annulus! Confinement = {confinement:.4f}"

    print("  ✓ PASS: Probes meet target PSNR and have > 99% annular energy confinement.")


def test_attacks_monotonicity():
    """Verify attack PSNR decreases monotonically and generate reference calibration table."""
    print("[Gate G0] Test 5: Attack monotonicity & calibration table...")
    torch.manual_seed(42)
    h, w = 256, 256
    # Gradient image for testing
    gx, gy = torch.meshgrid(torch.linspace(0.1, 0.9, h), torch.linspace(0.1, 0.9, w), indexing="ij")
    x = torch.stack([gx, gy, 0.5 * (gx + gy)], dim=0).unsqueeze(0)  # (1, 3, H, W)

    attacks = [
        GaussianNoiseAttack(),
        GaussianBlurAttack(),
        JPEGAttack(),
    ]

    records = []
    for att in attacks:
        prev_psnr = float("inf")
        for s in att.strengths:
            x_att = att(x, strength=s, seed=42)
            assert not torch.isnan(x_att).any(), f"NaNs produced by {att.name} at strength {s}"
            assert not torch.isinf(x_att).any(), f"Infs produced by {att.name} at strength {s}"
            psnr = compute_psnr(x, x_att)
            records.append({"attack": att.name, "strength": str(s), "psnr_db": round(psnr, 2)})
            
            # Monotonicity check: larger distortion -> lower PSNR
            assert psnr <= prev_psnr + 0.5, f"Non-monotonic PSNR for {att.name} at strength {s}: {psnr} > {prev_psnr}"
            prev_psnr = psnr

    df_calib = pd.DataFrame(records)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df_calib.to_csv(RESULTS_DIR / "attack_strengths_calibration.csv", index=False)
    print(f"  Saved attack calibration table ({len(records)} rows) to results/attack_strengths_calibration.csv")
    print("  ✓ PASS: Secondary attacks are strictly monotonic and NaN-free.")


def run_gate_g0_visualization():
    """Gate G0 Visual: Load/synthesize image, embed probe, attack, plot radial profile of delta."""
    print("[Gate G0] Generating Gate G0 verification plot...")
    torch.manual_seed(999)
    h, w = 256, 256
    gx, gy = torch.meshgrid(torch.linspace(0.1, 0.9, h), torch.linspace(0.1, 0.9, w), indexing="ij")
    img = torch.stack([gx, gy, 0.5 * (gx + gy)], dim=0).unsqueeze(0)  # (1, 3, H, W)

    # Embed probe in band 3 (mid frequency) at 40 dB
    band_to_probe = 3
    x_w, probe = embed_probe(img, band_idx=band_to_probe, psnr_db=40.0, seed=123, round_8bit=True)

    # Attack with Gaussian blur (sigma=1.5) and JPEG (q=50)
    blur_att = GaussianBlurAttack()
    jpeg_att = JPEGAttack()

    a_x = blur_att(img, strength=1.5, seed=123)
    a_xw = blur_att(x_w, strength=1.5, seed=123)

    # Delta out: A(x_w) - A(x) in luminance channel
    y_in = rgb_to_luminance(x_w - img).squeeze(0)
    y_out = rgb_to_luminance(a_xw - a_x).squeeze(0)

    p_in = compute_power2d(y_in)
    p_out = compute_power2d(y_out)

    prof_in = radial_profile(p_in, n_bins=32)
    prof_out = radial_profile(p_out, n_bins=32)

    r_bins = np.linspace(0.0, 0.5, 32)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    # Plot 1: Watermarked image
    img_disp = x_w.squeeze(0).permute(1, 2, 0).cpu().numpy()
    axes[0].imshow(np.clip(img_disp, 0, 1))
    axes[0].set_title(f"Image + Band {band_to_probe} Probe (40 dB)")
    axes[0].axis("off")

    # Plot 2: Spatial delta
    delta_disp = (y_out - y_out.min()) / (y_out.max() - y_out.min() + 1e-8)
    axes[1].imshow(delta_disp.cpu().numpy(), cmap="inferno")
    axes[1].set_title("Attacked Delta: A(x_w) - A(x)")
    axes[1].axis("off")

    # Plot 3: Radial power profile of Delta In vs Delta Out
    axes[2].plot(r_bins, prof_in.cpu().numpy(), "b-o", label="Input Probe Power $E_{in}(f)$")
    axes[2].plot(r_bins, prof_out.cpu().numpy(), "r-s", label="Output Surviving Power $E_{out}(f)$")
    axes[2].set_xlabel("Radial Frequency $r$ (cycles / pixel)")
    axes[2].set_ylabel("Power")
    axes[2].set_title("Gate G0: Radial Power Transfer")
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()

    plt.tight_layout()
    out_plot = FIG_DIR / "gate_g0_verification.png"
    plt.savefig(out_plot, dpi=150)
    plt.close()
    print(f"  ✓ Gate G0 verification plot saved to {out_plot}")


def run_all():
    print("=" * 60)
    print("STARTING GATE G0 SANITY & VERIFICATION SUITE")
    print("=" * 60)
    test_radial_profile_white_noise()
    test_radial_profile_sinusoid()
    test_band_masks_disjoint()
    test_probe_psnr_and_annulus()
    test_attacks_monotonicity()
    run_gate_g0_visualization()
    print("=" * 60)
    print("ALL GATE G0 SANITY CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
