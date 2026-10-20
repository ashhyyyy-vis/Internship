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
    df = pd.read_csv(sweep_csv)
    df_clean = df[df["attack"] != "none"]

    attacks = df_clean["attack"].unique()
    fig, axes = plt.subplots(1, len(attacks), figsize=(6 * len(attacks), 5), squeeze=False)

    for ax, att in zip(axes[0], attacks):
        sub = df_clean[df_clean["attack"] == att]
        pivot = sub.groupby(["strength", "band"])["bit_acc"].mean().unstack()

        cax = ax.imshow(pivot.values, cmap="magma", vmin=0.5, vmax=1.0, aspect="auto")
        ax.set_xticks(range(8))
        ax.set_xticklabels([f"B{i}" for i in range(8)])
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_xlabel("Frequency Band")
        ax.set_ylabel("Attack Strength")
        ax.set_title(f"Classical Bit Accuracy: {att}")
        fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(out_file, dpi=180)
    plt.close()
    print(f"[Plots] Saved Fig 3 to {out_file}")
