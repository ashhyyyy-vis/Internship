"""
scripts/build_t2_notebook.py - Generates the canonical, clean, dependency-isolated
Colab notebook for Task 2 (Held-Out Benchmark on 500 Test Images).
"""

import json
from pathlib import Path

# Read core/sd_vae.py so we can embed it as a self-healing fallback in Cell 2
sd_vae_py_text = Path("core/sd_vae.py").read_text()

cell_0_md = """# T2: Held-Out Benchmark — 500 Test Images × All Methods
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

> Change `CHUNK_ID` at the top of Cell 1 before running."""

cell_1_code = """import subprocess, sys, os, time, json, zipfile, hashlib, math
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

# ── Clean Dependency Management ──────────────────────────────────────────────
# 1. Uninstall peft to prevent BloomPreTrainedModel / text-model import errors
subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'peft'], check=False)

# 2. Block peft in Python import cache so no lazy-loader ever queries it
sys.modules['peft'] = None

# 3. Install core packages without touching existing PyTorch / NumPy binaries
deps = ['safetensors', 'huggingface_hub>=0.25.0', 'scikit-image', 'tqdm']
if CHUNK_ID == 0:
    deps.extend(['diffusers>=0.30.0', 'accelerate>=0.28.0'])
elif CHUNK_ID in (1, 2):
    deps.append('compressai')

subprocess.run([sys.executable, '-m', 'pip', 'install', '-q'] + deps, check=True)

# 4. Alias deprecated cached_download in huggingface_hub to hf_hub_download
import huggingface_hub
if not hasattr(huggingface_hub, 'cached_download'):
    huggingface_hub.cached_download = huggingface_hub.hf_hub_download

import torch
import pandas as pd
import numpy as np
print('PyTorch:', torch.__version__, '| CUDA:', torch.cuda.is_available())
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Device:', device)"""

cell_2_code = f'''# ── Unzip Bundle ─────────────────────────────────────────────────────────────
REPO = Path('/content/repo')
REPO.mkdir(exist_ok=True)

bundle_zips = sorted(DRIVE_DIR.glob('project_bundle_v2_*.zip'))
if not bundle_zips:
    raise FileNotFoundError(f'No project_bundle_v2_*.zip in {{DRIVE_DIR}}')
bundle_zip = bundle_zips[-1]
print(f'Using bundle: {{bundle_zip.name}}')
with zipfile.ZipFile(bundle_zip, 'r') as zf:
    zf.extractall(REPO)
sys.path.insert(0, str(REPO))
print('Bundle extracted, sys.path[0]:', sys.path[0])

# Ensure core/sd_vae.py exists in repo (self-healing for older bundle zips)
sd_vae_file = REPO / 'core' / 'sd_vae.py'
if not sd_vae_file.exists():
    sd_vae_file.parent.mkdir(parents=True, exist_ok=True)
    sd_vae_file.write_text({repr(sd_vae_py_text)})
    print('✓ Embedded core/sd_vae.py fallback into repo')

# ── Load Images ───────────────────────────────────────────────────────────────
import torchvision.transforms as T
from PIL import Image

TEST_DIR = REPO / 'data' / 'processed' / 'test'
transform = T.Compose([T.Resize((256, 256)), T.ToTensor()])

def load_images(d: Path, n: int):
    imgs, ids = [], []
    for p in sorted(d.glob('*.png'))[:n]:
        img = Image.open(p).convert('RGB')
        imgs.append(transform(img))
        ids.append(p.stem)
    return imgs, ids

n_eval = 3 if SMOKE else 500
all_imgs, all_ids = load_images(TEST_DIR, n_eval)
print(f'Loaded {{len(all_imgs)}} test images (SMOKE={{SMOKE}})')
assert len(all_imgs) > 0, 'No images loaded!'
print(f'Image shape: {{all_imgs[0].shape}}, range: [{{all_imgs[0].min():.2f}}, {{all_imgs[0].max():.2f}}]')'''

cell_3_code = """# ── Define Attack Configs Per Chunk ──────────────────────────────────────────
from core.attacks import get_attack_family, StableDiffusionVAEAttack

# Ensure StableDiffusionVAEAttack has dual-mode robust loader
def robust_get_vae(self):
    if self._vae is not None:
        return self._vae
    try:
        from diffusers import AutoencoderKL
        vae = AutoencoderKL.from_pretrained(self.model_id)
        vae.eval().to(self.device)
        for p in vae.parameters():
            p.requires_grad = False
        self._vae = vae
        print(f'✓ Loaded {self.model_id} via diffusers')
        return self._vae
    except Exception as err:
        print(f'Diffusers load failed ({err}), falling back to direct pure PyTorch AutoencoderKL...')
    from core.sd_vae import load_sd_vae
    self._vae = load_sd_vae(self.model_id, device=self.device)
    return self._vae

StableDiffusionVAEAttack.get_vae = robust_get_vae

sd_vae_attack = get_attack_family('sd_vae')
compressai_attack = get_attack_family('compressai')

ATTACK_CONFIGS = {
    0: [  # SD VAE (all 6 noise strengths)
        ('sd_vae', sd_vae_attack, [0.0, 0.02, 0.05, 0.1, 0.15, 0.2]),
    ],
    1: [  # CompressAI q=1-4
        ('compressai_bmshj2018', compressai_attack, [1, 2, 3, 4]),
    ],
    2: [  # CompressAI q=5-8
        ('compressai_bmshj2018', compressai_attack, [5, 6, 7, 8]),
    ],
}

attack_list = ATTACK_CONFIGS[CHUNK_ID]
print(f'Attack configs for CHUNK_ID={CHUNK_ID}: {len(attack_list)} attack family')
for name, atk, strengths in attack_list:
    print(f'  {name}: strengths={strengths}')

# Immediate Model Health Check (Verify loading BEFORE entering main loop)
print('\\nVerifying model loading...')
if CHUNK_ID == 0:
    vae = sd_vae_attack.get_vae()
    dummy_x = torch.zeros(1, 3, 256, 256, device=device)
    with torch.no_grad():
        dummy_out = sd_vae_attack(dummy_x, strength=0.0)
    assert dummy_out.shape == dummy_x.shape
    print(f'✓ SD VAE verified and ready on {device} (output shape: {tuple(dummy_out.shape)})')
elif CHUNK_ID in (1, 2):
    m = compressai_attack.get_model(quality=attack_list[0][2][0])
    dummy_x = torch.zeros(1, 3, 256, 256, device=device)
    with torch.no_grad():
        dummy_out = compressai_attack(dummy_x, strength=attack_list[0][2][0])
    assert dummy_out.shape == dummy_x.shape
    print(f'✓ CompressAI model verified and ready on {device} (output shape: {tuple(dummy_out.shape)})')"""

