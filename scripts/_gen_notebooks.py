"""
Helper script to generate .ipynb notebooks as valid JSON files.
Run with: python scripts/_gen_notebooks.py
"""
import json
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"
NOTEBOOKS_DIR.mkdir(exist_ok=True)

def nb_base():
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10.0"
            },
            "accelerator": "GPU"
        },
        "cells": []
    }

def md_cell(source: str) -> dict:
    if isinstance(source, str):
        source = source.splitlines(keepends=True)
    return {
        "cell_type": "markdown",
        "id": f"md_{abs(hash(str(source))) % 10**9:09d}",
        "metadata": {},
        "source": source
    }

def code_cell(source: str) -> dict:
    if isinstance(source, str):
        source = source.splitlines(keepends=True)
    return {
        "cell_type": "code",
        "id": f"code_{abs(hash(str(source))) % 10**9:09d}",
        "metadata": {},
        "source": source,
        "outputs": [],
        "execution_count": None
    }

def save_nb(nb: dict, name: str):
    path = NOTEBOOKS_DIR / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"Written: {path}  ({path.stat().st_size} bytes)")

# ==========================================================================
# T0: colab_T0_env_check_v1.ipynb
# ==========================================================================
T0_HEADER = """\
# T0: Environment Check & Timing
Purpose: Verify Colab GPU, install dependencies, time one forward pass for SD VAE and CompressAI.
Runtime: GPU (T4). Estimated time: ~5 minutes.
Inputs: None (downloads public models automatically).
Outputs: `timing.json` with GPU name, model load times, inference times per batch size.
Return: `results_T0_v1_<timestamp>.zip` → place in `incoming/T0/`
"""

T0_SETUP = """\
import subprocess, sys, os, time, json, hashlib
from pathlib import Path

# Mount Drive and set working folder
from google.colab import drive
drive.mount('/content/drive')
DRIVE_DIR = Path('/content/drive/MyDrive/watermark_project')
DRIVE_DIR.mkdir(parents=True, exist_ok=True)

# Print GPU info
result = subprocess.run(
    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
    capture_output=True, text=True
)
gpu_info = result.stdout.strip()
print('GPU:', gpu_info)

# Install pinned deps
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
    'torch', 'torchvision', 'diffusers', 'transformers', 'accelerate',
    'compressai', 'lpips', 'scipy', 'scikit-image', 'pandas', 'tqdm'
], check=True)

import torch
print('PyTorch:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Device:', device)
"""

T0_COMPRESSAI = """\
import compressai.zoo as zoo
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
timing = {'gpu': gpu_info}

# Load CompressAI q=1
t0 = time.time()
ca_model = zoo.bmshj2018_factorized(quality=1, pretrained=True).eval().to(device)
timing['compressai_load_s'] = time.time() - t0

# Time inference
dummy = torch.rand(4, 3, 256, 256).to(device)
with torch.no_grad():
    t0 = time.time()
    for _ in range(3):
        out = ca_model(dummy)
    timing['compressai_bs4_ms'] = (time.time() - t0) / 3 * 1000
print(f'CompressAI loaded in {timing[\"compressai_load_s\"]:.1f}s, bs=4 inference: {timing[\"compressai_bs4_ms\"]:.0f}ms')
del ca_model
"""

T0_SDVAE = """\
from diffusers import AutoencoderKL

t0 = time.time()
vae = AutoencoderKL.from_pretrained('stabilityai/sd-vae-ft-mse').eval().to(device)
timing['sd_vae_load_s'] = time.time() - t0

dummy = torch.rand(2, 3, 256, 256).to(device) * 2 - 1  # [-1, 1]
with torch.no_grad():
    t0 = time.time()
    for _ in range(3):
        z = vae.encode(dummy).latent_dist.mean
        rec = vae.decode(z).sample
    timing['sd_vae_bs2_ms'] = (time.time() - t0) / 3 * 1000
print(f'SD VAE loaded in {timing[\"sd_vae_load_s\"]:.1f}s, bs=2 inference: {timing[\"sd_vae_bs2_ms\"]:.0f}ms')
del vae
"""

T0_PACKAGE = """\
import zipfile
from datetime import datetime

timing['timestamp'] = datetime.utcnow().isoformat()

out_path = Path('/tmp/timing.json')
with open(out_path, 'w') as f:
    json.dump(timing, f, indent=2)
print('Timing:', json.dumps(timing, indent=2))

# Create return package
ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
zip_path = DRIVE_DIR / f'results_T0_v1_{ts}.zip'
with zipfile.ZipFile(zip_path, 'w') as zf:
    zf.write(out_path, 'timing.json')
    # Write a simple manifest
    manifest = {'task': 'T0', 'version': 'v1', 'files': ['timing.json'], 'timing': timing}
    zf.writestr('manifest.json', json.dumps(manifest, indent=2))
print(f'Package saved to: {zip_path}')
print('Return this file: place it in incoming/T0/')
"""

