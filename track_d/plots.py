"""
track_d/plots.py - Figure Generation and Visualization from Benchmark CSVs.

Implements Section 9 & Section 12:
- Fig 1: Measured vs Fitted Transfer Functions H(f) across strengths (Track A)
- Fig 2: Predicted vs Measured Cutoff Frequency f_c & N_eff vs sigma^2 scaling (Track A)
- Fig 3: Classical Band x Strength Bit Accuracy Heatmaps overlaid with f_c curve (Track B)
- Fig 4: Learned Dynamic Band Allocation Weights g_b vs Attack Strength (Track C)
"""

import json
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core.bands import band_centers


FIG_DIR = Path("figures")


def plot_fig1_transfer_functions(
    transfer_csv: str = "results/track_a_transfer.csv",
    fitted_json: str = "results/fitted_g.json",
    out_file: str = "figures/fig1_transfer_functions.png",
):
    """Fig 1: Measured vs fitted transfer functions H(f)."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(transfer_csv)
    with open(fitted_json, "r") as f:
        fitted = json.load(f)

    # Filter to target PSNR (default 40.0 dB)
    psnr_target = fitted.get("psnr_fit", 40.0)
    if "psnr_target" in df.columns:
        if (df["psnr_target"] == psnr_target).any():
            df = df[df["psnr_target"] == psnr_target]
        else:
            first_p = df["psnr_target"].iloc[0]
            df = df[df["psnr_target"] == first_p]

    b_mids = band_centers(8, 0.5).numpy()
    attacks = df["attack"].unique()

    fig, axes = plt.subplots(1, len(attacks), figsize=(6 * len(attacks), 5), squeeze=False)

    for ax, att in zip(axes[0], attacks):
        df_att = df[df["attack"] == att]
        strengths = df_att["strength"].unique()

        for s in strengths:
            sub = df_att[df_att["strength"] == s].sort_values("band")
            ax.plot(b_mids, sub["h_measured"], "o-", label=f"Meas s={s}")

            # Plot fitted Wiener curve if available
            s_data = fitted.get("attacks", {}).get(att, {}).get(str(s), {})
            if "N_eff" in s_data:
                n_eff = s_data["N_eff"]
                alpha = fitted["dataset_alpha"]
                A = np.exp(fitted["dataset_log_A"])
                f_dense = np.linspace(0.01, 0.5, 100)
                P_f = A * (f_dense ** (-alpha))
                G_dense = P_f / (P_f + n_eff)
                ax.plot(f_dense, G_dense, "--", alpha=0.7)

        ax.set_title(f"Transfer Function: {att}")
        ax.set_xlabel("Frequency (cycles/pixel)")
        ax.set_ylabel("H(band)")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(out_file, dpi=180)
    plt.close()
    print(f"[Plots] Saved Fig 1 to {out_file}")


def plot_fig2_cutoff_prediction(
    fitted_json: str = "results/fitted_g.json",
    out_file: str = "figures/fig2_cutoff_and_scaling.png",
):
    """Fig 2: Predicted vs measured cutoff f_c & N_eff vs sigma^2."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(fitted_json, "r") as f:
        fitted = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    preds = []
    meas = []
    labels = []

    for att, s_dict in fitted.get("attacks", {}).items():
        for s, vals in s_dict.items():
            if "f_c_pred" in vals and "f_c_meas" in vals:
                preds.append(vals["f_c_pred"])
                meas.append(vals["f_c_meas"])
                labels.append(f"{att}_{s}")

    # Plot 1: Scatter with y = x line
    axes[0].scatter(preds, meas, color="navy", s=50, zorder=3)
    lims = [0.0, 0.5]
    axes[0].plot(lims, lims, "r--", label="y = x", zorder=2)
    axes[0].set_xlabel("Predicted Cutoff $f_c$")
    axes[0].set_ylabel("Measured Cutoff $f_c$")
    axes[0].set_title("Theoretical vs Measured Cutoff")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Plot 2: SD VAE N_eff vs sigma^2
    sd_strengths = fitted.get("attacks", {}).get("sd_vae", {})
    sigmas = []
    n_effs = []
    for s_str, vals in sd_strengths.items():
        try:
            s_val = float(s_str)
            sigmas.append(s_val ** 2)
            n_effs.append(vals["N_eff"])
        except ValueError:
            pass

    if len(sigmas) > 1:
        axes[1].plot(sigmas, n_effs, "g-o", linewidth=2)
        axes[1].set_xlabel("Noise Variance $\sigma^2$")
        axes[1].set_ylabel("Fitted $N_{eff}$")
        axes[1].set_title("Wiener Noise Parameter Scaling on SD VAE")
        axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_file, dpi=180)
    plt.close()
    print(f"[Plots] Saved Fig 2 to {out_file}")


