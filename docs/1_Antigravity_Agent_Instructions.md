# Agent Instructions: Strengthening and Explaining the Spectral Watermarking Project

**Audience:** Antigravity (coding agent working in the project repository).
**Purpose:** Turn a completed but thinly-evidenced B.Tech project into one whose claims are backed by data, whose weak points are diagnosed, and whose behaviour can be explained and defended in a viva.

---

## 0. Project in one paragraph

Invisible watermarks hide a 32-bit message in an image. A *regeneration attack* passes the image through a VAE (noise, then reconstruct), which keeps the visual content but erases the watermark. The project's thesis: a VAE behaves like a **low-pass filter on the watermark**, well approximated by a Wiener gain

```
G(f) = P(f) / ( P(f) + N_eff )          P(f) = A · f^(−α)  (natural-image power spectrum)
f_c  = ( A / N_eff )^(1/α)              (frequency where gain = 0.5)
```

so a watermark should live in frequency bands below `f_c`. The project has three parts:

1. **Measurement and fit:** measure the VAE's transfer function H(f) with band-limited probes, fit the Wiener model.
2. **Classical sweep:** spread-spectrum watermark in 8 radial bands × 4 PSNR levels × 14 attack strengths × 300 images.
3. **Learned encoder:** small CNN with a learnable band-allocation layer, trained through a Fourier-domain surrogate of the VAE.

Attacks: CompressAI `bmshj2018` (quality 1–8) and Stable Diffusion VAE `sd-vae-ft-mse` with pre-noise σ in [0, 0.20]. Images are 256×256 COCO 2017. Embedding PSNR is matched at 40 dB for the held-out benchmark. Payload is 32 bits. Detection threshold is τ = 24 of 32 (FPR = 0.35% under a Binomial(32, 0.5) null).

## 1. Ground rules (read before touching anything)

1. **Never fabricate or "tidy" numbers.** Every number that appears in the report must be reproducible from a results CSV written by code in this repo. If an experiment fails or looks bad, report that.
2. **Do not overwrite existing results.** Write new outputs to `results/v2/` and `figures/v2/`; keep a `CHANGELOG.md` noting what changed and why.
3. **Seed everything** (numpy, torch, python `random`) and record seeds in the CSV.
4. **Deterministic attacks:** for stochastic attacks use the same seed for `A(x)` and `A(x_w)`.
5. **Tidy-results schema** for every new CSV: `method, band, attack, strength, psnr_target, psnr_actual, image_id, bit_acc, detected, lpips, ssim`.
6. **Compute model:** CPU work runs locally; GPU work is packaged as a Colab notebook that the user runs while you wait (Section 3). Make every script resumable and device-agnostic (`cuda` if available, else `cpu`).
7. **Statistics:** report TPR with 95% Wilson confidence intervals. Use τ = 24 unless a different threshold is derived from the binomial tail (`scipy.stats.binom.sf`).
8. **Honesty over polish.** The report already contains a learned-model null result. Do not hide or overwrite it; diagnose it (Task 1).

## 2. Step zero: orient yourself

- Locate the code for: data prep, attack wrappers, probe/carrier generation, the sweep, the learned model, the evaluation script, and the figure scripts.
- Locate existing result CSVs and checkpoints.
- Write `AUDIT.md` summarising: file map, how to run each stage, any hard-coded paths, and anything that looks inconsistent with the numbers in the report (for example, the number of images actually used in the held-out run).
- Re-run one small slice (a few images) end to end to confirm the environment works before launching any long job.

## 3. Execution model: local runs vs Colab hand-offs

You run local scripts yourself. You cannot run a GPU job: for those you **write a Colab notebook, hand it to the user, and wait**. The user runs it on Colab (free T4), then returns the outputs to you. Everything in this document must respect that loop.

### 3.1 Decide where each piece runs

| Run locally | Hand off to Colab |
| --- | --- |
| Data prep, manifests, preprocessing | Anything using the Stable Diffusion VAE at scale |
| Radial-spectrum utilities, probe/carrier generation | Any model training or retraining (Tasks 1 and 8) |
| Fits, R², statistics, Wilson CIs, tables, plots | Large CompressAI sweeps (many images x many qualities) |
| Metrics (PSNR, SSIM, LPIPS) on saved images | Anything your timing benchmark says is too slow on CPU |
| Report edits | |