nb_t0 = nb_base()
nb_t0["cells"] = [
    md_cell(T0_HEADER),
    code_cell(T0_SETUP),
    code_cell(T0_COMPRESSAI),
    code_cell(T0_SDVAE),
    code_cell(T0_PACKAGE),
]
save_nb(nb_t0, "colab_T0_env_check_v1.ipynb")


# ==========================================================================
# T1: colab_T1_learned_diag_v1.ipynb
# ==========================================================================
T1_HEADER = """\
# T1: Learned Watermark Diagnostics
**Purpose:** Load trained learned-model checkpoints from Drive, run no-attack evaluation on
100 test images, and run a 100-image overfit test to diagnose pipeline correctness.

**Runtime:** GPU (T4). Estimated time: ~25 minutes.

**Inputs (required on Drive):**
- `MyDrive/watermark_project/project_bundle_v2_<date>.zip` — project bundle
- `MyDrive/watermark_project/checkpoints/main_stage1/latest_checkpoint.pt`
- `MyDrive/watermark_project/checkpoints/learned_control_low/latest_checkpoint.pt`
- `MyDrive/watermark_project/checkpoints/learned_control_mid/latest_checkpoint.pt`
- `MyDrive/watermark_project/checkpoints/learned_control_high/latest_checkpoint.pt`

**Outputs (saved to Drive):**
- `no_attack_eval.csv` — columns: method, image_id, bit_acc
- `overfit_history.json` — per-epoch loss and bit_acc for the overfit sanity test

**Return:** `results_T1_v1_<timestamp>.zip` → place in `incoming/T1/`
"""

T1_SETUP = """\
import subprocess, sys, os, time, json, zipfile, hashlib
from pathlib import Path
from datetime import datetime

# ── Flags ────────────────────────────────────────────────────────────────────
SMOKE = False          # Set True to run 3-image smoke test only
N_EVAL_IMAGES = 3 if SMOKE else 100
N_OVERFIT_IMAGES = 3 if SMOKE else 20
OVERFIT_EPOCHS = 10 if SMOKE else 50
N_BITS = 32
SECRET_KEY = 42
PSNR_TARGET = 40.0
# ─────────────────────────────────────────────────────────────────────────────

# Mount Drive
from google.colab import drive
drive.mount('/content/drive')
DRIVE_DIR = Path('/content/drive/MyDrive/watermark_project')
DRIVE_DIR.mkdir(parents=True, exist_ok=True)

# GPU check
result = subprocess.run(
    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
    capture_output=True, text=True
)
gpu_info = result.stdout.strip()
print('GPU:', gpu_info)

# Install deps
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
    'torch', 'torchvision', 'diffusers', 'transformers', 'accelerate',
    'compressai', 'lpips', 'scipy', 'scikit-image', 'pandas', 'tqdm'
], check=True)

import torch
print('PyTorch:', torch.__version__, '| CUDA:', torch.cuda.is_available())
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
"""

T1_BUNDLE = """\
# ── Unzip Bundle ─────────────────────────────────────────────────────────────
REPO = Path('/content/repo')
REPO.mkdir(exist_ok=True)

bundle_zips = sorted(DRIVE_DIR.glob('project_bundle_v2_*.zip'))
if not bundle_zips:
    raise FileNotFoundError(
        f'No project_bundle_v2_*.zip found in {DRIVE_DIR}. '
        'Please upload the bundle to Drive first.'
    )
bundle_zip = bundle_zips[-1]  # most recent
print(f'Using bundle: {bundle_zip.name}')

with zipfile.ZipFile(bundle_zip, 'r') as zf:
    zf.extractall(REPO)
print(f'Bundle extracted to {REPO}')

# Add repo to sys.path so we can import track_* and core
sys.path.insert(0, str(REPO))
print('sys.path[0]:', sys.path[0])
"""