cell_4_code = """# ── Define Watermarking Methods ───────────────────────────────────────────────
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

print(f'\\nTotal methods configured: {len(methods)}')
for m in methods:
    print(f'  {m}')"""

cell_5_code = """# ── Metric Helpers ────────────────────────────────────────────────────────────
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
        return method_cfg['wm'].embed(x, payload.unsqueeze(0), band_idx=method_cfg['band_idx'], psnr_db=PSNR_TARGET, round_8bit=True)
    elif method_cfg['type'] == 'learned':
        with torch.no_grad():
            x_w, _ = method_cfg['encoder'](x, payload.unsqueeze(0))
            return x_w
    elif method_cfg['type'] == 'null':
        return x.clone()
    return x.clone()


def decode_image(method_cfg: dict, x_attacked: torch.Tensor, payload: torch.Tensor) -> float:
    if method_cfg['type'] == 'classical':
        hard_bits, _ = method_cfg['wm'].decode(x_attacked, band_idx=method_cfg['band_idx'])
        return (hard_bits.squeeze(0).float() == payload.to(device)).float().mean().item()
    elif method_cfg['type'] == 'learned':
        with torch.no_grad():
            logits = method_cfg['decoder'](x_attacked)
            decoded = (logits > 0.0).float()
        return (decoded.squeeze(0) == payload.to(device)).float().mean().item()
    elif method_cfg['type'] == 'null':
        return 0.5
    return 0.0"""

cell_6_code = """# ── Main Evaluation Loop (Resumable) ─────────────────────────────────────────
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
print(f'Elapsed: {time.time() - t_start:.0f}s')"""

cell_7_code = """# ── Final Validation ─────────────────────────────────────────────────────────
df = pd.read_csv(OUT_CSV)
print(f'\\nRow count: {len(df)}')
print(f'Columns: {list(df.columns)}')
print(f'NaN counts:\\n{df.isna().sum()}')
print(f'\\nMethods: {df["method"].unique().tolist()}')
print(f'Attacks: {df["attack"].unique().tolist()}')
print(f'\\nBit accuracy summary:')
print(df.groupby(['method', 'attack'])['bit_acc'].agg(['mean', 'min', 'max']).to_string())

REQUIRED_COLS = ['method', 'band', 'attack', 'strength', 'psnr_target',
                 'psnr_actual', 'image_id', 'bit_acc', 'detected', 'lpips', 'ssim']
missing = [c for c in REQUIRED_COLS if c not in df.columns]
if missing:
    print(f'\\n✗ MISSING COLUMNS: {missing}')
else:
    print(f'\\n✓ All required columns present')"""

cell_8_code = """# ── Create Return Package ────────────────────────────────────────────────────
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
print('Return this file: place it in incoming/T2/')"""


def make_cell(ctype, src):
    lines = [l + '\n' for l in src.split('\n')]
    if lines and lines[-1] == '\n':
        lines[-1] = ''
    return {
        'cell_type': ctype,
        'metadata': {},
        'source': lines,
        **({'outputs': [], 'execution_count': None} if ctype == 'code' else {})
    }


def build():
    nb = {
        'nbformat': 4,
        'nbformat_minor': 0,
        'metadata': {
            'accelerator': 'GPU',
            'colab': {'provenance': []},
            'language_info': {'name': 'python'}
        },
        'cells': [
            make_cell('markdown', cell_0_md),
            make_cell('code', cell_1_code),
            make_cell('code', cell_2_code),
            make_cell('code', cell_3_code),
            make_cell('code', cell_4_code),
            make_cell('code', cell_5_code),
            make_cell('code', cell_6_code),
            make_cell('code', cell_7_code),
            make_cell('code', cell_8_code),
        ]
    }

    targets = [
        'notebooks/colab_T2_heldout500_v1.ipynb',
    ]
    for target in targets:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w') as f:
            json.dump(nb, f, indent=1)
        print(f'Successfully built: {target}')

if __name__ == '__main__':
    build()