**Benchmark before deciding.** The local machine is a laptop (Ryzen 5 5500U, 8 GB RAM, no GPU). Time a 5-image slice of the job locally and extrapolate. Run it locally if the full job is under about 20 minutes of CPU time and fits in memory; otherwise make a notebook.

**Split every task into two stages.**
1. **GPU stage (Colab):** produce *raw* measurements only: per-image rows, per-band energies, decoded bits, saved example images. No fancy analysis.
2. **Local stage:** fits, statistics, tables and figures computed from the returned raw files.

This keeps round trips to a minimum: you can change an analysis or a plot locally without asking the user to rerun Colab. Therefore save *more* raw data than you think you need.

### 3.2 Notebook requirements

Each Colab notebook goes in `notebooks/` and is named `colab_T<task>_<short-name>_v<N>.ipynb` (for example `colab_T2_heldout500_v1.ipynb`). Every notebook must:

1. **Start with a markdown header cell** stating: purpose, runtime type (GPU), estimated run time, inputs it needs on Drive, exact outputs it produces, and how to resume if it disconnects.
2. **Setup cells:** mount Drive; set a working folder on Drive (`MyDrive/watermark_project/`); print the GPU (`nvidia-smi`); install pinned dependencies from the bundle's `requirements.txt`; set all seeds.
3. **Load code and data from the bundle** (Section 3.3). Never assume files that are not in the bundle. Public models only (`stabilityai/sd-vae-ft-mse`, CompressAI zoo weights), so no tokens or API keys are needed.
4. **Smoke test cell:** run the whole pipeline on 3 images in under 2 minutes with assertions (tensor shapes, PSNR near target, no NaNs). Stop with a clear error if it fails. Also expose a `SMOKE = True` flag so you can run the same notebook logic locally on CPU on a tiny slice before handing it over.
5. **Resumable main loop:** write partial results to Drive every N images (default 25) and skip rows already present on restart. Training must save a checkpoint to Drive every epoch and resume from the latest one.
6. **Chunked:** design each notebook to finish within about 60 to 90 minutes. If a job is longer, split it with a `CHUNK_ID` parameter (for example by attack family or image range) and write one notebook run per chunk.
7. **Final cells:** validate outputs (expected row counts, no NaNs, columns match the CSV schema), then write one return package (Section 3.5) and print its path.
8. **Be device-agnostic.** The same code path must run on CPU in smoke mode.

### 3.3 The bundle

Build `bundle/` and zip it as `project_bundle_v2_<date>.zip`. It contains: the code (`core/` and any track code the notebook needs), a pinned `requirements.txt`, split manifests, the preprocessed 256x256 PNGs the notebook needs (500 test images; fit images only if required), existing checkpoints, and a `config.json`. Keep it under about 200 MB. The user uploads it to `MyDrive/watermark_project/` once; notebooks unzip it. Increment the bundle version whenever code changes, and state the version in each run request.

### 3.4 Run request (how you hand off)

When a notebook is ready, validated locally in smoke mode, post exactly this message and then **stop working on anything that depends on it**:

```
RUN REQUEST  T<task>  v<N>
Notebook:        notebooks/<name>.ipynb
Upload first:    project_bundle_v2_<date>.zip -> MyDrive/watermark_project/
Runtime:         Colab, GPU (T4), High-RAM not required
Estimated time:  <minutes>   (chunks: <n>, set CHUNK_ID = 0..n-1)
If it disconnects: re-run all cells; it resumes automatically
Return to me:    <package name>.zip  -> place in incoming/T<task>/
Package holds:   <list of CSVs / NPZ / checkpoints / log>
What I do next:  <the local analysis you will run when it arrives>
```

Do not guess results while waiting, and do not fill in numbers from smoke runs.

### 3.5 Return package and ingest

Every notebook ends by creating `results_T<task>_v<N>[_chunk<k>]_<timestamp>.zip` containing:

- the raw result CSV/NPZ files (tidy schema from Section 1),
- `manifest.json`: task, notebook version, bundle version, git hash or bundle hash, library versions, GPU name, seeds, start/end time, row counts per file, and SHA-256 of each file,
- `log.txt` with the printed output,
- the executed notebook (`.ipynb` with outputs),
- trained checkpoints, if any (keep them small; note sizes in the manifest).

**When the user places a package in `incoming/T<task>/`, you ingest it:**
1. Verify `manifest.json`: checksums match, row counts match expectations, versions match what you requested, no NaNs.
2. Run `scripts/ingest.py` (write it once): unzip to `results/v2/T<task>/`, concatenate chunks, de-duplicate rows by key, and append to the master results CSV.
3. Run the sanity checks for that task (for example H close to 1 in the lowest bands at mild strength; unattacked bit accuracy near the expected ceiling). If a check fails, diagnose first, and if needed issue a new notebook version (`v<N+1>`). Never silently reinterpret or patch bad data.
4. Run the local analysis stage, regenerate the tables and figures, and report back (Section 7).

### 3.6 Keep a run queue

Maintain `RUN_QUEUE.md` as a table with one row per notebook: task, notebook, version, status (`drafted`, `smoke-tested`, `awaiting user`, `returned`, `ingested`, `needs rerun`), requested date, and notes. Update it every time something changes.

### 3.7 Do not sit idle

Order your work like this:
1. Run the Step 0 audit.
2. Build and smoke-test **all** the Colab notebooks you can, starting with a tiny environment check notebook `colab_T0_env_check_v1.ipynb` (prints the GPU, installs dependencies, loads the SD VAE and one CompressAI model, times one forward pass at 256x256, and returns a small `timing.json`). Use its timings to size the real chunks.
3. Post the run requests, ideally in a batch, in priority order (Task 1 and Task 2 first).
4. While the user runs them, do all the local tasks (Group 1 in Section 4).
5. Ingest returned packages as they arrive.

## 4. Task graph (what can run in parallel)

```
Step 0 (audit)
   |
   +-- Group 1 (local, independent) ------------------------+
   |     Task 3  fit-quality tables                        |
   |     Task 5  perceptual metrics                        |
   |     Task 6  linearity + leakage                       |
   |     Task 7  "why band X fails" analysis               |
   |     Task 9  report fixes                              |
   |                                                       |
   +-- Group 2 (GPU stages -> Colab notebooks) -------------+
   |     Task 1  learned-model diagnostic  --> Task 8      |
   |     Task 2  500-image held-out rerun                  |
   |                                                       |
   +-- Group 3 (needs Group 1 outputs) --------------------+
         Task 4  H2: best band vs f_c
         Task 10 explanatory figures
```

Group 2 items are GPU stages: build their Colab notebooks first, post the run requests, then work through Group 1 locally while the user runs the notebooks. In every task the analysis stage runs locally once the raw results are ingested (Section 3).

---

## Task 1: Diagnose the learned model (highest priority)

**Where it runs:** Hybrid. *Local:* evaluate the existing checkpoint with no attack if the model is small enough for CPU (step 1), and inspect the code for bugs (step 3). *Colab:* the overfit test and any retraining (steps 2 and 5) as `colab_T1_learned_diag`, returning training curves, `g_b` history and checkpoints.

**Why:** the main learned model scores about 50% bit accuracy everywhere, including conditions where the fixed-low control reaches 77%. A model at chance even with no attack usually indicates a bug, not a scientific null result.

**Steps**
1. Run the trained learned model with **identity noise (no attack)** on 500 held-out images. Report bit accuracy.
2. **Overfit test:** train on about 100 images, identity noise only, 16-bit payload. Bit accuracy should reach near 100% quickly. If it does not, find the bug (message injection into the encoder, loss wiring, sign convention of targets, decoder output shape, learning rate, BatchNorm in eval mode, residual energy normalisation collapsing to zero).
3. Check that the band-allocation layer's output residual RMS equals the target (PSNR 40 dB) and that the band shares `g_b = softmax(θ)` sum to 1.
4. Plot training curves: BCE loss, bit accuracy per noise type, and the evolution of `g_b` over epochs.
5. If a bug is found, fix it, retrain in this order: identity only, then identity plus light noise, then the full noise mixture, then the mixture with the Fourier surrogate.