T1_CHECKPOINTS = """\
# ── Load Checkpoints ─────────────────────────────────────────────────────────
from track_c.model import WatermarkEncoder, WatermarkDecoder, BandAllocationLayer

CHECKPOINT_DIR = DRIVE_DIR / 'checkpoints'
CHECKPOINTS = {
    'learned_main_surrogate':  CHECKPOINT_DIR / 'main_stage1'      / 'latest_checkpoint.pt',
    'learned_control_low':     CHECKPOINT_DIR / 'learned_control_low'  / 'latest_checkpoint.pt',
    'learned_control_mid':     CHECKPOINT_DIR / 'learned_control_mid'  / 'latest_checkpoint.pt',
    'learned_control_high':    CHECKPOINT_DIR / 'learned_control_high' / 'latest_checkpoint.pt',
}

REGIME_MAP = {
    'learned_main_surrogate': None,
    'learned_control_low':    'low',
    'learned_control_mid':    'mid',
    'learned_control_high':   'high',
}

loaded_models = {}  # method -> (encoder, decoder)

for method, ckpt_path in CHECKPOINTS.items():
    if not ckpt_path.exists():
        print(f'  ⚠ Checkpoint not found, skipping: {ckpt_path}')
        continue
    regime = REGIME_MAP[method]
    enc = WatermarkEncoder(n_bits=N_BITS, fixed_regime=regime).to(device)
    dec = WatermarkDecoder(n_bits=N_BITS).to(device)
    ckpt = torch.load(ckpt_path, map_location=device)
    enc.load_state_dict(ckpt['encoder_state_dict'])
    dec.load_state_dict(ckpt['decoder_state_dict'])
    enc.eval(); dec.eval()
    loaded_models[method] = (enc, dec)
    print(f'  ✓ Loaded {method}')

print(f'Loaded {len(loaded_models)} model(s): {list(loaded_models.keys())}')
"""

T1_DATASETS = """\
# ── Load Test Images ─────────────────────────────────────────────────────────
import torchvision.transforms as T
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader
from PIL import Image
import glob

TEST_DIR = REPO / 'data' / 'processed' / 'test'
if not TEST_DIR.exists():
    # Fallback: look for data dir
    TEST_DIR = Path('/content/data/processed/test')
    TEST_DIR.mkdir(parents=True, exist_ok=True)

transform = T.Compose([
    T.Resize((256, 256)),
    T.ToTensor(),
])

def load_images_from_dir(d: Path, n: int):
    imgs = sorted(list(d.glob('*.png')) + list(d.glob('*.jpg')))[:n]
    tensors, ids = [], []
    for p in imgs:
        img = Image.open(p).convert('RGB')
        tensors.append(transform(img))
        ids.append(p.stem)
    if not tensors:
        raise FileNotFoundError(f'No images found in {d}')
    return torch.stack(tensors), ids  # (N, 3, 256, 256)

print(f'Loading up to {N_EVAL_IMAGES} test images from {TEST_DIR}')
test_imgs, test_ids = load_images_from_dir(TEST_DIR, N_EVAL_IMAGES)
print(f'Loaded {len(test_ids)} images. Shape: {test_imgs.shape}')
"""

T1_NO_ATTACK = """\
# ── No-Attack Bit Accuracy Evaluation ────────────────────────────────────────
import pandas as pd
from track_b.watermark import ClassicalSpreadSpectrumWatermarker

no_attack_rows = []

# Classical Band 2 sanity reference
print('\\n── Classical Band 2 (sanity reference) ──')
wm_classical = ClassicalSpreadSpectrumWatermarker(
    n_bits=N_BITS, secret_key=SECRET_KEY, device=device
)
payload = torch.randint(0, 2, (N_BITS,), dtype=torch.float32)

for i, (img, img_id) in enumerate(zip(test_imgs, test_ids)):
    x = img.unsqueeze(0).to(device)  # (1, 3, 256, 256)
    with torch.no_grad():
        wm_img = wm_classical.encode(x, payload, band_idx=2, psnr_db=PSNR_TARGET)
        decoded = wm_classical.decode(wm_img, band_idx=2)
    bit_acc = (decoded.round() == payload.to(device)).float().mean().item()
    no_attack_rows.append({'method': 'classical_band2', 'image_id': img_id, 'bit_acc': bit_acc})

mean_ba = sum(r['bit_acc'] for r in no_attack_rows) / max(len(no_attack_rows), 1)
print(f'  Classical Band 2 no-attack mean bit_acc: {mean_ba:.4f} (expected ~0.98+)')

# Learned models
for method, (enc, dec) in loaded_models.items():
    print(f'\\n── {method} ──')
    for img, img_id in zip(test_imgs, test_ids):
        x = img.unsqueeze(0).to(device)
        payload_b = torch.randint(0, 2, (1, N_BITS), dtype=torch.float32).to(device)
        with torch.no_grad():
            wm_img = enc(x, payload_b)
            logits = dec(wm_img)
            decoded_bits = (torch.sigmoid(logits) > 0.5).float()
        bit_acc = (decoded_bits == payload_b).float().mean().item()
        no_attack_rows.append({'method': method, 'image_id': img_id, 'bit_acc': bit_acc})

no_attack_df = pd.DataFrame(no_attack_rows)
print('\\nNo-attack evaluation summary:')
print(no_attack_df.groupby('method')['bit_acc'].agg(['mean', 'min', 'max']))

# Save to Drive
no_attack_csv = DRIVE_DIR / 'no_attack_eval.csv'
no_attack_df.to_csv(no_attack_csv, index=False)
print(f'\\nSaved: {no_attack_csv}')
"""

