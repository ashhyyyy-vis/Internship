# Spectral Band Allocation for Invisible Watermarks Under VAE Regeneration

**Bachelor of Technology (B.Tech) Capstone Project**  
**Department of Computer Science and Engineering**  
**Indian Institute of Information Technology, Pune (IIIT Pune)**  
**Author:** Viseash Ashley (MIS: 112115123)  
**Date:** November 2026  

---

## 📌 Overview

This project investigates the frequency-domain mechanics of generative autoencoder regeneration on invisible digital image watermarks. Modern generative autoencoders—specifically continuous-latent diffusion autoencoders (e.g., Stable Diffusion VAE) and factorized neural codecs (e.g., CompressAI BMSHJ2018)—severely attenuate high spatial frequencies, causing conventional invisible watermarks to collapse.

By decomposing the spatial spectrum into 8 concentric radial frequency bands, this repository provides:
1. **Analytical Transfer Characterization:** Empirical measurement of frequency-dependent attenuation $|H(f)|^2$ and analytical Wiener surrogate filter fitting.
2. **Classical Spread-Spectrum Sweep (Track B):** Full-factorial evaluation of 8 radial bands across 500 unseen images ($N=500$, 77,000 evaluations) under calibrated imperceptibility (target $\text{PSNR} = 40.0\text{ dB}$, empirical mean $40.06\text{ dB}$).
3. **Learned Watermarking Network (Track C):** Implementation and training diagnosis of end-to-end learned watermark autoencoders with a differentiable Fourier surrogate layer.
4. **The "Two Forces" Trade-Off:** Mathematical and empirical resolution of the Band 0 / SSIM paradox, balancing host cover interference against generative attenuation.

---

## 🗂️ Repository Directory Structure

