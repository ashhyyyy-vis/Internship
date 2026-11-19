import sys, os
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim_fn

# Add project root to sys.path
sys.path.insert(0, '/home/viseash/Ashley/Work/Internship')
from track_b.watermark import ClassicalSpreadSpectrumWatermarker

# Test for lpips package
have_lpips = False
try:
    import lpips
    loss_fn_alex = lpips.LPIPS(net='alex')
    loss_fn_alex.eval()
    have_lpips = True
    print("LPIPS package found and AlexNet loaded.")
except Exception as e:
    print(f"LPIPS not available or failed to load: {e}. Skipping LPIPS.")

test_dir = Path('data/processed/test')
img_files = sorted(list(test_dir.glob('*.png')))[:20]
if not img_files:
    img_files = sorted(list(test_dir.glob('*.jpg')))[:20]

print(f"Found {len(img_files)} test images for perceptual evaluation.")

wm = ClassicalSpreadSpectrumWatermarker(n_bits=32, secret_key=42)

results = []

for band in range(8):
    ssims = []
    lpipss = []
    psnrs = []
    
    for idx, f in enumerate(img_files):
        pil_img = Image.open(f).convert('RGB')
        x_np = np.array(pil_img, dtype=np.float32) / 255.0
        x_tensor = torch.from_numpy(x_np).permute(2, 0, 1).unsqueeze(0)
        
        # Fixed deterministic message for consistency
        torch.manual_seed(idx)
        msg = torch.randint(0, 2, (1, 32), dtype=torch.long)
        
        x_w_tensor = wm.embed(x_tensor, msg.float(), band_idx=band, psnr_db=40.0, round_8bit=True)
        
        # Calculate actual PSNR
        diff = (x_w_tensor - x_tensor).squeeze(0).numpy()
        mse = np.mean(diff ** 2)
        psnr = 10.0 * np.log10(1.0 / (mse + 1e-12))
        psnrs.append(psnr)
        
        x_w_np = x_w_tensor.squeeze(0).permute(1, 2, 0).numpy()
        
        # SSIM
        s = ssim_fn(x_np, x_w_np, channel_axis=2, data_range=1.0)
        ssims.append(s)
        
        # LPIPS
        if have_lpips:
            # lpips expects inputs normalized to [-1, 1]
            x_in = x_tensor * 2.0 - 1.0
            xw_in = x_w_tensor * 2.0 - 1.0
            with torch.no_grad():
                d = loss_fn_alex(x_in, xw_in).item()
            lpipss.append(d)
        else:
            lpipss.append(np.nan)
            
    center_freq = 0.5 * (band * 0.0625 + (band + 1) * 0.0625)
    mean_psnr = float(np.mean(psnrs))
    mean_ssim = float(np.mean(ssims))
    mean_lpips = float(np.mean(lpipss)) if have_lpips else np.nan
    
    results.append({
        'band': band,
        'band_center_freq': center_freq,
        'psnr_actual': mean_psnr,
        'ssim': mean_ssim,
        'lpips': mean_lpips
    })
    print(f"Band {band} (f={center_freq:.4f}): PSNR={mean_psnr:.2f}dB, SSIM={mean_ssim:.4f}, LPIPS={mean_lpips:.4f}")

df = pd.DataFrame(results)
df.to_csv('results/v2/perceptual_metrics.csv', index=False)
print("Saved results/v2/perceptual_metrics.csv")

# Plot SSIM and LPIPS per band
fig, ax1 = plt.subplots(figsize=(8, 5))
bands = df['band']
color = 'tab:blue'
ax1.set_xlabel('Band Index')
ax1.set_ylabel('SSIM', color=color)
bars1 = ax1.bar(bands - 0.2, df['ssim'], width=0.4, color=color, label='SSIM')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_ylim(0.95, 1.0)

if have_lpips:
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('LPIPS (lower is better)', color=color)
    bars2 = ax2.bar(bands + 0.2, df['lpips'], width=0.4, color=color, label='LPIPS')
    ax2.tick_params(axis='y', labelcolor=color)

plt.title('Perceptual Quality (SSIM & LPIPS) across Frequency Bands at PSNR=40dB')
fig.tight_layout()
plt.savefig('figures/v2/fig_perceptual_per_band.png', dpi=300)
print("Saved figures/v2/fig_perceptual_per_band.png")

# Save example images for bands 0, 2, 7
sample_img_path = img_files[0]
sample_pil = Image.open(sample_img_path).convert('RGB')
x_np = np.array(sample_pil, dtype=np.float32) / 255.0
x_tensor = torch.from_numpy(x_np).permute(2, 0, 1).unsqueeze(0)
msg = torch.randint(0, 2, (1, 32), dtype=torch.long)

for b in [0, 2, 7]:
    xw_tensor = wm.embed(x_tensor, msg.float(), band_idx=b, psnr_db=40.0, round_8bit=True)
    xw_np = xw_tensor.squeeze(0).permute(1, 2, 0).numpy()
    res = (xw_np - x_np) * 10.0 + 0.5
    res = np.clip(res, 0.0, 1.0)
    
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(x_np)
    axes[0].set_title("Original")
    axes[0].axis('off')
    
    axes[1].imshow(xw_np)
    axes[1].set_title(f"Watermarked (Band {b})")
    axes[1].axis('off')
    
    axes[2].imshow(res)
    axes[2].set_title(f"Residual 10x Amp (Band {b})")
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.savefig(f'figures/v2/example_band{b}.png', dpi=300)
    plt.close()
    print(f"Saved figures/v2/example_band{b}.png")