T1_OVERFIT = """\
# ── Overfit Test ──────────────────────────────────────────────────────────────
# Train encoder+decoder for OVERFIT_EPOCHS on N_OVERFIT_IMAGES, identity noise, 32-bit payload.
# Bit accuracy should reach >95% by epoch 20 if the pipeline is correct.
import torch.optim as optim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print(f'\\nRunning overfit test: {OVERFIT_EPOCHS} epochs on {N_OVERFIT_IMAGES} images')
overfit_imgs = test_imgs[:N_OVERFIT_IMAGES].to(device)
fixed_payload = torch.randint(0, 2, (N_OVERFIT_IMAGES, N_BITS), dtype=torch.float32).to(device)

# Use fresh models for overfit test (don't modify loaded checkpoints)
enc_ov = WatermarkEncoder(n_bits=N_BITS, fixed_regime=None).to(device)
dec_ov = WatermarkDecoder(n_bits=N_BITS).to(device)
enc_ov.train(); dec_ov.train()

optimizer = optim.Adam(list(enc_ov.parameters()) + list(dec_ov.parameters()), lr=1e-3)
criterion = torch.nn.BCEWithLogitsLoss()

history = {'loss': [], 'bit_acc': []}

for epoch in range(OVERFIT_EPOCHS):
    optimizer.zero_grad()
    wm_imgs = enc_ov(overfit_imgs, fixed_payload)
    logits = dec_ov(wm_imgs)
    loss = criterion(logits, fixed_payload)
    loss.backward()
    optimizer.step()

    with torch.no_grad():
        decoded = (torch.sigmoid(logits) > 0.5).float()
        bit_acc = (decoded == fixed_payload).float().mean().item()
    history['loss'].append(loss.item())
    history['bit_acc'].append(bit_acc)

    if (epoch + 1) % 10 == 0 or epoch == 0:
        print(f'  Epoch {epoch+1:3d}/{OVERFIT_EPOCHS}  loss={loss.item():.4f}  bit_acc={bit_acc:.4f}')

final_bit_acc = history['bit_acc'][-1]
print(f'\\nFinal overfit bit_acc: {final_bit_acc:.4f}')
if final_bit_acc > 0.95:
    print('✓ PASS: Pipeline is correct (bit_acc > 0.95)')
else:
    print('✗ WARN: Pipeline may have a bug (bit_acc <= 0.95 after overfit)')

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.plot(history['loss']); ax1.set_title('Overfit Loss'); ax1.set_xlabel('Epoch')
ax2.plot(history['bit_acc']); ax2.axhline(0.95, color='r', linestyle='--', label='0.95')
ax2.set_title('Overfit Bit Accuracy'); ax2.set_xlabel('Epoch'); ax2.legend()
plt.tight_layout()
plot_path = '/tmp/overfit_plot.png'
plt.savefig(plot_path, dpi=100)
plt.show()
print(f'Plot saved: {plot_path}')

# Save history to Drive
overfit_path = DRIVE_DIR / 'overfit_history.json'
with open(overfit_path, 'w') as f:
    json.dump(history, f, indent=2)
print(f'Saved: {overfit_path}')
"""

T1_PACKAGE = """\
# ── Create Return Package ────────────────────────────────────────────────────
ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
zip_path = DRIVE_DIR / f'results_T1_v1_{ts}.zip'

files_to_include = [
    (DRIVE_DIR / 'no_attack_eval.csv', 'no_attack_eval.csv'),
    (DRIVE_DIR / 'overfit_history.json', 'overfit_history.json'),
    (Path('/tmp/overfit_plot.png'), 'overfit_plot.png'),
]

checksums = {}
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for src, arcname in files_to_include:
        if Path(src).exists():
            zf.write(src, arcname)
            checksums[arcname] = hashlib.sha256(Path(src).read_bytes()).hexdigest()
            print(f'  + {arcname}')
        else:
            print(f'  ⚠ Not found, skipping: {src}')

    manifest = {
        'task': 'T1', 'version': 'v1',
        'timestamp': ts,
        'files': [a for _, a in files_to_include],
        'checksums': checksums,
        'summary': {
            'gpu': gpu_info,
            'n_eval_images': N_EVAL_IMAGES,
            'n_overfit_images': N_OVERFIT_IMAGES,
            'overfit_epochs': OVERFIT_EPOCHS,
            'final_overfit_bit_acc': float(history['bit_acc'][-1]) if history['bit_acc'] else None,
        }
    }
    zf.writestr('manifest.json', json.dumps(manifest, indent=2))

print(f'\\nPackage saved: {zip_path}')
print('Return this file: place it in incoming/T1/')
"""

