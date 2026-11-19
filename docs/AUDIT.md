# AUDIT.md — Spectral Watermarking Project

Generated: 2026-11-14 by Antigravity agent.
Updated: see CHANGELOG.md for subsequent edits.

---

## 1. File Map

```
Internship/
├── core/
│   ├── attacks.py          Deterministic attack wrappers (CompressAI, SD VAE, Gaussian, JPEG)
│   ├── bands.py            8 disjoint annular masks over [0, 0.5] cyc/px (PyTorch + NumPy)
│   ├── dataset_utils.py    Image path resolution helpers
│   ├── probes.py           Band-limited probe generation, PSNR utils, 8-bit rounding
│   └── radial.py           2D frequency grid, luminance conversion
│
├── track_a/
│   ├── measure.py          Empirical H(f) measurement: probe → attack → energy ratio
│   └── fit.py              Power-spectrum fit (alpha, log_A) + Wiener N_eff LM optimization
│
├── track_b/
│   ├── watermark.py        ClassicalSpreadSpectrumWatermarker (embed/decode, 32-bit, any band)
│   └── sweep.py            Grid sweep: 8 bands × 4 PSNRs × 14 attack settings × N images
│
├── track_c/
│   ├── model.py            WatermarkEncoder (CNN + BandAllocationLayer) + WatermarkDecoder
│   ├── noise_layers.py     NoiseMixtureLayer incl. SpectralTransferSurrogate (Wiener filter)
│   └── train.py            Training loop with curriculum, checkpoint saving, g_b history
│
├── track_d/
│   ├── harness.py          Unified benchmark harness for final evaluation
│   ├── metrics.py          TPR/FPR, tau calculation
│   └── plots.py            Figure 4 generator
│
├── data/
│   ├── manifests/
│   │   ├── fit_manifest.json        300 image filenames (Track A/B calibration)  ← .jpg extension
│   │   ├── train_manifest.json      4200 image filenames (Track C training)      ← .jpg extension
│   │   └── test_manifest.json       500 image filenames (held-out benchmark)     ← .jpg extension
│   └── processed/
│       ├── fit/      300 PNGs (256×256) — PRESENT ✓
│       ├── test/     500 PNGs (256×256) — PRESENT ✓
│       └── train/    0 PNGs — MISSING (no train images available locally)
│
├── results/
│   ├── track_a_transfer.csv    336 rows: 8 bands × 7 CompressAI + 6 SD VAE × 7 PSNRs (not all combinations present)
│   ├── track_b_sweep.csv       144,000 rows: classical SS, all 8 bands, 300 images, 4 PSNRs, 14+baseline attacks
│   ├── merge2_final_eval.csv   5,376 rows: 6 methods × 14 attack conditions × 64 images
│   ├── fitted_g.json           Wiener fit: alpha=2.660, log_A=-8.737, N_eff per attack/strength
│   └── attack_strengths_calibration.csv
│
├── figures/
│   ├── fig1_transfer_functions.png
│   ├── fig2_cutoff_and_scaling.png
│   ├── fig3_classical_heatmaps.png
│   └── fig4_held_out_benchmark.png
│
├── colab/
│   ├── worker_a.ipynb, worker_b.ipynb, worker_c.ipynb, worker_d.ipynb  (legacy)
│
├── scripts/
│   └── build_docx_report.py    Programmatic .docx builder (python-docx)
│
├── data_prep.py                COCO download + resize to 256×256 + split
├── requirements.txt
└── WORKFLOW.md
```

---

## 2. How to Run Each Stage

### Environment
```bash
cd /home/viseash/Ashley/Work/Internship
source .venv/bin/activate   # or: .venv/bin/python
```

### Track A — Transfer Function Measurement
```bash
python -m track_a.measure \
    --manifest data/manifests/fit_manifest.json \
    --images_dir data/processed/fit \
    --out results/track_a_transfer.csv
python -m track_a.fit --csv results/track_a_transfer.csv --out results/fitted_g.json
```

### Track B — Classical Spread-Spectrum Sweep
```bash
python -m track_b.sweep \
    --manifest data/manifests/fit_manifest.json \
    --images_dir data/processed/fit \
    --out results/track_b_sweep.csv
```

### Track C — Learned Model Training (GPU required; Colab)
```bash
python -m track_c.train \
    --manifest data/manifests/train_manifest.json \
    --images_dir data/processed/train \
    --save_dir checkpoints/main_stage1 \
    --epochs 30
```