```text
├── README.md                                  # Repository documentation & directory overview
├── CHANGELOG.md                               # Project revision and development milestone history
├── requirements.txt                           # Core Python package dependencies
├── data_prep.py                               # COCO val2017 dataset split downloader & preprocessor
├── gate_g0.py                                 # Phase 0 sanity verification & environment check
│
├── BTP_Final_Report_Spectral_Watermarking.docx # Final compiled thesis document (IIIT Pune format)
│
├── core/                                      # Shared algorithmic modules
│   ├── attacks.py                             # Distortion attacks (CompressAI, SD-VAE, Gaussian noise)
│   ├── bands.py                               # 8-band concentric annular Fourier frequency mask generator
│   ├── dataset_utils.py                       # Manifest-based dataset loader & image transforms
│   ├── probes.py                              # Synthetic impulse & sinusoidal spectral probe generators
│   ├── radial.py                              # 2D Fourier power spectrum & radial profile integration
│   └── sd_vae.py                              # Stable Diffusion VAE wrapper (Diffusers pipeline)
│
├── track_a/                                   # Track A: Transfer Function & Surrogate Filter Fitting
│   ├── measure.py                             # Empirical MTF measurement using white-noise and delta probes
│   └── fit.py                                 # Wiener surrogate filter fitting G(f) = 1 / (1 + (f/f_c)^alpha)
│
├── track_b/                                   # Track B: Classical Spread-Spectrum Watermarking
│   ├── watermark.py                           # 32-bit annular bandpass spread-spectrum embedder & decoder
│   └── sweep.py                               # Full-factorial band sweep across distortion parameters
│
├── track_c/                                   # Track C: Learned Watermarking with Differentiable Surrogate
│   ├── model.py                               # Residual encoder & decoder CNN with frequency allocation layer
│   ├── noise_layers.py                        # Differentiable Fourier filter surrogate & noise layers
│   └── train.py                               # Multi-objective training pipeline (BCE loss + L1 perceptual loss)
│
├── track_d/                                   # Track D: Evaluation Harness & Perceptual Verification
│   ├── harness.py                             # Standardized evaluation harness across test sets
│   ├── metrics.py                             # Bit accuracy, TPR (@ tau=24/32), PSNR, and SSIM
│   └── plots.py                               # Visualization and evaluation heatmap routines
│
├── scripts/                                   # Automation, ingestion, and report generation scripts
│   ├── build_btp_report_v3.py                 # Primary automated DOCX thesis report builder
│   ├── sync_md_report_v3.py                   # Synchronization tool for report markdown
│   ├── build_docx_report.py                   # Legacy DOCX builder
│   ├── build_markdown_report_final.py         # Markdown report generator
│   ├── build_t2_notebook.py                   # Generator script for Colab T2 evaluation notebook
│   ├── ingest.py                              # Chunk-based ingestion utility for Colab evaluation archives
│   ├── _gen_notebooks.py                      # Notebook generator for worker pipelines A-D
│   └── analysis/                              # Data analysis & figure generation scripts
│       ├── task2_plot_chunk0.py               # Empirical benchmark plotting (Chunk 0 / SD-VAE)
│       ├── task2_plot_full_benchmark.py       # Full 4-panel held-out benchmark visualizer
│       ├── task3_wiener_fit.py                # Full Wiener fit quality evaluation & R^2 fitting
│       ├── task4_best_band.py                 # Optimal band vs. f_c cutoff tracker
│       ├── task5_perceptual.py                # Per-band PSNR/SSIM perceptual analysis
│       ├── task7_host_interference.py         # Zero-mean luminance host cover variance calculation
│       └── task10_explanatory_figures.py      # High-resolution publication diagrams (300 DPI)
│
├── report/                                    # Thesis documentation & executive summaries
│   ├── BTP_Final_Report_Spectral_Watermarking.md    # Complete peer-reviewed thesis report (Markdown)
│   ├── BTP_Final_Report_Spectral_Watermarking.docx  # Final compiled thesis document (DOCX)
│   └── final_results_summary.md                     # Condensed executive summary of empirical results
│
├── results/                                   # Experimental evaluation outputs & tabular data
│   ├── fitted_g.json                          # Fitted Wiener surrogate parameters (alpha, f_c, A)
│   ├── track_a_transfer.csv                   # Raw radial transfer measurements
│   ├── track_b_sweep.csv                      # Track B pilot parameter sweep data
│   ├── merge2_final_eval.csv                  # Pilot evaluation logs (Track B vs. Track C)
│   └── v2/                                    # Final benchmark outputs (N=500 test images)
│       ├── perceptual_metrics.csv             # Per-band empirical PSNR and SSIM values
│       ├── wiener_fit_full.csv                # Per-condition R^2 and N_eff Wiener fit metrics
│       ├── chunk0_empirical_findings.md       # Chunk 0 intermediate analysis notes
│       ├── full_heldout_benchmark_report.md   # Final 77,000-sample benchmark report
│       ├── task3_summary.md                   # Wiener transfer equivalence summary
│       ├── task4_conclusion.txt               # Cutoff tracking findings
│       ├── task7_explanation.md               # Baseband host interference diagnostic notes
│       └── T2/                                # Ingested raw evaluation chunks
│           └── master.csv                     # Master evaluation dataset (77,000 rows)
│
├── figures/                                   # Publication figures (PNG, 300 DPI)
│   ├── gate_g0_verification.png               # Environment verification plots
│   ├── fig1_transfer_functions.png            # Transfer function curves |H(f)|^2
│   ├── fig2_cutoff_and_scaling.png            # Cutoff f_c scaling vs. attack strength
│   ├── fig3_classical_heatmaps.png            # Band survival heatmaps
│   ├── fig4_held_out_benchmark.png            # Pilot held-out evaluation plot
│   └── v2/                                    # Final publication figures
│       ├── fig_heldout_benchmark_full.png     # Complete 4-panel held-out benchmark (Figure 4.4)
│       ├── fig_null_distribution.png          # Blind unwatermarked null vs. Binomial(32, 0.5) (Figure 4.5)
│       ├── fig_perceptual_per_band.png        # Structural similarity across bands (Figure 4.6)
│       ├── fig_two_forces.png                 # The Two Forces trade-off diagram (Figure 4.8)
│       ├── fig_best_band_vs_fc.png            # Empirical optimal band vs. predicted cutoff
│       ├── fig_wiener_fit_quality.png         # Wiener fit quality R^2 curves
│       ├── fig_wiener_debug_fits.png          # Detailed per-condition Wiener fit curves
│       ├── fig10_1_band_map.png               # Annular frequency band partition diagram
│       ├── fig10_2_wiener_intuition.png       # Wiener transfer intuition diagram
│       ├── fig10_3_spectrum_before_after.png  # Image power spectrum before and after regeneration
│       ├── fig10_4_watermark_residuals.png    # Spatial residuals (amplified 10x) across bands
│       ├── fig10_5_pipeline_diagram.png       # Complete methodology pipeline diagram
│       └── fig10_6_band_survival_story.png    # Band survival mechanics summary diagram
│
├── notebooks/                                 # Google Colab orchestration notebooks
│   ├── colab_T0_env_check_v1.ipynb            # Environment check and GPU availability notebook
│   ├── colab_T1_learned_diag_v1.ipynb         # Diagnostic notebook for learned watermarking
│   └── colab_T2_heldout500_v1.ipynb           # Held-out 500-image distributed evaluation notebook
│
├── colab/                                     # Worker notebooks for modular parallel evaluation
│   ├── README.md                              # Instructions for Colab execution
│   ├── worker_a.ipynb                         # Worker Track A: Transfer measurement
│   ├── worker_b.ipynb                         # Worker Track B: Parameter sweep
│   ├── worker_c.ipynb                         # Worker Track C: Learned model training
│   └── worker_d.ipynb                         # Worker Track D: Benchmark evaluation
│
├── data/                                      # Dataset manifests and processed splits
│   ├── manifests/                             # Train, fit, and test JSON manifests
│   │   ├── train_manifest.json                # 2,000 images for model training
│   │   ├── fit_manifest.json                  # 200 images for surrogate fitting
│   │   └── test_manifest.json                 # 500 unseen images for held-out evaluation
│   └── processed/                             # Preprocessed 256x256 image splits
│       ├── train/                             # 2,000 training images
│       ├── fit/                               # 200 fitting images
│       └── test/                              # 500 test images
│
├── docs/                                      # Project documentation, specifications & design history
│   ├── Project Guide Spectral Band Allocation for Invisible Watermarks.pdf # Original BTP guide
│   ├── BTP Report Sample_Updated.docx         # Reference institutional thesis template
│   ├── AUDIT.md                               # Codebase and experimental audit log
│   ├── CHANGELOG.md                           # Milestone log
│   ├── RUN_QUEUE.md                           # Task queue log
│   ├── WORKFLOW.md                            # Detailed multi-phase workflow specification
│   └── 1_Antigravity_Agent_Instructions.md    # Initial orchestration instructions
│
├── incoming/                                  # Staging directory for downloaded Colab output zips
└── bundle/                                    # Compressed distribution packages
```

