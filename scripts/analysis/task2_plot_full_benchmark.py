"""
results/v2/task2_plot_full_benchmark.py - Complete Held-Out Benchmark Visualization (N=500, 77k rows).
Produces 4-panel publication figure covering SD-VAE (sigma 0..0.2) and CompressAI (q 1..8)
with Wilson 95% confidence intervals and empirical FPR.
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

sd_df = df[df["attack"] == "sd_vae"]
ca_df = df[df["attack"] == "compressai_bmshj2018"]

sd_strengths = sorted(sd_df["strength"].unique())
ca_strengths = sorted(ca_df["strength"].unique())

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)

colors = plt.cm.plasma(np.linspace(0.05, 0.95, 8))

# ── Row 1: SD-VAE ────────────────────────────────────────────────────────────
# Panel A: SD-VAE Bit Accuracy
ax_sd_acc = axes[0, 0]
for b in range(8):
    mname = f"classical_ss_bands_all_b{b}"
    b_df = sd_df[sd_df["method"] == mname]
    accs = [b_df[b_df["strength"] == s]["bit_acc"].mean() for s in sd_strengths]
    lw = 2.5 if b in (1, 2) else 1.2
    marker = "o" if b in (1, 2) else "s"
    ax_sd_acc.plot(sd_strengths, accs, marker=marker, color=colors[b], label=f"Band {b}", linewidth=lw)

ax_sd_acc.axhline(0.5, color="gray", linestyle=":", linewidth=1.2, label="Chance (50%)")
ax_sd_acc.axhline(0.75, color="red", linestyle="--", linewidth=1.2, label=r"Threshold $\tau=24/32$")
ax_sd_acc.set_title("(a) SD-VAE: Bit Accuracy vs Pre-noise $\sigma$ (N=500)", fontsize=11, fontweight="bold")
ax_sd_acc.set_xlabel(r"SD-VAE Pre-noise $\sigma$", fontsize=10, fontweight="bold")
ax_sd_acc.set_ylabel("Mean Bit Accuracy", fontsize=10, fontweight="bold")
ax_sd_acc.set_ylim(0.45, 0.85)
ax_sd_acc.legend(loc="lower left", fontsize=8, ncol=2)

# Panel B: SD-VAE TPR with Wilson CIs
ax_sd_tpr = axes[0, 1]
for b in [0, 1, 2, 3, 4]:
    mname = f"classical_ss_bands_all_b{b}"
    b_df = sd_df[sd_df["method"] == mname]
    tprs, err_low, err_high = [], [], []
    for s in sd_strengths:
        s_sub = b_df[b_df["strength"] == s]
        k = int(s_sub["detected"].sum())
        n = len(s_sub)
        tpr = k / n
        c_low, c_high = wilson_ci(k, n)
        tprs.append(tpr)
        err_low.append(max(0.0, tpr - c_low))
        err_high.append(max(0.0, c_high - tpr))
    lw = 2.2 if b in (1, 2) else 1.2
    ax_sd_tpr.errorbar(sd_strengths, tprs, yerr=[err_low, err_high], marker="o", color=colors[b],
                       label=f"Band {b}", linewidth=lw, capsize=3)

# Null check
null_sd = sd_df[sd_df["method"] == "null_check"]
null_tprs = [null_sd[null_sd["strength"] == s]["detected"].mean() for s in sd_strengths]
ax_sd_tpr.plot(sd_strengths, null_tprs, color="black", linestyle="--", linewidth=1.5, label="Null check (FPR=0.0%)")

ax_sd_tpr.set_title("(b) SD-VAE: Detection Rate (TPR @ $\tau=24$) with 95% Wilson CIs", fontsize=11, fontweight="bold")
ax_sd_tpr.set_xlabel(r"SD-VAE Pre-noise $\sigma$", fontsize=10, fontweight="bold")
ax_sd_tpr.set_ylabel("True Positive Rate (TPR)", fontsize=10, fontweight="bold")
ax_sd_tpr.set_ylim(-0.02, 0.65)
ax_sd_tpr.legend(loc="upper right", fontsize=8.5)

# ── Row 2: CompressAI ────────────────────────────────────────────────────────
# Panel C: CompressAI Bit Accuracy
ax_ca_acc = axes[1, 0]
for b in range(8):
    mname = f"classical_ss_bands_all_b{b}"
    b_df = ca_df[ca_df["method"] == mname]
    accs = [b_df[b_df["strength"] == q]["bit_acc"].mean() for q in ca_strengths]
    lw = 2.5 if b in (1, 2, 3) else 1.2
    marker = "o" if b in (1, 2, 3) else "s"
    ax_ca_acc.plot(ca_strengths, accs, marker=marker, color=colors[b], label=f"Band {b}", linewidth=lw)

ax_ca_acc.axhline(0.5, color="gray", linestyle=":", linewidth=1.2, label="Chance (50%)")
ax_ca_acc.axhline(0.75, color="red", linestyle="--", linewidth=1.2, label=r"Threshold $\tau=24/32$")
ax_ca_acc.set_title("(c) CompressAI: Bit Accuracy vs Quality Factor $q$ (N=500)", fontsize=11, fontweight="bold")
ax_ca_acc.set_xlabel("Compression Quality Factor $q$", fontsize=10, fontweight="bold")
ax_ca_acc.set_ylabel("Mean Bit Accuracy", fontsize=10, fontweight="bold")
ax_ca_acc.set_ylim(0.45, 1.02)
ax_ca_acc.set_xticks(ca_strengths)
ax_ca_acc.legend(loc="lower right", fontsize=8, ncol=2)

# Panel D: CompressAI TPR with Wilson CIs
ax_ca_tpr = axes[1, 1]
for b in range(8):
    mname = f"classical_ss_bands_all_b{b}"
    b_df = ca_df[ca_df["method"] == mname]
    tprs, err_low, err_high = [], [], []
    for q in ca_strengths:
        q_sub = b_df[b_df["strength"] == q]
        k = int(q_sub["detected"].sum())
        n = len(q_sub)
        tpr = k / n
        c_low, c_high = wilson_ci(k, n)
        tprs.append(tpr)
        err_low.append(max(0.0, tpr - c_low))
        err_high.append(max(0.0, c_high - tpr))
    lw = 2.2 if b in (1, 2, 3) else 1.2
    ax_ca_tpr.errorbar(ca_strengths, tprs, yerr=[err_low, err_high], marker="o", color=colors[b],
                       label=f"Band {b}", linewidth=lw, capsize=3)

# Null check
null_ca = ca_df[ca_df["method"] == "null_check"]
null_tprs_ca = [null_ca[null_ca["strength"] == q]["detected"].mean() for q in ca_strengths]
ax_ca_tpr.plot(ca_strengths, null_tprs_ca, color="black", linestyle="--", linewidth=1.5, label="Null check (FPR=0.0%)")

ax_ca_tpr.set_title("(d) CompressAI: Detection Rate (TPR @ $\tau=24$) with 95% Wilson CIs", fontsize=11, fontweight="bold")
ax_ca_tpr.set_xlabel("Compression Quality Factor $q$", fontsize=10, fontweight="bold")
ax_ca_tpr.set_ylabel("True Positive Rate (TPR)", fontsize=10, fontweight="bold")
ax_ca_tpr.set_ylim(-0.02, 1.05)
ax_ca_tpr.set_xticks(ca_strengths)
ax_ca_tpr.legend(loc="center left", fontsize=8)

plt.tight_layout()
out_fig = Path("figures/v2/fig_heldout_benchmark_full.png")
plt.savefig(out_fig, dpi=300)
print(f"✓ Saved full benchmark figure to {out_fig}")