nb_t1 = nb_base()
nb_t1["cells"] = [
    md_cell(T1_HEADER),
    code_cell(T1_SETUP),
    code_cell(T1_BUNDLE),
    code_cell(T1_CHECKPOINTS),
    code_cell(T1_DATASETS),
    code_cell(T1_NO_ATTACK),
    code_cell(T1_OVERFIT),
    code_cell(T1_PACKAGE),
]
save_nb(nb_t1, "colab_T1_learned_diag_v1.ipynb")


# ==========================================================================
# T2: colab_T2_heldout500_v1.ipynb
# ==========================================================================
T2_HEADER = """\
# T2: Held-Out Benchmark — 500 Test Images × All Methods
**Purpose:** Run the full held-out benchmark on all 500 test images for all 6 methods
against SD VAE (6 sigma levels) and CompressAI (q=1–8), producing a ~42,000-row CSV.

**CHUNK_ID**: Split the work across 3 Colab sessions to stay within 90 min.
- `CHUNK_ID = 0` → SD VAE (6 sigma levels) — ~60 min
- `CHUNK_ID = 1` → CompressAI q=1–4 — ~60 min
- `CHUNK_ID = 2` → CompressAI q=5–8 — ~60 min

**Runtime:** GPU (T4). **Estimated time per chunk:** ~60 minutes.

**Inputs (on Drive):**
- `MyDrive/watermark_project/project_bundle_v2_<date>.zip`
- `MyDrive/watermark_project/checkpoints/` — optional learned checkpoints

**Outputs (appended to Drive CSV):**
- `MyDrive/watermark_project/T2_results_chunk<CHUNK_ID>.csv`
  Columns: `method, band, attack, strength, psnr_target, psnr_actual, image_id, bit_acc, detected, lpips, ssim`

**Return:** `results_T2_v1_<timestamp>.zip` → place in `incoming/T2/`

> Change `CHUNK_ID` at the top of Cell 2 before running.
"""

T2_SETUP = """\
import subprocess, sys, os, time, json, zipfile, hashlib, math
from pathlib import Path
from datetime import datetime

# ── Flags ────────────────────────────────────────────────────────────────────
CHUNK_ID  = 0        # <── CHANGE THIS: 0=SD_VAE, 1=CompressAI_q1-4, 2=CompressAI_q5-8
SMOKE     = False    # Set True for 3-image smoke test
WRITE_EVERY = 25     # Flush to Drive every N images
N_BITS    = 32
SECRET_KEY = 42
PSNR_TARGET = 40.0
# ─────────────────────────────────────────────────────────────────────────────

CHUNK_NAMES = {0: 'sd_vae', 1: 'compressai_q1-4', 2: 'compressai_q5-8'}
print(f'CHUNK_ID={CHUNK_ID} ({CHUNK_NAMES.get(CHUNK_ID, "unknown")})')
print(f'SMOKE={SMOKE}')

# Mount Drive
from google.colab import drive
drive.mount('/content/drive')
DRIVE_DIR = Path('/content/drive/MyDrive/watermark_project')
DRIVE_DIR.mkdir(parents=True, exist_ok=True)

# GPU check
result = subprocess.run(
    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
    capture_output=True, text=True
)
gpu_info = result.stdout.strip()
print('GPU:', gpu_info)

# Install deps
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
    'torch', 'torchvision', 'diffusers', 'transformers', 'accelerate',
    'compressai', 'lpips', 'scipy', 'scikit-image', 'pandas', 'tqdm'
], check=True)

import torch
import pandas as pd
import numpy as np
print('PyTorch:', torch.__version__, '| CUDA:', torch.cuda.is_available())
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
"""