**Acceptance criteria**
- A table with no-attack bit accuracy for: learned main, learned low/mid/high controls.
- A short written diagnosis (`results/v2/learned_diagnosis.md`): either "bug found and fixed, here is the new result" or "pipeline verified correct (identity accuracy X%), so the null result under attack is genuine".

**Outputs:** `results/v2/learned_diagnosis.md`, training-curve figure, updated checkpoints if retrained.

## Task 2: Rerun the held-out benchmark on all 500 test images

**Where it runs:** *Colab* for every attack and decode pass (SD VAE and CompressAI, all methods, plus unwatermarked-attacked images for the null check), chunked by attack family, returning per-image rows (`bit_acc`, `detected`, decoded bits). *Local* for Wilson CIs, significance tests, Tables 1 and 2 and Figure 4.

**Why:** every TPR in the report is a multiple of 1/64, so the benchmark used 64 images. At n = 64, a TPR cell carries up to ±12 percentage points of sampling error.

**Steps**
1. Confirm the 500-image test manifest exists and does not overlap fit/train splits.
2. Run all methods (classical Band 2, classical Band 0, ideally all 8 classical bands, the three learned controls, learned main) against every attack setting (SD VAE σ levels, CompressAI q = 1–8) at 40 dB.
3. Compute bit accuracy, TPR at τ = 24, and Wilson 95% CIs. Also compute an empirical null: decode unwatermarked, attacked images and confirm mean bit agreement is about 50% with no strong per-bit bias.
4. Regenerate Tables 1 and 2 and Figure 4 from the new CSV.

**Acceptance criteria:** new tables with CIs; a statement of whether Band 2 > Band 0 is statistically significant at each strength (non-overlapping intervals or a two-proportion test).

## Task 3: Full fit-quality table for the Wiener model

**Where it runs:** *Colab* for the probe measurement sweeps (raw per-band input and output energy per image, attack, strength, band), unless the local timing benchmark shows the CompressAI part fits on CPU. *Local* for all fits, R², held-out-strength prediction, the `N_eff` vs sigma^2 regression and the plots.

**Why:** the report cites R² only for CompressAI q = 1 and 2 and admits the fit degrades at higher quality.

**Steps**
1. For every CompressAI quality (1–8) and every SD VAE σ, report: fitted `N_eff`, R² against measured H(f), RMSE, predicted `f_c`, and measured `f_c` (frequency where H crosses 0.5, by linear interpolation).
2. **Held-out strength test (non-circular prediction):** fit `N_eff` on a subset of strengths (for example q = 1, 3, 5, 7), interpolate in log `N_eff` against strength, and predict `f_c` at the left-out strengths (q = 2, 4, 6, 8). Report prediction error.
3. **Theory check on the SD VAE:** with an orthonormal FFT, pre-noise of std σ has flat spectrum σ², so `N_eff` should scale about linearly with σ². Fit `N_eff = c · σ² + b`, report slope, intercept and R². Make the comparison on a log-log plot as well.
4. Plot predicted vs measured `f_c` with a y = x line and annotate the error.

**Acceptance criteria:** one table covering all strengths, the held-out-strength prediction table, and Figure 2 regenerated with the numbers shown on the figure.

## Task 4: Properly test H2 (best band vs cutoff)

**Where it runs:** Local, from the classical sweep CSV (and the Task 3 `f_c` values).

**Why:** the report's H2 claim is the weaker "collapse boundary matches f_c". The stronger question is whether the best-performing band tracks `f_c` as attack strength changes.

**Steps**
1. From the classical sweep, for each attack and strength find the band with maximum bit accuracy (and its confidence interval).
2. Plot best band centre frequency vs predicted `f_c(strength)` on the same axes, for both attacks.
3. Report whether the best band moves lower as strength grows.
4. If the best band does not track `f_c` (for example Band 2 always wins), say so and explain using Task 7 (host-image interference in the lowest bands).

**Outputs:** `figures/v2/best_band_vs_fc.png` and a two-sentence conclusion for the report.

