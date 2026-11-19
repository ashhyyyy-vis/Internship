"""
results/v2/task2_plot_chunk0.py - Generate held-out empirical benchmark plot for SD-VAE (Chunk 0).
Includes Wilson 95% confidence intervals on TPR and per-band bit accuracy degradation curves.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def wilson_ci(k, n, z=1.96):
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return np.maximum(0.0, center - margin), np.minimum(1.0, center + margin)

master_csv = Path("results/v2/T2/master.csv")
df = pd.read_csv(master_csv)

strengths = sorted(df["strength"].unique())
bands = range(8)

# Style configuration
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

colors = plt.cm.viridis(np.linspace(0, 0.95, 8))

# Panel 1: Bit Accuracy vs Noise Strength
ax1 = axes[0]
for b in bands:
    mname = f"classical_ss_bands_all_b{b}"
    b_df = df[df["method"] == mname]
    acc_means = [b_df[b_df["strength"] == s]["bit_acc"].mean() for s in strengths]
    lw = 2.5 if b in (1, 2) else 1.2
    alpha = 1.0 if b in (0, 1, 2) else 0.65
    marker = "o" if b in (1, 2) else "s"
    ax1.plot(strengths, acc_means, marker=marker, color=colors[b], label=f"Band {b}", linewidth=lw, alpha=alpha)

ax1.axhline(0.5, color="gray", linestyle=":", linewidth=1.2, label="Chance (50%)")
ax1.axhline(0.75, color="red", linestyle="--", linewidth=1.2, label=r"Threshold $\tau=24/32$ (75%)")
ax1.set_xlabel(r"SD-VAE Pre-noise Standard Deviation $\sigma$", fontsize=11, fontweight="bold")
ax1.set_ylabel("Bit Accuracy", fontsize=11, fontweight="bold")
ax1.set_title("Bit Accuracy Degradation Under SD-VAE Regeneration (N=500)", fontsize=12, fontweight="bold")
ax1.set_ylim(0.45, 0.85)
ax1.legend(loc="lower left", fontsize=8.5, ncol=2, frameon=True)

# Panel 2: Detection Rate (TPR) with Wilson 95% Confidence Intervals
ax2 = axes[1]
for b in [0, 1, 2, 3, 4]:
    mname = f"classical_ss_bands_all_b{b}"
    b_df = df[df["method"] == mname]
    tprs = []
    yerr_lower = []
    yerr_upper = []
    for s in strengths:
        s_df = b_df[b_df["strength"] == s]
        k = int(s_df["detected"].sum())
        n = len(s_df)
        tpr = k / n
        ci_low, ci_high = wilson_ci(k, n)
        tprs.append(tpr)
        yerr_lower.append(tpr - ci_low)
        yerr_upper.append(ci_high - tpr)
    
    yerr = [yerr_lower, yerr_upper]
    lw = 2.2 if b in (1, 2) else 1.2
    ax2.errorbar(strengths, tprs, yerr=yerr, marker="o", color=colors[b], label=f"Band {b} (Wilson 95% CI)",
                 linewidth=lw, capsize=3.5, capthick=1.0)

# Also plot null_check
null_df = df[df["method"] == "null_check"]
null_tprs = [null_df[null_df["strength"] == s]["detected"].mean() for s in strengths]
ax2.plot(strengths, null_tprs, color="black", linestyle="--", linewidth=1.5, label="Null check (Empirical FPR = 0.0%)")

ax2.set_xlabel(r"SD-VAE Pre-noise Standard Deviation $\sigma$", fontsize=11, fontweight="bold")
ax2.set_ylabel(r"True Positive Rate (TPR @ $\tau=24$)", fontsize=11, fontweight="bold")
ax2.set_title("Empirical Detection Rate with 95% Wilson CIs (N=500)", fontsize=12, fontweight="bold")
ax2.set_ylim(-0.02, 0.65)
ax2.legend(loc="upper right", fontsize=8.5, frameon=True)

plt.tight_layout()
out_fig = Path("figures/v2/fig_heldout_sd_vae.png")
out_fig.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_fig, dpi=300)
print(f"✓ Saved empirical held-out figure to {out_fig}")