### Track D — Held-Out Benchmark (GPU required for SD VAE; Colab)
```bash
python -m track_d.harness \
    --manifest data/manifests/test_manifest.json \
    --images_dir data/processed/test \
    --out results/merge2_final_eval.csv \
    --attacks sd_vae compressai \
    --limit 64   # was 64, needs to be 500
```

### Report Build
```bash
python scripts/build_docx_report.py
```

---

## 3. Hard-Coded Paths / Known Issues

| Issue | Location | Severity |
|---|---|---|
| Manifests store `.jpg` extension but processed images are `.png` | `data/manifests/*.json` vs `data/processed/*/` | Medium — `dataset_utils.resolve_image_path` strips extension and tries both; works in practice |
| `--limit 64` default in Colab cells | `colab/worker_d.ipynb` | **Critical** — caused the 64-image benchmark reported as 500 |
| Train images absent locally | `data/processed/train/` is empty | High — Track C training cannot run locally; Colab only |
| No checkpoints locally | None found in repo | High — learned model cannot be evaluated locally |
| `fitted_g.json` has N_eff=0.01 for all attacks | `results/fitted_g.json` | Suspicious — all N_eff identical suggests fit did not converge properly or was hard-coded |
| `track_a_transfer.csv` has only 336 rows | Expected: 8 bands × 2 attacks × 14 strengths × 1 PSNR ≈ 224 rows; actual 336 suggests some variation | Minor |
| `lpips` column is 0.0 in both CSVs | `track_b_sweep.csv`, `merge2_final_eval.csv` | High — LPIPS was not actually computed |
| `ssim` is 0.9 (constant) in track_b | `track_b_sweep.csv` | High — SSIM was not actually computed |
| `track_d/harness.py` line 192 had a SyntaxError | Fixed in prior session | Resolved |

---

## 4. Inconsistencies with the Report

| Report Claim | Actual Data | Status |
|---|---|---|
| "500 test images" | 64 unique images in merge2_final_eval.csv | **Incorrect — acknowledged, being fixed (Task 2)** |
| "R² > 0.88" | R²=0.877 at q=1; fitted_g.json shows N_eff=0.01 (constant) for all attacks | **Suspicious — N_eff should vary; Task 3 to investigate** |
| "144,000-point sweep" | 144,000 rows incl. 9,600 unattacked baselines; 134,400 attacked | Technically accurate but needed clarification |
| "τ=23, FPR≤1%" | τ=23 gives exact FPR=1.003%; τ=24 gives 0.35% | Fixed in report to τ=24 |
| Learned model: 49–50% bit acc under attack | Confirmed from CSV | Correct. But cause unknown — no-attack accuracy not yet measured |
| Band 2 best classical | Confirmed from sweep and benchmark CSVs | Correct |
| Band 0 ~ 58% under SD VAE | Confirmed: 57.96% at σ=0 | Correct |

---

## 5. Smoke Test Result (2026-11-14)

```
Classical SS, no attack, 5 test images:
  Band 0: 0.6250  ← already weak (host interference)
  Band 1: 0.8875
  Band 2: 0.9750
  Band 3: 1.0000
  Band 4: 1.0000
  Band 5: 1.0000
  Band 6: 1.0000
  Band 7: 1.0000
Time for 5 images × 8 bands: 0.7s → 300 images × 8 bands ≈ 42s (locally feasible)
```

**Key observation:** Band 0 no-attack accuracy of 62.5% confirms the host-interference hypothesis for Task 7 even before any attack is applied. Band 2–7 all reach ≥97.5% with no attack; the attack is what distinguishes them.

---

## 6. Local vs Colab Decision

| Task | Local? | Rationale |
|---|---|---|
| Task 3: Full Wiener fit table | Mostly local — Track A data already exists for most conditions; may need Colab only if additional probe measurements needed | Local first |
| Task 4: Best band vs f_c | Fully local — uses track_b_sweep.csv | Local |
| Task 5: SSIM/LPIPS per band | Local — no VAE needed for x vs x_w metrics | Local |
| Task 6: Linearity / leakage | CompressAI part: local CPU (slow but feasible for 10–20 images). SD VAE part: Colab | Hybrid |
| Task 7: Host interference analysis | Fully local — no attack needed | Local |
| Task 10 local figures | Fully local | Local |
| Task 1: Learned model diag, identity no-attack | **Colab** — no checkpoint available locally; must load from Drive | Colab |
| Task 2: 500-image held-out benchmark | **Colab** — SD VAE requires GPU | Colab |
| Task 8: Retrain learned model | **Colab** — training requires GPU + time | Colab (after Task 1) |