T2_BUNDLE = """\
# ── Unzip Bundle ─────────────────────────────────────────────────────────────
REPO = Path('/content/repo')
REPO.mkdir(exist_ok=True)

bundle_zips = sorted(DRIVE_DIR.glob('project_bundle_v2_*.zip'))
if not bundle_zips:
    raise FileNotFoundError(f'No project_bundle_v2_*.zip in {DRIVE_DIR}')
bundle_zip = bundle_zips[-1]
print(f'Using bundle: {bundle_zip.name}')
with zipfile.ZipFile(bundle_zip, 'r') as zf:
    zf.extractall(REPO)
sys.path.insert(0, str(REPO))
print('Bundle extracted, sys.path[0]:', sys.path[0])

# ── Load Images ───────────────────────────────────────────────────────────────
import torchvision.transforms as T
from PIL import Image

TEST_DIR = REPO / 'data' / 'processed' / 'test'
transform = T.Compose([T.Resize((256, 256)), T.ToTensor()])

def load_images(d: Path, n: int):
    paths = sorted(list(d.glob('*.png')) + list(d.glob('*.jpg')))[:n]
    tensors, ids = [], []
    for p in paths:
        tensors.append(transform(Image.open(p).convert('RGB')))
        ids.append(p.stem)
    return torch.stack(tensors), ids

N_IMAGES = 3 if SMOKE else 500
print(f'Loading {N_IMAGES} test images...')
all_imgs, all_ids = load_images(TEST_DIR, N_IMAGES)
print(f'Loaded: {all_imgs.shape}')
"""

T2_ATTACKS = """\
# ── Define Attack Configs Per Chunk ──────────────────────────────────────────
from core.attacks import SDVAEAttack, CompressAIAttack, GaussianNoiseAttack

ATTACK_CONFIGS = {
    0: [  # SD VAE
        ('sd_vae', SDVAEAttack(device=device), [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]),
    ],
    1: [  # CompressAI q=1-4
        ('compressai', CompressAIAttack(quality=q, device=device), [q]) for q in range(1, 5)
    ],
    2: [  # CompressAI q=5-8
        ('compressai', CompressAIAttack(quality=q, device=device), [q]) for q in range(5, 9)
    ],
}

attack_list = ATTACK_CONFIGS[CHUNK_ID]
print(f'Attack configs for CHUNK_ID={CHUNK_ID}: {len(attack_list)} attack(s)')
for name, atk, strengths in attack_list:
    print(f'  {name}: strengths={strengths}')
"""

T2_METHODS = """\
# ── Define Watermarking Methods ───────────────────────────────────────────────
from track_b.watermark import ClassicalSpreadSpectrumWatermarker

methods = {}

# Classical Band 2 (primary)
methods['classical_ss_band2'] = {
    'type': 'classical', 'band_idx': 2,
    'wm': ClassicalSpreadSpectrumWatermarker(n_bits=N_BITS, secret_key=SECRET_KEY, device=device)
}
# Classical Band 0
methods['classical_ss_band0'] = {
    'type': 'classical', 'band_idx': 0,
    'wm': ClassicalSpreadSpectrumWatermarker(n_bits=N_BITS, secret_key=SECRET_KEY, device=device)
}
# Classical all 8 bands
for b in range(8):
    methods[f'classical_ss_bands_all_b{b}'] = {
        'type': 'classical', 'band_idx': b,
        'wm': ClassicalSpreadSpectrumWatermarker(n_bits=N_BITS, secret_key=SECRET_KEY, device=device)
    }

# Learned models (optional — load if checkpoints exist)
try:
    from track_c.model import WatermarkEncoder, WatermarkDecoder
    CHECKPOINT_DIR = DRIVE_DIR / 'checkpoints'
    LEARNED_CONFIGS = {
        'learned_control_low':  ('low',  CHECKPOINT_DIR / 'learned_control_low'  / 'latest_checkpoint.pt'),
        'learned_control_mid':  ('mid',  CHECKPOINT_DIR / 'learned_control_mid'  / 'latest_checkpoint.pt'),
        'learned_control_high': ('high', CHECKPOINT_DIR / 'learned_control_high' / 'latest_checkpoint.pt'),
        'learned_main_surrogate': (None, CHECKPOINT_DIR / 'main_stage1'          / 'latest_checkpoint.pt'),
    }
    for mname, (regime, ckpt_path) in LEARNED_CONFIGS.items():
        if ckpt_path.exists():
            enc = WatermarkEncoder(n_bits=N_BITS, fixed_regime=regime).to(device).eval()
            dec = WatermarkDecoder(n_bits=N_BITS).to(device).eval()
            ckpt = torch.load(ckpt_path, map_location=device)
            enc.load_state_dict(ckpt['encoder_state_dict'])
            dec.load_state_dict(ckpt['decoder_state_dict'])
            methods[mname] = {'type': 'learned', 'encoder': enc, 'decoder': dec}
            print(f'  ✓ Loaded learned method: {mname}')
        else:
            print(f'  ⚠ Checkpoint not found, skipping: {mname}')
except ImportError as e:
    print(f'  ⚠ Could not import learned models: {e}')

# Null check method (unwatermarked images through attack)
methods['null_check'] = {'type': 'null'}

print(f'\\nTotal methods: {len(methods)}')
for m in methods:
    print(f'  {m}')
"""