---

## 🔬 Key Scientific Findings

1. **Architecture-Dependent Transfer Mechanics (Hypothesis H1):**
   - **CompressAI (Factorized Neural Codec):** Conforms closely to analytical Wiener filtering ($R^2 \in [0.928, 0.997]$). The effective noise parameter $N_{\text{eff}}$ scales monotonically across compression qualities, decreasing by $\approx 44\times$ (from $2.41 \times 10^{-7}$ at $q=1$ to $5.52 \times 10^{-9}$ at $q=8$).
   - **SD-VAE (Continuous Latent Autoencoder):** Violates linear shift-invariance due to spatial $8\times$ downsampling and patch decoders, resulting in poor or negative fits ($R^2 \in [-2.45, 0.43]$).
2. **The "Two Forces" Trade-Off & Baseband Failure (Band 0):**
   - Band 0 ($[0, 0.0625)\text{ cyc/px}$) achieves the highest structural similarity ($\text{SSIM} = 0.9842$) because smooth luminance shifts leave local Gaussian cross-correlations intact.
   - However, empirical zero-mean host cover variance is $26.6\times$ higher in Band 0 ($\sigma^2 = 0.0474$) than Band 2 ($\sigma^2 = 0.00178$). At $40.0\text{ dB}$ PSNR, the raw signal-to-interference ratio is $-26.8\text{ dB}$ in Band 0 vs. $-12.5\text{ dB}$ in Band 2 (a $14.3\text{ dB}$ host advantage), causing Band 0 detection to collapse.
3. **Attack-Dependent Robustness Window (Hypothesis H3):**
   - Under aggressive regeneration (SD-VAE), **Band 1** is optimal across all noise strengths ($\text{TPR} = 55.0\%$ at $\sigma=0.00$, $26.6\%$ at $\sigma=0.20$), strictly outperforming Band 2. Bands 1 and 2 collectively form the survivable operational window.
   - Under variable-rate compression (CompressAI), the survival boundary matches $f_c$, with higher bands activating as quality increases (reaching $100.0\%$ bit accuracy at $q=8$).
