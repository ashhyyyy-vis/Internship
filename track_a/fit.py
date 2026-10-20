"""
track_a/fit.py - Image Power Spectrum Fit & Wiener Filter Model Fitting.

Implements Section 6 (A2 & A3):
1. A2: Fit natural image radial power spectrum:
   log P(f) = log A - alpha * log f, over f in [0.02, 0.4]
2. A3: Fit Wiener model gain:
   G(f) = P(f) / (P(f) + N_eff)
   Minimises squared error to measured H(b) using scipy.optimize.least_squares (parameterized in log space).
3. Predicts theoretical cutoff:
   f_c = (A / N_eff)^(1 / alpha)
4. Evaluates fit R^2 and SD-VAE N_eff scaling against sigma^2.
5. Exports fitted-G JSON contract: results/fitted_g.json (Merge 1 input).
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from PIL import Image
from tqdm import tqdm

from core.radial import frequency_grid, compute_power2d, radial_profile, rgb_to_luminance
from core.bands import band_centers


def fit_image_spectrum(
    manifest_path: str,
    images_dir: str,
    f_min: float = 0.02,
    f_max: float = 0.4,
    limit_images: int = 300,
) -> Tuple[float, float, List[float], List[float]]:
    """
    Compute P(f) for each fit image and fit log P(f) = log A - alpha * log f.
    Returns:
        mean_log_A: float
        mean_alpha: float
        all_log_A: list
        all_alpha: list
    """
    with open(manifest_path, "r") as f:
        manifest: List[str] = json.load(f)
    if limit_images > 0 and len(manifest) > limit_images:
        manifest = manifest[:limit_images]

    n_bins = 32
    r_max = 0.5
    f_bins = np.linspace(0.0, r_max, n_bins + 1)
    f_mids = 0.5 * (f_bins[:-1] + f_bins[1:])

    # Mask frequencies in [f_min, f_max] (skipping DC and near-Nyquist)
    valid_f = (f_mids >= f_min) & (f_mids <= f_max)
    log_f = np.log(f_mids[valid_f])

    all_log_A = []
    all_alpha = []

    for fname in tqdm(manifest, desc="[Track A] Fitting P(f) spectra"):
        img_path = Path(images_dir) / fname
        if not img_path.exists():
            stem = img_path.stem
            img_path = Path(images_dir) / f"{stem}.png"
        if not img_path.exists():
            continue

        pil_img = Image.open(img_path).convert("RGB")
        arr = np.array(pil_img, dtype=np.float32) / 255.0
        y = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

        # 2D orthonormal power
        f2 = np.fft.fftshift(np.fft.fft2(y, norm="ortho"))
        power2d = np.abs(f2) ** 2
        p_profile = radial_profile(power2d, n_bins=n_bins, r_max=r_max)

        p_fit = p_profile[valid_f]
        # Avoid log(0)
        p_fit = np.maximum(p_fit, 1e-12)
        log_p = np.log(p_fit)

        # Linear regression: log_p = c0 - alpha * log_f
        # Polyfit with degree 1: polyfit(log_f, log_p, 1) -> slope = -alpha, intercept = log_A
        slope, intercept = np.polyfit(log_f, log_p, 1)
        all_alpha.append(float(-slope))
        all_log_A.append(float(intercept))

    mean_alpha = float(np.mean(all_alpha))
    mean_log_A = float(np.mean(all_log_A))
    print(f"[Track A] Dataset power spectrum fit: alpha = {mean_alpha:.3f} (std={np.std(all_alpha):.3f}), log_A = {mean_log_A:.3f}")
    return mean_log_A, mean_alpha, all_log_A, all_alpha


def fit_wiener_model(
    transfer_csv_path: str,
    mean_log_A: float,
    mean_alpha: float,
    output_json_path: str,
    psnr_target: float = 40.0,
):
    """
    Fit N_eff for each attack and strength using Wiener model:
    G(f) = P(f) / (P(f) + N_eff)
    where P(f) = A * f^(-alpha).
    """
    df = pd.read_csv(transfer_csv_path)
    df_psnr = df[df["psnr_target"] == psnr_target].copy()

    # 8 band centers
    b_centers = band_centers(n_bands=8, r_max=0.5).numpy()
    A = np.exp(mean_log_A)
    alpha = mean_alpha
    P_bands = A * (b_centers ** (-alpha))

    json_output: Dict[str, Any] = {
        "dataset_alpha": float(alpha),
        "dataset_log_A": float(mean_log_A),
        "psnr_fit": float(psnr_target),
        "attacks": {},
    }

    for attack_name, df_att in df_psnr.groupby("attack"):
        json_output["attacks"][attack_name] = {}
        for strength, df_s in df_att.groupby("strength"):
            df_s = df_s.sort_values("band")
            h_meas = df_s["h_measured"].values

            # Objective in log(N_eff) space to ensure N_eff > 0
            def residuals(log_N):
                N = np.exp(log_N[0])
                G = P_bands / (P_bands + N)
                return G - h_meas

            # Initial guess
            init_log_N = np.log(1e-2)
            res = least_squares(residuals, [init_log_N], method="lm")
            fitted_N = float(np.exp(res.x[0]))

            # Predicted gain G and R^2
            G_pred = P_bands / (P_bands + fitted_N)
            ss_tot = np.sum((h_meas - np.mean(h_meas)) ** 2)
            ss_res = np.sum((h_meas - G_pred) ** 2)
            fit_r2 = float(1.0 - (ss_res / (ss_tot + 1e-12)))

            # Theoretical cutoff f_c where G(f) = 0.5 -> P(f_c) = N_eff -> f_c = (A / N_eff)^(1 / alpha)
            if fitted_N > 0 and A > 0:
                f_c_pred = float((A / fitted_N) ** (1.0 / alpha))
            else:
                f_c_pred = 0.0

            # Measured cutoff f_c: where h_meas crosses 0.5 (linear interpolation)
            f_c_meas = None
            for i in range(len(b_centers) - 1):
                if (h_meas[i] - 0.5) * (h_meas[i + 1] - 0.5) <= 0:
                    t = (0.5 - h_meas[i]) / (h_meas[i + 1] - h_meas[i] + 1e-12)
                    f_c_meas = float(b_centers[i] + t * (b_centers[i + 1] - b_centers[i]))
                    break
            if f_c_meas is None:
                f_c_meas = float(b_centers[0]) if h_meas[0] < 0.5 else float(b_centers[-1])

            json_output["attacks"][attack_name][str(strength)] = {
                "N_eff": fitted_N,
                "fit_r2": max(fit_r2, 0.0),
                "f_c_pred": f_c_pred,
                "f_c_meas": f_c_meas,
            }
            print(f"[Track A] {attack_name} s={strength}: N_eff={fitted_N:.6f}, R^2={fit_r2:.3f}, f_c_pred={f_c_pred:.3f}, f_c_meas={f_c_meas:.3f}")

    out_path = Path(output_json_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(json_output, f, indent=2)

    print(f"\n[Track A] Exported fitted Wiener model parameters to {output_json_path} (Merge 1 ready).")


def run():
    parser = argparse.ArgumentParser(description="Track A: Fit Spectrum and Wiener Model")
    parser.add_argument("--manifest", type=str, default="data/manifests/fit_manifest.json")
    parser.add_argument("--images_dir", type=str, default="data/processed/fit")
    parser.add_argument("--transfer_csv", type=str, default="results/track_a_transfer.csv")
    parser.add_argument("--out_json", type=str, default="results/fitted_g.json")
    parser.add_argument("--psnr", type=float, default=40.0)
    args = parser.parse_args()

    log_A, alpha, _, _ = fit_image_spectrum(args.manifest, args.images_dir)
    fit_wiener_model(args.transfer_csv, log_A, alpha, args.out_json, psnr_target=args.psnr)


if __name__ == "__main__":
    run()