## Task 5: Perceptual metrics at matched PSNR

**Where it runs:** Local. SSIM and LPIPS between `x` and `x_w` need no VAE pass; benchmark LPIPS on CPU first, and only use Colab if it is too slow.

**Why:** H3 is about robustness at matched PSNR, but PSNR alone does not show how visible a pattern is. Low-frequency patterns tend to be more visible at the same PSNR.

**Steps**
1. For each band at 40 dB, compute SSIM and LPIPS (AlexNet, `lpips` package) between `x` and `x_w` over the test set.
2. Plot LPIPS and SSIM per band; add a robustness-vs-LPIPS scatter (bit accuracy under a fixed mid-strength attack vs LPIPS) to show the trade-off.
3. Save 3 or 4 side-by-side example images (original, watermarked per band, residual amplified 10×).

**Acceptance criteria:** per-band perceptual table plus the example figure.

## Task 6: Linearity check and leakage matrix

**Where it runs:** *Colab* for the multi-amplitude probe passes (raw per-band energies for each probe band and output band). *Local* for the H(f) overlay and the leakage heatmap.

**Why:** the Wiener model assumes the VAE acts linearly on the watermark. These two checks test that assumption directly and are interesting results in themselves.

**Steps**
1. **Amplitude dependence:** repeat the Track A measurement at probe PSNR of 30, 35, 40, 45, 50 dB. Plot H(f) for each. If the curves overlap, the VAE is approximately linear at watermark scale; if not, report where it breaks.
2. **Leakage matrix:** embed a probe in band `i`; measure the output energy in every band `j` of `A(x_w) − A(x)`. Plot an 8×8 heatmap. Off-diagonal energy shows the VAE moving energy between bands (nonlinearity or aliasing).

**Outputs:** two figures and a short paragraph for the Limitations section.

## Task 7: Explain why each band behaves as it does

**Where it runs:** Local. Cover-image band energy and no-attack bit accuracy need no VAE.

**Why:** the biggest unexplained observation: Band 0 is poor (about 58%) even though it is the lowest, safest band.

**Hypothesis to test:** in the lowest bands the *cover image* has enormous energy, so blind correlation decoding is dominated by host interference, not by the attack.

**Steps**
1. For each band, compute the mean cover-image energy in that band (from the radial profile) and the watermark energy at 40 dB.
2. Compute the **no-attack** bit accuracy per band. If Band 0 is already low with no attack, the explanation is host interference.
3. Compute a theoretical decoding SNR per band: `SNR_b ≈ (watermark energy in band) / (cover energy in band)` times the processing gain (number of degrees of freedom in the band). Show it predicts the no-attack accuracy.
4. Combine both effects into one "two-forces" figure: x = band, curves for (a) VAE gain `G` at the band centre, (b) cover-interference ceiling, (c) measured bit accuracy. The optimum sits where the two losses balance, which is why Band 2 wins.
5. Optional improvement as a clearly labelled extra experiment: non-blind decoding or a whitening step that reduces host interference, to show Band 0 can recover.

**Outputs:** the two-forces figure and a paragraph for the Discussion chapter.

## Task 8: Learned band-allocation results (only after Task 1)

**Where it runs:** *Colab* for training (main, no-surrogate ablation, three fixed-band controls) and held-out evaluation: one notebook per model, with per-epoch checkpoints on Drive. *Local* for the learned-gains figure and ablation table.

**Steps**
1. With a working model, train: (a) main model with surrogate in the noise mixture, (b) the same model without the surrogate, (c) fixed-low / fixed-mid / fixed-high controls, trained equally long.
2. Evaluate all on the held-out SD VAE and CompressAI (500 images).
3. Plot the learned band shares `g_b` per attack strength (train one model per strength group, or condition on strength).
4. Report the surrogate ablation (a) vs (b). A negative result is acceptable if properly diagnosed and clearly reported.

**Acceptance criteria:** learned-gains figure, surrogate ablation table, honest one-paragraph conclusion.

## Task 9: Report corrections (small, mechanical)

**Where it runs:** Local.

Apply these edits to the report source and list them in `CHANGELOG.md`.

