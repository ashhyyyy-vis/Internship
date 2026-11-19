"""
task10_explanatory_figures.py
Publication-quality explanatory figures for the spectral watermarking project.
All figures saved to figures/v2/ at 300 DPI.
"""

import sys
import os
import warnings
warnings.filterwarnings("ignore")

# Ensure project root is on path
sys.path.insert(0, '/home/viseash/Ashley/Work/Internship')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import Normalize
import matplotlib.cm as cm
from PIL import Image
import pandas as pd
import torch

# ── global style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

OUT_DIR = '/home/viseash/Ashley/Work/Internship/figures/v2'
os.makedirs(OUT_DIR, exist_ok=True)

# ── Wiener model parameters ────────────────────────────────────────────────────
ALPHA = 2.660
LOG_A = -8.737
A = np.exp(LOG_A)

# ── Band configuration ─────────────────────────────────────────────────────────
N_BANDS = 8
R_MAX   = 0.5
BAND_EDGES = np.linspace(0.0, R_MAX, N_BANDS + 1)   # [0.000, 0.0625, …, 0.5]

BAND_LABELS = [
    f"B{b}: {BAND_EDGES[b]:.3f}–{BAND_EDGES[b+1]:.3f}"
    for b in range(N_BANDS)
]

# ── Tab10 colors (8 bands) ─────────────────────────────────────────────────────
TAB10 = plt.cm.tab10(np.linspace(0, 0.9, N_BANDS))

