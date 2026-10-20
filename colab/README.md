# Multi-Colab Distributed Execution Guide

This folder contains the self-contained execution templates for running the heavy GPU tracks across multiple Google Colab accounts concurrently.

---

## 1. Distribution Matrix

| Worker | Google Account | Notebook / Task | Expected Run Time | Output Artifacts |
| :--- | :--- | :--- | :--- | :--- |
| **Worker A** | Colab Account 1 | `colab_worker_a.ipynb` (Track A: Transfer Sweeps & Wiener Fit) | ~35 mins (T4) | `results/track_a_transfer.csv`, `results/fitted_g.json` |
| **Worker B** | Colab Account 2 | `colab_worker_b.ipynb` (Track B: Classical Spread-Spectrum Sweep) | ~40 mins (T4) | `results/track_b_sweep.csv` |
| **Worker C** | Colab Account 3 | `colab_worker_c.ipynb` (Track C: Controls & Main Model Training) | ~60 mins (T4) | `checkpoints/c_controls/`, `checkpoints/c_stage1.pt` |
| **Worker D** | Colab Account 4 | `colab_worker_d.ipynb` (Track D: TrustMark & Held-Out Benchmark) | ~25 mins (T4) | `results/trustmark_baseline.csv`, `results/merge2_final_eval.csv` |

---

## 2. Standard 1-Click Setup on Colab

Each notebook starts with these cells:

```python
# Cell 1: Mount Google Drive for automatic artifact syncing
from google.colab import drive
drive.mount('/content/drive')
SHARED_DIR = '/content/drive/MyDrive/watermark_internship'

# Cell 2: Clone repository & install dependencies
!git clone https://github.com/<YOUR_USER>/<YOUR_REPO>.git /content/repo
%cd /content/repo
!pip install -q -r requirements.txt

# Cell 3: Unpack preprocessed splits from shared Google Drive
!mkdir -p /content/repo/data
!if [ -f $SHARED_DIR/processed_splits.zip ]; then cp $SHARED_DIR/processed_splits.zip /content/repo/data/; fi
!unzip -q /content/repo/data/processed_splits.zip -d /content/repo/data/
```

---

## 3. Worker Execution Commands

### Worker A (Account 1):
```bash
python -m track_a.measure --manifest data/manifests/fit_manifest.json --images_dir data/processed/fit --out results/track_a_transfer.csv
python -m track_a.fit --manifest data/manifests/fit_manifest.json --images_dir data/processed/fit --transfer_csv results/track_a_transfer.csv --out_json results/fitted_g.json

# Copy fitted_g.json to Google Drive for Worker C
!cp results/fitted_g.json /content/drive/MyDrive/watermark_internship/results/
```

### Worker B (Account 2):
```bash
python -m track_b.sweep --manifest data/manifests/fit_manifest.json --images_dir data/processed/fit --out results/track_b_sweep.csv

# Copy results CSV to Google Drive
!cp results/track_b_sweep.csv /content/drive/MyDrive/watermark_internship/results/
```

### Worker C (Account 3):
```bash
# 1. Sanity overfit (100 images)
python -m track_c.train --overfit_100 --epochs 10 --save_dir checkpoints/overfit_check

# 2. Train 3 Fixed-band Controls (Low, Mid, High)
python -m track_c.train --fixed_regime low --epochs 25 --save_dir checkpoints/control_low
python -m track_c.train --fixed_regime mid --epochs 25 --save_dir checkpoints/control_mid
python -m track_c.train --fixed_regime high --epochs 25 --save_dir checkpoints/control_high

# 3. Train Stage 1 Main Model
python -m track_c.train --epochs 30 --save_dir checkpoints/main_stage1

# 4. Once Worker A completes: Train Stage 2 with Surrogate (Merge 1)
python -m track_c.train --surrogate_json /content/drive/MyDrive/watermark_internship/results/fitted_g.json --epochs 30 --save_dir checkpoints/main_stage2
```

### Worker D (Account 4 / Merge 2):
```bash
# Run unified evaluation on 500 held-out images with SD VAE
python -m track_d.harness --manifest data/manifests/test_manifest.json --images_dir data/processed/test --out results/merge2_final_eval.csv
```