1. **References:** merge entries [12] and [13] into one:
   Lu, S., et al. (2025). *Robust Watermarking Using Generative Priors Against Image Editing: From Benchmarking to Advances.* ICLR 2025. arXiv:2410.18775. (This paper introduces both W-Bench and VINE.)
2. **Reference [11]:** authors should be Zhao, X., et al. (Xuandong Zhao et al.), *Invisible Image Watermarks Are Provably Removable Using Generative AI*, NeurIPS 2024, arXiv:2306.01953.
3. **Section 2.2:** Zhao et al. show that pixel-level invisible watermarks are removable by regeneration (not "JPEG-style" ones). VINE is a watermarking method that uses blur-type surrogate attacks and a generative prior; it is not a "learnable attack surrogate".
4. **Abstract and conclusion:** replace "B0-B2 remain resilient" with the Band 2 finding; state that Band 0 is weak and why (Task 7). Replace "comparable to classical Band 2" (77.1% vs 98.2%) with an accurate comparison. Learned-main range is 48.9–50.1% and covers six σ conditions plus eight q conditions, so state it that way.
5. **R² claims:** replace the 0.877–0.910 range by the full table from Task 3.
6. Fill every `[Supervisor Name]` placeholder (cover, certificate, acknowledgement).
7. Pick one spelling convention (British or American) and apply it everywhere.
8. Update every number that Tasks 2, 3, 5 produce, with the new CI where relevant.

## Task 10: Explanatory figures (makes the project presentable)

**Where it runs:** Local, except figures 1 and 4 which need VAE outputs: add one small Colab notebook (`colab_T10_figure_data`) that saves the example images, attacked versions and decoded bits as PNG/NPZ, then draw the figures locally.

Create clean, labelled figures, each with a one-line takeaway caption:

1. **Before/after-VAE spectrum:** one image, its radial power spectrum before and after regeneration, with the cutoff `f_c` marked.
2. **Band map:** the 8 annuli drawn on a 2D frequency plane, labelled with cycles/pixel ranges.
3. **What a watermark looks like per band:** residual patterns (amplified) for bands 0, 2, 5, 7.
4. **Survival story:** one watermarked image through the SD VAE with decoded bits shown (correct/incorrect) per band.
5. **Wiener intuition:** plot of `P(f)`, `N_eff`, and `G(f)` on one chart, marking where `P = N_eff`.
6. **Pipeline diagram** of the three parts (measure and fit; classical sweep; learned encoder with surrogate).

## 5. Optional extensions (only if everything above is done)

- **Diffusion regeneration** (noise, then denoise for a few steps) on about 100 images, as an extra attack to test whether the fitted model transfers.
- **TrustMark reference** (`pip install trustmark`) through the same runner and attacks.
- **Bands 1 and 3** with finer bands (16 annuli) around the best band to localise the optimum.
- **Payload size sweep** (16, 32, 64 bits) to show the capacity-robustness trade-off for Band 2.

## 6. Deliverables checklist

- [ ] `AUDIT.md`
- [ ] `RUN_QUEUE.md`, `scripts/ingest.py`, and the bundle zip
- [ ] `colab_T0_env_check_v1.ipynb` and its returned `timing.json`
- [ ] One smoke-tested Colab notebook per GPU stage, each with a run request
- [ ] `results/v2/learned_diagnosis.md` plus training curves
- [ ] 500-image held-out tables and figure with Wilson CIs
- [ ] Full Wiener fit table, held-out-strength prediction, `N_eff` vs σ² fit
- [ ] Best-band-vs-`f_c` figure
- [ ] Per-band SSIM/LPIPS table and example images
- [ ] Linearity and leakage figures
- [ ] Two-forces figure (why Band 2 wins, why Band 0 fails)
- [ ] Learned-gains figure and surrogate ablation (if Task 1 allows)
- [ ] Explanatory figures from Task 10
- [ ] Corrected report text and `CHANGELOG.md`

## 7. Reporting back

After each task (and after each ingested Colab package), post a short note stating: what was run, where the outputs are, the key numbers, and anything surprising or contradicting the existing report. If a result contradicts a claim in the report, flag it explicitly instead of editing the claim silently.