def plot_fig3_classical_heatmaps(
    sweep_csv: str = "results/track_b_sweep.csv",
    fitted_json: Optional[str] = "results/fitted_g.json",
    out_file: str = "figures/fig3_classical_heatmaps.png",
):
    """Fig 3: Heatmap of Band x Strength Bit Accuracy with f_c overlay."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(sweep_csv, low_memory=False)
    df_clean = df[df["attack"] != "none"].copy()

    # Load cutoff data if available
    fitted = None
    if fitted_json and Path(fitted_json).exists():
        with open(fitted_json, "r") as f:
            fitted = json.load(f)

    attacks = df_clean["attack"].unique()
    fig, axes = plt.subplots(1, len(attacks), figsize=(7 * len(attacks), 5.5), squeeze=False)

    for ax, att in zip(axes[0], attacks):
        sub = df_clean[df_clean["attack"] == att].copy()
        sub["strength_num"] = pd.to_numeric(sub["strength"], errors="coerce")
        sub = sub.sort_values(["strength_num", "band"])
        pivot = sub.groupby(["strength_num", "band"])["bit_acc"].mean().unstack()

        cax = ax.imshow(pivot.values, cmap="viridis", vmin=0.5, vmax=1.0, aspect="auto", origin="lower")
        ax.set_xticks(range(8))
        ax.set_xticklabels([f"B{i}" for i in range(8)], fontsize=10)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([str(s) for s in pivot.index], fontsize=10)
        ax.set_xlabel("Frequency Band (B0: Low -> B7: High)", fontsize=11)
        ax.set_ylabel(f"Attack Strength ({att})", fontsize=11)
        ax.set_title(f"Classical Watermark Accuracy: {att}", fontsize=12, fontweight="bold")
        fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label="Mean Bit Accuracy")

        # Overlay theoretical cutoff if present
        if fitted and att in fitted.get("attacks", {}):
            att_fits = fitted["attacks"][att]
            cutoff_bands = []
            for s_val in pivot.index:
                s_key = str(s_val)
                if s_key in att_fits and "f_c_pred" in att_fits[s_key]:
                    fc = att_fits[s_key]["f_c_pred"]
                    # Map fc in [0, 0.5] to band index [0, 7]
                    b_mapped = np.clip(fc / 0.5 * 8 - 0.5, 0, 7)
                    cutoff_bands.append(b_mapped)
                else:
                    cutoff_bands.append(np.nan)
            if not all(np.isnan(cutoff_bands)):
                ax.plot(cutoff_bands, range(len(pivot.index)), "r--o", linewidth=2.5, markersize=6, label="Wiener Cutoff $f_c$")
                ax.legend(loc="upper right", fontsize=9)

    plt.tight_layout()
    plt.savefig(out_file, dpi=200)
    plt.close()
    print(f"[Plots] Saved Fig 3 to {out_file}")


def plot_fig4_learned_weights(
    history_json: str = "checkpoints/main_stage2_surrogate/training_history.json",
    eval_csv: Optional[str] = "results/merge2_final_eval.csv",
    out_file: str = "figures/fig4_learned_allocation.png",
):
    """Fig 4: Learned dynamic band allocation weights g_b & Merge 2 robustness comparison."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Plot 4A: Evolution of band weights over epochs
    hist_path = Path(history_json)
    if hist_path.exists():
        with open(hist_path, "r") as f:
            hist = json.load(f)
        epochs = [entry["epoch"] for entry in hist]
        g_weights = np.array([entry["g"] for entry in hist])  # (E, 8)
        for b in range(8):
            axes[0].plot(epochs, g_weights[:, b], label=f"Band {b}", linewidth=2)
        axes[0].set_xlabel("Epoch")
        axes[0].set_ylabel("Normalized Energy Weight $g_b$")
        axes[0].set_title("Learned Band Allocation Evolution (Track C)")
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(loc="upper left", ncol=2, fontsize=8)
    else:
        axes[0].text(0.5, 0.5, "Training history not found", ha="center", va="center")
        axes[0].set_title("Learned Band Allocation Evolution")

    # Plot 4B: Robustness comparison on held-out SD VAE (Merge 2)
    if eval_csv and Path(eval_csv).exists():
        df_eval = pd.read_csv(eval_csv)
        sd_data = df_eval[df_eval["attack"].str.contains("sd_vae|stability", case=False, na=False)]
        if not sd_data.empty:
            for m_name, sub in sd_data.groupby("method"):
                sub_agg = sub.groupby("strength")["bit_acc"].mean().reset_index()
                axes[1].plot(sub_agg["strength"].astype(str), sub_agg["bit_acc"], "o-", label=m_name, linewidth=2)
            axes[1].set_xlabel("Attack Strength ($\sigma$)")
            axes[1].set_ylabel("Bit Accuracy")
            axes[1].set_ylim(0.45, 1.02)
            axes[1].axhline(0.5, color="gray", linestyle="--", alpha=0.5, label="Random Guess")
            axes[1].set_title("Held-out SD VAE Robustness (Merge 2)")
            axes[1].grid(True, alpha=0.3)
            axes[1].legend(fontsize=8)
        else:
            axes[1].text(0.5, 0.5, "No SD VAE data in eval CSV", ha="center", va="center")
    else:
        axes[1].text(0.5, 0.5, "merge2_final_eval.csv not generated yet", ha="center", va="center")
        axes[1].set_title("Held-out SD VAE Robustness (Merge 2)")

    plt.tight_layout()
    plt.savefig(out_file, dpi=180)
    plt.close()
    print(f"[Plots] Saved Fig 4 to {out_file}")


def generate_all_plots():
    import argparse
    parser = argparse.ArgumentParser(description="Track D: Generate All Paper Figures")
    parser.add_argument("--transfer_csv", type=str, default="results/track_a_transfer.csv")
    parser.add_argument("--sweep_csv", type=str, default="results/track_b_sweep.csv")
    parser.add_argument("--fitted_json", type=str, default="results/fitted_g.json")
    parser.add_argument("--eval_csv", type=str, default="results/merge2_final_eval.csv")
    parser.add_argument("--history_json", type=str, default="checkpoints/main_stage2_surrogate/training_history.json")
    args = parser.parse_args()

    if Path(args.transfer_csv).exists() and Path(args.fitted_json).exists():
        plot_fig1_transfer_functions(args.transfer_csv, args.fitted_json)
    if Path(args.fitted_json).exists():
        plot_fig2_cutoff_prediction(args.fitted_json)
    if Path(args.sweep_csv).exists():
        plot_fig3_classical_heatmaps(args.sweep_csv, args.fitted_json)
    plot_fig4_learned_weights(args.history_json, args.eval_csv)


if __name__ == "__main__":
    generate_all_plots()