# =============================================================================
# Figure 1 – 8 Annular Frequency Bands
# =============================================================================
def fig1_band_map():
    print("  [Fig 1] Drawing band map …")
    SIZE = 400
    cx, cy = SIZE // 2, SIZE // 2

    # Build radial frequency grid
    ys, xs = np.mgrid[0:SIZE, 0:SIZE]
    fx = (xs - cx) / SIZE          # cycles per pixel  (centered)
    fy = (ys - cy) / SIZE
    r  = np.sqrt(fx**2 + fy**2)

    # Assign each pixel to a band (or background if r > 0.5)
    band_img = np.full((SIZE, SIZE, 4), [0.95, 0.95, 0.95, 1.0])  # light-grey bg
    for b in range(N_BANDS):
        lo, hi = BAND_EDGES[b], BAND_EDGES[b + 1]
        mask = (r >= lo) & (r < hi)
        color = TAB10[b]
        band_img[mask] = color

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(band_img, extent=[-0.5, 0.5, -0.5, 0.5], origin='lower')

    # Nyquist circle
    theta = np.linspace(0, 2 * np.pi, 300)
    ax.plot(0.5 * np.cos(theta), 0.5 * np.sin(theta),
            'k--', lw=1.0, label='Nyquist (f=0.5)')

    # Radial band-edge circles and labels
    for b in range(N_BANDS):
        lo, hi   = BAND_EDGES[b], BAND_EDGES[b + 1]
        mid_r    = (lo + hi) / 2
        # Place label at 45° direction
        angle = np.pi / 4
        lx, ly = mid_r * np.cos(angle) * 1.0, mid_r * np.sin(angle) * 1.0
        ax.text(lx, ly, f"B{b}", ha='center', va='center',
                fontsize=7, fontweight='bold', color='white',
                bbox=dict(boxstyle='round,pad=0.1', fc=TAB10[b], ec='none', alpha=0.9))

    # Legend
    patches = [mpatches.Patch(color=TAB10[b], label=BAND_LABELS[b]) for b in range(N_BANDS)]
    ax.legend(handles=patches, loc='lower left', fontsize=7, ncol=2,
              framealpha=0.85, edgecolor='grey')

    ax.set_xlabel("Spatial frequency  $f_x$  (cyc/px)")
    ax.set_ylabel("Spatial frequency  $f_y$  (cyc/px)")
    ax.set_title("8 Disjoint Annular Frequency Bands")
    fig.suptitle("Low bands carry more signal energy; high bands are dominated by noise",
                 fontsize=9, style='italic', y=0.02)

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    path = os.path.join(OUT_DIR, 'fig10_1_band_map.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"    saved → {path}")
    return path


# =============================================================================
# Figure 2 – Wiener Filter Intuition
# =============================================================================
def fig2_wiener_intuition():
    print("  [Fig 2] Wiener filter intuition …")
    N_EFF = 0.001
    f = np.logspace(np.log10(0.01), np.log10(0.5), 500)

    Pf  = A * f**(-ALPHA)
    Gf  = Pf / (Pf + N_EFF)

    # Cutoff frequency where G=0.5  =>  P(f_c) = N_eff
    # A * f_c^(-alpha) = N_eff  =>  f_c = (N_eff/A)^(-1/alpha)
    f_c = (N_EFF / A) ** (-1.0 / ALPHA)
    print(f"    f_c = {f_c:.4f} cyc/px")

    fig, ax1 = plt.subplots(figsize=(8, 5))

    # Primary axis: P(f) and N_eff
    l1, = ax1.loglog(f, Pf,  color='steelblue', lw=2, label=r'$P(f) = A\,f^{-\alpha}$')
    l2  = ax1.axhline(N_EFF, color='tomato', lw=1.8, ls='--',
                      label=r'$N_\mathrm{eff}=0.001$')
    ax1.set_xlabel("Spatial frequency  $f$  (cyc/px)")
    ax1.set_ylabel("Power spectral density  (arb.)", color='steelblue')
    ax1.tick_params(axis='y', labelcolor='steelblue')

    # Secondary axis: G(f)
    ax2 = ax1.twinx()
    l3, = ax2.semilogx(f, Gf, color='darkorange', lw=2.5,
                       label=r'$G(f) = P(f)/(P(f)+N_\mathrm{eff})$')
    ax2.set_ylabel("Wiener gain  $G(f)$  (dimensionless)", color='darkorange')
    ax2.tick_params(axis='y', labelcolor='darkorange')
    ax2.set_ylim(0, 1.05)
    ax2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))

    # Cutoff vertical line
    ax1.axvline(f_c, color='purple', lw=1.5, ls=':', alpha=0.8)
    ax2.axvline(f_c, color='purple', lw=1.5, ls=':', alpha=0.8)
    ax2.text(f_c * 1.05, 0.52, r'$f_c$ (cutoff)', color='purple',
             fontsize=9, va='bottom')

    # Shade band 2 (0.125–0.1875)
    ax1.axvspan(0.125, 0.1875, alpha=0.18, color='limegreen', label='Band 2 (0.125–0.1875)')

    # Combined legend
    lines = [l1, l2, l3,
             mpatches.Patch(fc='limegreen', alpha=0.4, label='Band 2')]
    ax1.legend(handles=lines, loc='upper right', fontsize=9)

    ax1.set_title("Wiener Filter Intuition: Why Low Bands Survive")
    fig.suptitle(
        "Low frequencies (small $f$) have high $P(f)$ → $G≈1$; "
        "high frequencies are killed by noise → $G≈0$",
        fontsize=9, style='italic', y=0.02
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    path = os.path.join(OUT_DIR, 'fig10_2_wiener_intuition.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"    saved → {path}")
    return path


# =============================================================================
# Figure 3 – Radial Power Spectrum Before/After VAE
# =============================================================================
def fig3_spectrum_before_after():
    print("  [Fig 3] Power spectrum before/after VAE …")
    N_EFF = 0.001

    # Load first image alphabetically
    test_dir = '/home/viseash/Ashley/Work/Internship/data/processed/test'
    fname = sorted(os.listdir(test_dir))[0]
    img = Image.open(os.path.join(test_dir, fname)).convert('RGB')
    arr = np.array(img, dtype=np.float32) / 255.0

    # Luminance
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    H, W = lum.shape

    # 2D FFT power spectrum (centered)
    F = np.fft.fftshift(np.fft.fft2(lum - lum.mean()))
    P2d = (np.abs(F) ** 2) / (H * W)

    # Radial frequency grid
    ys, xs = np.mgrid[0:H, 0:W]
    r2d = np.sqrt(((xs - W//2)/W)**2 + ((ys - H//2)/H)**2)

    # Bin into 50 radial bins
    n_bins = 50
    r_bins = np.linspace(0.0, 0.5, n_bins + 1)
    r_centers = 0.5 * (r_bins[:-1] + r_bins[1:])

    P_before, P_after = [], []
    for i in range(n_bins):
        mask = (r2d >= r_bins[i]) & (r2d < r_bins[i + 1])
        if mask.sum() == 0:
            P_before.append(np.nan)
            P_after.append(np.nan)
        else:
            p_avg = P2d[mask].mean()
            # Wiener gain at this radial bin center
            fc = r_centers[i] if r_centers[i] > 1e-6 else 1e-6
            Pf = A * fc**(-ALPHA)
            Gf = Pf / (Pf + N_EFF)
            P_before.append(p_avg)
            P_after.append(p_avg * Gf**2)

    P_before = np.array(P_before)
    P_after  = np.array(P_after)

    # Cutoff
    f_c = (N_EFF / A) ** (-1.0 / ALPHA)

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.loglog(r_centers, P_before, lw=2.0, color='steelblue',
              label='Before VAE')
    ax.loglog(r_centers, P_after,  lw=2.0, color='tomato', ls='--',
              label='After VAE (×$G^2$)')

    # Shade 8 bands alternately
    band_colors = ['#d0e8ff', '#ffe4c4'] * 4
    for b in range(N_BANDS):
        lo, hi = BAND_EDGES[b], BAND_EDGES[b+1]
        ax.axvspan(lo, hi, alpha=0.3, color=band_colors[b], zorder=0,
                   label=f'B{b}' if b == 0 else '_')
        # Label band number at top
        mid = (lo + hi) / 2
        ax.text(mid, ax.get_ylim()[1] if hasattr(ax, '_ylim') else 1.0,
                f'B{b}', ha='center', fontsize=7, color='grey')

    # Vertical cutoff line
    ax.axvline(f_c, color='purple', lw=1.5, ls=':', alpha=0.9,
               label=f'$f_c$={f_c:.3f}')

    ax.set_xlabel("Radial frequency  $f$  (cyc/px)")
    ax.set_ylabel("Mean power  (arb.)")
    ax.set_title("Radial Power Spectrum: Before and After VAE Regeneration")
    ax.legend(fontsize=9)
    ax.set_xlim(0.009, 0.52)

    # Re-annotate band labels after proper ylim
    ylo, yhi = ax.get_ylim()
    for b in range(N_BANDS):
        mid = (BAND_EDGES[b] + BAND_EDGES[b+1]) / 2
        ax.text(mid, yhi * 1.5, f'B{b}', ha='center', fontsize=7,
                color='dimgrey', clip_on=False)

    fig.suptitle(
        f"VAE acts as a low-pass filter — only bands below $f_c≈{f_c:.3f}$ survive",
        fontsize=9, style='italic', y=0.02
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    path = os.path.join(OUT_DIR, 'fig10_3_spectrum_before_after.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"    saved → {path}")
    return path


# =============================================================================
# Figure 4 – Watermark Residuals per Band
# =============================================================================
def fig4_watermark_residuals():
    print("  [Fig 4] Watermark residuals …")
    from track_b.watermark import ClassicalSpreadSpectrumWatermarker

    test_dir = '/home/viseash/Ashley/Work/Internship/data/processed/test'
    fname = sorted(os.listdir(test_dir))[0]
    img = Image.open(os.path.join(test_dir, fname)).convert('RGB').resize((256, 256))
    arr = np.array(img, dtype=np.float32) / 255.0   # H×W×3

    x = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)  # (1,3,H,W)
    msg = torch.randint(0, 2, (1, 32))

    wm = ClassicalSpreadSpectrumWatermarker(n_bits=32, secret_key=42)
    bands_to_show = [0, 2, 4, 7]
    PSNR_DB = 40.0

    fig, axes = plt.subplots(1, 4, figsize=(14, 4))

    for ax, b in zip(axes, bands_to_show):
        with torch.no_grad():
            x_w = wm.embed(x, msg, band_idx=b, psnr_db=PSNR_DB)

        # Residual, amplified 10×, shifted to 0.5 baseline
        residual = (x_w - x).squeeze(0).permute(1, 2, 0).numpy()   # H×W×3
        residual_amp = residual * 10.0 + 0.5
        residual_amp = np.clip(residual_amp, 0.0, 1.0)

        im = ax.imshow(residual_amp)
        ax.set_title(f"Band {b}\n({BAND_LABELS[b].split(':')[1].strip()})", fontsize=9)
        ax.axis('off')

        # Colorbar using luminance channel for reference
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        # Map residual amplitude
        res_lum = residual.mean(-1)
        norm = Normalize(vmin=res_lum.min(), vmax=res_lum.max())
        sm = cm.ScalarMappable(norm=norm, cmap='RdBu_r')
        fig.colorbar(sm, cax=cax, label='Δ (raw)' if b == bands_to_show[-1] else '')

    fig.suptitle(
        "Watermark Residuals per Frequency Band (Amplified 10×)\n"
        "Low bands spread energy broadly; high bands show fine structure",
        fontsize=11
    )
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'fig10_4_watermark_residuals.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"    saved → {path}")
    return path


# =============================================================================
# Figure 5 – Pipeline Diagram
# =============================================================================
def fig5_pipeline_diagram():
    print("  [Fig 5] Pipeline diagram …")
    fig, ax = plt.subplots(figsize=(16, 7))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # ── Helper functions ──────────────────────────────────────────────────────
    def add_box(ax, x, y, w, h, title, lines, color, fontsize=8.5):
        """Draw a FancyBboxPatch with a title and bullet lines."""
        box = FancyBboxPatch((x, y), w, h,
                             boxstyle="round,pad=0.15",
                             facecolor=color, edgecolor='#444444',
                             linewidth=1.5, zorder=2)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.28, title,
                ha='center', va='top', fontsize=fontsize + 0.5,
                fontweight='bold', zorder=3, wrap=True)
        for i, line in enumerate(lines):
            ax.text(x + 0.18, y + h - 0.62 - i * 0.42, f"• {line}",
                    ha='left', va='top', fontsize=fontsize - 0.5,
                    zorder=3, color='#222222')

    def add_arrow(ax, x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#444444',
                                   lw=2.0, connectionstyle='arc3,rad=0.0'),
                    zorder=4)

    # ── Stage boxes ──────────────────────────────────────────────────────────
    BOX_Y   = 1.0
    BOX_H   = 5.0
    BOX_W   = 4.2
    GAP     = 0.5

    # Stage 1 – Transfer Function Measurement
    add_box(ax, 0.3, BOX_Y, BOX_W, BOX_H,
            "① Transfer Function\n   Measurement",
            [
                "300 fit images",
                "Band probes (8 sinusoidal)",
                "Attack: VAE / CompressAI",
                "Measure H(f) per band",
                "Wiener model fit:",
                " G(f) = P(f)/(P(f)+N_eff)",
                "Output: α, A, N_eff, f_c",
            ],
            color='#dbeafe')

    # Stage 2 – Classical Spread-Spectrum Sweep
    add_box(ax, 0.3 + BOX_W + GAP, BOX_Y, BOX_W, BOX_H,
            "② Classical Spread-Spectrum\n   Sweep",
            [
                "300 fit images",
                "8 bands × 4 PSNRs",
                "14 attacks × blind decode",
                "32-bit correlation detector",
                "→ Bit accuracy per cell",
                "→ Heatmap: band × attack",
                "Sweet spot: Band 2 survives",
            ],
            color='#dcfce7')

    # Stage 3 – Learned Band Allocation
    add_box(ax, 0.3 + 2*(BOX_W + GAP), BOX_Y, BOX_W, BOX_H,
            "③ Learned Band-Allocation\n   (Null Result)",
            [
                "CNN encoder (HiDDeN-style)",
                "Soft band-allocation g_b",
                "Fourier surrogate G(f)",
                "Attack differentiable proxy",
                "CNN decoder",
                "→ Loss: BER + distortion",
                "⚠ 50% bit acc. under attack",
            ],
            color='#fef9c3')

    # Arrows between stages
    mid_y = BOX_Y + BOX_H / 2
    add_arrow(ax, 0.3 + BOX_W, mid_y, 0.3 + BOX_W + GAP, mid_y)
    add_arrow(ax, 0.3 + 2*BOX_W + GAP, mid_y, 0.3 + 2*BOX_W + 2*GAP, mid_y)

    # Outputs below boxes
    out_y = BOX_Y - 0.55
    for i, (label, color) in enumerate([
        ("f_c ≈ 0.14 cyc/px\nα = 2.660, N_eff = 0.001", '#bfdbfe'),
        ("Band 2 bit acc ≈ 81%\n(CompressAI q=3)", '#bbf7d0'),
        ("Null result — training\ncollapsed at 50%", '#fde68a'),
    ]):
        bx = 0.3 + i * (BOX_W + GAP) + BOX_W/2
        ax.text(bx, out_y, label, ha='center', va='top',
                fontsize=8, color='#444444',
                bbox=dict(boxstyle='round,pad=0.3', fc=color, ec='#888888', lw=0.8))
        # Arrow down
        ax.annotate("", xy=(bx, out_y + 0.02), xytext=(bx, BOX_Y),
                    arrowprops=dict(arrowstyle='->', color='#777777', lw=1.2),
                    zorder=4)

    ax.set_title("Project Architecture: Three Complementary Approaches",
                 fontsize=14, fontweight='bold', pad=12)
    fig.suptitle(
        "Classical sweep (Track B) succeeded; learned approach (Track C) failed — Wiener theory explains why",
        fontsize=9, style='italic', y=0.02
    )

    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    path = os.path.join(OUT_DIR, 'fig10_5_pipeline_diagram.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"    saved → {path}")
    return path


# =============================================================================
# Figure 6 – Band Survival Story
# =============================================================================
def fig6_band_survival_story():
    print("  [Fig 6] Band survival story …")
    df = pd.read_csv('/home/viseash/Ashley/Work/Internship/results/track_b_sweep.csv',
                     low_memory=False)

    bands = list(range(N_BANDS))

    # ── No attack (psnr_target=41) ─────────────────────────────────────────
    no_atk = (
        df[(df['attack'] == 'none') & (df['psnr_target'] == 41.0)]
        .groupby('band')['bit_acc'].mean()
        .reindex(bands, fill_value=np.nan)
        .values
    )

    # ── CompressAI q=3 (strength='3', psnr_target=41) ─────────────────────
    ca3 = (
        df[(df['attack'] == 'compressai_bmshj2018') &
           (df['strength'].astype(str) == '3') &
           (df['psnr_target'] == 41.0)]
        .groupby('band')['bit_acc'].mean()
        .reindex(bands, fill_value=np.nan)
        .values
    )

    # ── SD-VAE σ=0.05 (psnr_target=41) ─────────────────────────────────────
    sdv = (
        df[(df['attack'] == 'sd_vae') &
           (df['strength'].astype(str) == '0.05') &
           (df['psnr_target'] == 41.0)]
        .groupby('band')['bit_acc'].mean()
        .reindex(bands, fill_value=np.nan)
        .values
    )

    # Print for verification
    print(f"    No attack:    {np.round(no_atk*100, 1)}")
    print(f"    CompressAI3:  {np.round(ca3*100, 1)}")
    print(f"    SD-VAE 0.05:  {np.round(sdv*100, 1)}")

    x  = np.arange(N_BANDS)
    w  = 0.26

    fig, ax = plt.subplots(figsize=(11, 5.5))

    bars_no  = ax.bar(x - w, no_atk * 100, w, label='No attack',
                      color='steelblue', edgecolor='white', linewidth=0.5, zorder=3)
    bars_ca  = ax.bar(x,      ca3    * 100, w, label='CompressAI q=3',
                      color='tomato',    edgecolor='white', linewidth=0.5, zorder=3)
    bars_sd  = ax.bar(x + w,  sdv    * 100, w, label='SD-VAE σ=0.05',
                      color='darkorange', edgecolor='white', linewidth=0.5, zorder=3)

    # Reference lines
    ax.axhline(50.0, color='crimson', lw=1.5, ls='--', zorder=2, label='Chance (50%)')
    ax.axhline(68.0, color='purple',  lw=1.2, ls=':',  zorder=2,
               label='τ=24 threshold (~68%)')

    # Shade band 2 as the sweet spot
    ax.axvspan(2 - 0.5, 2 + 0.5, alpha=0.12, color='limegreen', zorder=1,
               label='Band 2 sweet spot')
    ax.text(2, 103, '★ Sweet spot', ha='center', fontsize=9, color='darkgreen',
            fontweight='bold')

    # Value labels on bars (compact)
    for bars in [bars_no, bars_ca, bars_sd]:
        for bar in bars:
            h = bar.get_height()
            if not np.isnan(h):
                ax.text(bar.get_x() + bar.get_width()/2, h + 0.5,
                        f'{h:.0f}', ha='center', va='bottom', fontsize=6.5)

    ax.set_xticks(x)
    ax.set_xticklabels([f'B{b}\n{BAND_EDGES[b]:.3f}–{BAND_EDGES[b+1]:.3f}' for b in bands],
                       fontsize=8)
    ax.set_xlabel("Frequency Band")
    ax.set_ylabel("Mean Bit Accuracy (%)")
    ax.set_ylim(0, 115)
    ax.set_title("Band Survival Under Attack: Why Band 2 is the Sweet Spot")
    ax.legend(fontsize=9, loc='lower right')

    fig.suptitle(
        "Band 2 (0.125–0.188 cyc/px) is below f_c for most attacks yet above the DC noise floor",
        fontsize=9, style='italic', y=0.02
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    path = os.path.join(OUT_DIR, 'fig10_6_band_survival_story.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"    saved → {path}")
    return path


# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("Task 10 – Creating publication-quality explanatory figures")
    print("=" * 60)

    results = {}

    for label, func in [
        ("fig10_1_band_map",             fig1_band_map),
        ("fig10_2_wiener_intuition",     fig2_wiener_intuition),
        ("fig10_3_spectrum_before_after", fig3_spectrum_before_after),
        ("fig10_4_watermark_residuals",  fig4_watermark_residuals),
        ("fig10_5_pipeline_diagram",     fig5_pipeline_diagram),
        ("fig10_6_band_survival_story",  fig6_band_survival_story),
    ]:
        try:
            path = func()
            results[label] = ('OK', path)
        except Exception as e:
            import traceback
            results[label] = ('FAIL', str(e))
            traceback.print_exc()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for label, (status, info) in results.items():
        mark = "✓" if status == "OK" else "✗"
        print(f"  {mark} {label}: {status}")
        if status == "FAIL":
            print(f"      Error: {info}")

    # Verify file sizes
    print()
    print("File sizes:")
    for fname in sorted(os.listdir(OUT_DIR)):
        if fname.endswith('.png'):
            fp = os.path.join(OUT_DIR, fname)
            sz = os.path.getsize(fp)
            print(f"  {fname}: {sz/1024:.1f} KB")
