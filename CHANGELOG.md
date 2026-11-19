# CHANGELOG.md

All changes to code, results, and report content are logged here.
Format: `[date] [area] description`

---

## 2026-10-21

### Report (v1 → v2)
- Fixed held-out benchmark: 64 images, not 500; added ±12 pp sampling error caveat
- Fixed R² claim: "0.877–0.910" not ">0.88"
- Clarified 144,000 row count includes unattacked baselines
- Changed τ=23 → τ=24 (FPR=1.003% → 0.35%); all TPR values recomputed from CSV
- Replaced "prove/proved" with "demonstrate/show"
- Fixed band-collapse claim: 49.3% = mid-band (B3-5), 52% = high-band (B6-7)
- Added Section 4.5: explicit null result for learned model
- Removed "without visible artifacts" from H3 (no SSIM/LPIPS evidence)
- Softened H2 to "collapse boundary aligns with f_c"
- Fixed TrustMark citation: arXiv:2311.18297, Bui/Agarwal/Collomosse (not Tu/Zhang/Sun)
- Added W-Bench [12], VINE [13], Zhao et al. 2023 [11]
- Replaced Track A/B/C and Merge 2 with descriptive section names
- Fixed "Keywords: Keywords:" duplication
- Fixed garbled abstract sentence
- Added learned_main_surrogate row to Tables 1 & 2

---

## 2026-11-14

### Infrastructure
- Created AUDIT.md: full file map, inconsistencies with report, smoke test results
- Created RUN_QUEUE.md: notebook tracking table
- Created results/v2/, figures/v2/, notebooks/, incoming/T0,T1,T2/, bundle/ directories
- Wrote scripts/ingest.py: zip ingestion, checksum verification, deduplication, master CSV append
- Wrote notebooks/colab_T0_env_check_v1.ipynb
- Wrote notebooks/colab_T1_learned_diag_v1.ipynb
- Wrote notebooks/colab_T2_heldout500_v1.ipynb

### Analysis (Local)
- Task 3: Full Wiener fit quality table (all CompressAI q=1–8, all SD VAE σ levels)
- Task 4: Best band vs f_c analysis from track_b_sweep.csv
- Task 5: Per-band SSIM/LPIPS at 40 dB
- Task 7: Host interference analysis — confirmed Band 0 fails due to host interference even with no attack

### Key Finding (2026-11-14)
- **Smoke test confirms H7 immediately**: Classical SS Band 0 achieves only 62.5% bit accuracy with NO attack on 5 test images. Bands 2–7 achieve ≥97.5% with no attack. The Band 0 weakness is entirely due to host-image interference in the baseband, not the VAE attack.

### Citation Corrections (from instructions §Task 9)
- [11] Zhao → Zhao, X., et al. (Xuandong Zhao et al.), NeurIPS 2024, arXiv:2306.01953 (not "JPEG-style" — these are invisible pixel-level watermarks)
- [12,13] Merged: Lu, S., et al. (2025). Robust Watermarking Using Generative Priors Against Image Editing. ICLR 2025. arXiv:2410.18775. (Introduces both W-Bench benchmark and VINE method)
- Section 2.2 description of VINE corrected: VINE is a watermarking method, not "a learnable attack surrogate"

## [2026-11-14 16:25] - Ingested Chunk 0 (SD-VAE Held-Out Benchmark)
- Verified SHA-256 and ingested 33,000 rows from incoming/T2/results_T2_v1_chunk0_20261114_104607.zip into results/v2/T2/master.csv.
- Computed Wilson 95% CIs on TPRs for all 8 bands and null check across 6 SD-VAE noise levels.
- Generated publication figure: figures/v2/fig_heldout_sd_vae.png.
- Documented findings in results/v2/chunk0_empirical_findings.md.

## [2026-11-14 16:50] - Ingested Chunk 1 (CompressAI q=1-4 Held-Out Benchmark)
- Verified SHA-256 and ingested 22,000 rows from incoming/T2/results_T2_v1_chunk1_20261114_111200.zip into results/v2/T2/master.csv. Total rows now 55,000.
- Empirical confirmation of cutoff tracking: optimal band shifts from Band 1 (q=1) to Band 2 (q=2,3) to Band 3 (q=4).
- Band 0 remains suppressed (bit acc 57.3-58.8%, TPR <= 4.0%).
- Null check empirical FPR remains exactly 0.000%.

## [2026-11-14 17:10] - Full Held-Out Benchmark Complete (Chunks 0, 1, 2 Ingested)
- Ingested 22,000 rows from incoming/T2/results_T2_v1_chunk2_20261114_113454.zip into results/v2/T2/master.csv.
- Master dataset reaches complete planned size: 77,000 rows (500 test images x 11 methods x 14 attack conditions).
- Computed full Wilson 95% CIs across all 14 conditions and 8 bands.
- Generated comprehensive 4-panel publication figure: figures/v2/fig_heldout_benchmark_full.png.
- Full findings written to results/v2/full_heldout_benchmark_report.md.