T2_METRICS = """\
# ── Metric Helpers ────────────────────────────────────────────────────────────
from skimage.metrics import structural_similarity as ssim_fn
from skimage.metrics import peak_signal_noise_ratio as psnr_fn
import numpy as np

try:
    import lpips as lpips_lib
    lpips_net = lpips_lib.LPIPS(net='alex').to(device)
    USE_LPIPS = True
    print('LPIPS: enabled')
except ImportError:
    USE_LPIPS = False
    print('LPIPS: not available')


def compute_psnr(orig: torch.Tensor, recon: torch.Tensor) -> float:
    orig_np = orig.squeeze(0).permute(1, 2, 0).cpu().numpy()
    recon_np = recon.squeeze(0).permute(1, 2, 0).cpu().numpy()
    return psnr_fn(orig_np, recon_np, data_range=1.0)


def compute_ssim(orig: torch.Tensor, recon: torch.Tensor) -> float:
    orig_np = orig.squeeze(0).permute(1, 2, 0).cpu().numpy()
    recon_np = recon.squeeze(0).permute(1, 2, 0).cpu().numpy()
    return float(ssim_fn(orig_np, recon_np, channel_axis=2, data_range=1.0))


def compute_lpips(orig: torch.Tensor, recon: torch.Tensor) -> float:
    if not USE_LPIPS:
        return float('nan')
    with torch.no_grad():
        return lpips_net(orig * 2 - 1, recon * 2 - 1).item()


def encode_image(method_cfg: dict, x: torch.Tensor, payload: torch.Tensor) -> torch.Tensor:
    if method_cfg['type'] == 'classical':
        return method_cfg['wm'].encode(x, payload, band_idx=method_cfg['band_idx'], psnr_db=PSNR_TARGET)
    elif method_cfg['type'] == 'learned':
        with torch.no_grad():
            return method_cfg['encoder'](x, payload.unsqueeze(0))
    elif method_cfg['type'] == 'null':
        return x.clone()
    return x.clone()


def decode_image(method_cfg: dict, x_attacked: torch.Tensor, payload: torch.Tensor) -> float:
    if method_cfg['type'] == 'classical':
        decoded = method_cfg['wm'].decode(x_attacked, band_idx=method_cfg['band_idx'])
        return (decoded.round() == payload.to(device)).float().mean().item()
    elif method_cfg['type'] == 'learned':
        with torch.no_grad():
            logits = method_cfg['decoder'](x_attacked)
            decoded = (torch.sigmoid(logits) > 0.5).float()
        return (decoded == payload.unsqueeze(0).to(device)).float().mean().item()
    elif method_cfg['type'] == 'null':
        # Random chance for null check
        return 0.5
    return 0.0
"""