4. **Learned Watermarking Diagnosis (Track C):**
   - Compact CNNs trained under a strict $40\text{ dB}$ PSNR budget ($\approx 2.55$ intensity levels) without carrier priors or progressive curriculum stalled near chance accuracy ($49.83\% \pm 8.49\%$, $0.0\%$ TPR) even on unattacked images. Consequently, surrogate efficacy remains untested until progressive curriculum training is applied.

---

## 🚀 Reproduction & Execution

### 1. Environment Setup
```bash
# Create and activate Python 3.11 virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Sanity Gate G0 Check
Verify PyTorch, Torchvision, CompressAI, Diffusers, and GPU/CPU functionality:
```bash
python gate_g0.py
```

### 3. Re-running Empirical Analyses
Run analysis scripts located in `scripts/analysis/`:
```bash
# Perceptual metrics (PSNR & SSIM)
python scripts/analysis/task5_perceptual.py

# Host cover variance and SIR calculation
python scripts/analysis/task7_host_interference.py

# Wiener fit quality across models
python scripts/analysis/task3_wiener_fit.py

# Optimal band vs. cutoff comparison
python scripts/analysis/task4_best_band.py

# 4-panel held-out benchmark visualization
python scripts/analysis/task2_plot_full_benchmark.py

# Explanatory diagrams (300 DPI)
python scripts/analysis/task10_explanatory_figures.py
```

### 4. Compiling the Final Thesis Document
To compile the final Word report (`.docx`) conforming to IIIT Pune guidelines:
```bash
python scripts/build_btp_report_v3.py
```
Outputs:
- Root: [`BTP_Final_Report_Spectral_Watermarking.docx`](file:///home/viseash/Ashley/Work/Internship/BTP_Final_Report_Spectral_Watermarking.docx)
- Report: [`report/BTP_Final_Report_Spectral_Watermarking.docx`](file:///home/viseash/Ashley/Work/Internship/report/BTP_Final_Report_Spectral_Watermarking.docx)

---

## 📄 Primary Deliverables

| Deliverable | Format | Location | Description |
| :--- | :--- | :--- | :--- |
| **BTP Final Report** | Word (.docx) | [`BTP_Final_Report_Spectral_Watermarking.docx`](file:///home/viseash/Ashley/Work/Internship/BTP_Final_Report_Spectral_Watermarking.docx) | Fully styled institutional thesis document |
| **BTP Final Report** | Markdown (.md) | [`report/BTP_Final_Report_Spectral_Watermarking.md`](file:///home/viseash/Ashley/Work/Internship/report/BTP_Final_Report_Spectral_Watermarking.md) | Formatted report text with KaTeX equations |
| **Executive Summary** | Markdown (.md) | [`report/final_results_summary.md`](file:///home/viseash/Ashley/Work/Internship/report/final_results_summary.md) | High-level summary of empirical conclusions |
| **Master Evaluation Data** | CSV | [`results/v2/T2/master.csv`](file:///home/viseash/Ashley/Work/Internship/results/v2/T2/master.csv) | 77,000 evaluations across 500 test images |
| **Benchmark Figures** | PNG (300 DPI) | [`figures/v2/`](file:///home/viseash/Ashley/Work/Internship/figures/v2/) | Publication-ready visual assets |

---

## 📚 References
1. I. J. Cox et al., "Secure spread spectrum watermarking for multimedia," *IEEE TIP*, 1997.
2. J. Zhu et al., "HiDDeN: Hiding images with deep networks," *ECCV*, 2018.
3. M. Tancik et al., "StegaStamp: Invisible hyperlinks in physical photographs," *CVPR*, 2020.
4. T. Bui et al., "TrustMark: Universal watermarking for arbitrary resolution images," *arXiv:2311.18297*, 2023.
5. X. Zhao et al., "Invisible image watermarks are provably removable using generative AI," *NeurIPS*, 2024.
6. S. Lu et al., "Robust watermarking using generative priors against image editing: From benchmarking to advances," *ICLR*, 2025.
7. R. Rombach et al., "High-resolution image synthesis with latent diffusion models," *CVPR*, 2022.
8. A. van den Oord et al., "Neural discrete representation learning," *NeurIPS*, 2017.
9. D. L. Ruderman, "The statistics of natural images," *Network: Computation in Neural Systems*, 1994.
10. T. Y. Lin et al., "Microsoft COCO: Common objects in context," *ECCV*, 2014.
11. J. Ballé et al., "Variational image compression with a scale hyperprior," *ICLR*, 2018.
12. E. B. Wilson, "Probable inference, the law of succession, and statistical inference," *JASA*, 1927.