T2_MAIN_LOOP = """\
# ── Main Evaluation Loop (Resumable) ─────────────────────────────────────────
from tqdm import tqdm

OUT_CSV = DRIVE_DIR / f'T2_results_chunk{CHUNK_ID}.csv'

# Load existing rows for resume
if OUT_CSV.exists():
    existing_df = pd.read_csv(OUT_CSV)
    done_keys = set(
        zip(existing_df['method'], existing_df['attack'],
            existing_df['strength'].astype(str), existing_df['image_id'])
    )
    print(f'Resuming: {len(existing_df)} rows already in {OUT_CSV.name}')
else:
    existing_df = pd.DataFrame()
    done_keys = set()
    print(f'Starting fresh: {OUT_CSV.name}')

COLUMNS = ['method', 'band', 'attack', 'strength', 'psnr_target',
           'psnr_actual', 'image_id', 'bit_acc', 'detected', 'lpips', 'ssim']

buffer_rows = []

def flush_buffer():
    global existing_df, buffer_rows
    if not buffer_rows:
        return
    new_df = pd.DataFrame(buffer_rows, columns=COLUMNS)
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined.to_csv(OUT_CSV, index=False)
    existing_df = combined
    print(f'  [flush] Wrote {len(combined)} rows to {OUT_CSV.name}')
    buffer_rows = []

# Fixed payload for all images (deterministic)
rng = np.random.default_rng(SECRET_KEY)
payload_np = rng.integers(0, 2, size=N_BITS)
payload = torch.tensor(payload_np, dtype=torch.float32).to(device)

t_start = time.time()

for atk_name, attack, strengths in attack_list:
    for strength in strengths:
        for img_idx, (img, img_id) in enumerate(zip(all_imgs, all_ids)):
            for method_name, method_cfg in methods.items():
                key = (method_name, atk_name, str(strength), img_id)
                if key in done_keys:
                    continue

                x = img.unsqueeze(0).to(device)

                # Encode
                try:
                    x_wm = encode_image(method_cfg, x, payload)
                except Exception as e:
                    print(f'  ✗ Encode error ({method_name}, {img_id}): {e}')
                    continue

                # Attack
                try:
                    x_attacked = attack(x_wm, strength)
                except Exception as e:
                    print(f'  ✗ Attack error ({atk_name}, {strength}): {e}')
                    continue

                # Decode
                try:
                    bit_acc = decode_image(method_cfg, x_attacked, payload)
                except Exception as e:
                    print(f'  ✗ Decode error ({method_name}): {e}')
                    bit_acc = float('nan')

                # Metrics
                psnr_actual = compute_psnr(x, x_wm)
                ssim_val = compute_ssim(x, x_attacked)
                lpips_val = compute_lpips(x.to(device), x_attacked.to(device))

                band = method_cfg.get('band_idx', -1)
                detected = int(bit_acc >= 0.75)

                row = [
                    method_name, band, atk_name, strength, PSNR_TARGET,
                    psnr_actual, img_id, bit_acc, detected, lpips_val, ssim_val
                ]
                buffer_rows.append(row)
                done_keys.add(key)

            # Flush every WRITE_EVERY images (per attack/strength)
            if (img_idx + 1) % WRITE_EVERY == 0:
                flush_buffer()
                elapsed = time.time() - t_start
                total_done = len(existing_df) + len(buffer_rows)
                print(f'  Progress: img {img_idx+1}/{len(all_ids)}, '
                      f'atk={atk_name}@{strength}, elapsed={elapsed:.0f}s, rows={total_done}')

# Final flush
flush_buffer()

print(f'\\n── Evaluation complete ──────────────────────────────────────────────')
print(f'Total rows in {OUT_CSV.name}: {len(existing_df)}')
print(f'Elapsed: {time.time() - t_start:.0f}s')
"""

T2_VALIDATE = """\
# ── Final Validation ─────────────────────────────────────────────────────────
df = pd.read_csv(OUT_CSV)
print(f'\\nRow count: {len(df)}')
print(f'Columns: {list(df.columns)}')
print(f'NaN counts:\\n{df.isna().sum()}')
print(f'\\nMethods: {df[\"method\"].unique().tolist()}')
print(f'Attacks: {df[\"attack\"].unique().tolist()}')
print(f'\\nBit accuracy summary:')
print(df.groupby(['method', 'attack'])['bit_acc'].agg(['mean', 'min', 'max']).to_string())

REQUIRED_COLS = ['method', 'band', 'attack', 'strength', 'psnr_target',
                 'psnr_actual', 'image_id', 'bit_acc', 'detected', 'lpips', 'ssim']
missing = [c for c in REQUIRED_COLS if c not in df.columns]
if missing:
    print(f'\\n✗ MISSING COLUMNS: {missing}')
else:
    print(f'\\n✓ All required columns present')
"""

T2_PACKAGE = """\
# ── Create Return Package ────────────────────────────────────────────────────
ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
zip_path = DRIVE_DIR / f'results_T2_v1_chunk{CHUNK_ID}_{ts}.zip'

df = pd.read_csv(OUT_CSV)
checksum = hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()
csv_arcname = f'results_chunk{CHUNK_ID}.csv'

with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(OUT_CSV, csv_arcname)
    manifest = {
        'task': 'T2', 'version': 'v1',
        'chunk_id': CHUNK_ID,
        'chunk_name': CHUNK_NAMES[CHUNK_ID],
        'timestamp': ts,
        'files': [csv_arcname],
        'checksums': {csv_arcname: checksum},
        'summary': {
            'gpu': gpu_info,
            'n_images': len(all_ids),
            'n_rows': len(df),
            'smoke': SMOKE,
        }
    }
    zf.writestr('manifest.json', json.dumps(manifest, indent=2))

print(f'\\nPackage saved: {zip_path}')
print(f'Row count: {len(df)}')
print('Return this file: place it in incoming/T2/')
"""

nb_t2 = nb_base()
nb_t2["cells"] = [
    md_cell(T2_HEADER),
    code_cell(T2_SETUP),
    code_cell(T2_BUNDLE),
    code_cell(T2_ATTACKS),
    code_cell(T2_METHODS),
    code_cell(T2_METRICS),
    code_cell(T2_MAIN_LOOP),
    code_cell(T2_VALIDATE),
    code_cell(T2_PACKAGE),
]
save_nb(nb_t2, "colab_T2_heldout500_v1.ipynb")

print("\\nAll notebooks written successfully.")
