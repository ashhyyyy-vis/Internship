"""
core/probes.py - Frequency Annular Probes for Spectral Transfer Function Measurement.

Implements Section 0.3:
- White Gaussian noise filtered to a single disjoint frequency annulus
- Unit RMS normalization: RMS = sqrt(mean(p^2)) == 1
- Target PSNR scaling: a = 255 * 10^(-PSNR / 20) (or 10^(-PSNR/20) for [0, 1] range)
- 8-bit rounding test ensuring measured PSNR matches target within 0.1 dB
- Spectral isolation test verifying probe energy is confined to the annulus
"""

from typing import Tuple, Optional, Union
import math
import torch
import numpy as np
from core.bands import band_masks


def compute_mse(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Compute Mean Squared Error across all elements."""
    return torch.mean((x - y) ** 2)


def compute_psnr(
    x: torch.Tensor,
    y: torch.Tensor,
    max_val: float = 1.0
) -> float:
    """
    Compute Peak Signal-to-Noise Ratio (PSNR) in decibels (dB).
    PSNR = 10 * log10(max_val^2 / MSE) = 20 * log10(max_val / RMSE)
    """
    mse = compute_mse(x, y).item()
    if mse <= 1e-15:
        return float("inf")
    return 10.0 * math.log10((max_val ** 2) / mse)


def generate_band_probe(
    h: int,
    w: int,
    band_idx: int,
    n_bands: int = 8,
    r_max: float = 0.5,
    seed: Optional[int] = None,
    device: Optional[torch.device] = None,
    dtype: torch.dtype = torch.float32
) -> torch.Tensor:
    """
    Synthesize a single-band annular probe with unit RMS.
    
    1. Sample white Gaussian noise w ~ N(0, 1)
    2. Compute orthonormal 2D FFT: W = fftshift(fft2(w, norm='ortho'))
    3. Filter by annular band mask M_b
    4. Inverse FFT: p = ifft2(ifftshift(W * M_b), norm='ortho').real
    5. Normalize to exact unit RMS: p / sqrt(mean(p^2))
    
    Returns:
        probe: Tensor of shape (h, w) with unit RMS.
    """
    if seed is not None:
        generator = torch.Generator(device=device if device and device.type != 'mps' else 'cpu').manual_seed(seed)
    else:
        generator = None
        
    noise = torch.randn(h, w, generator=generator, device=device, dtype=dtype)
    
    # Orthonormal FFT
    w_fft = torch.fft.fftshift(torch.fft.fft2(noise, norm="ortho"))
    
    # Disjoint annular mask (centered)
    masks = band_masks(h, w, n_bands=n_bands, r_max=r_max, shifted=True, device=device, dtype=dtype)
    mask = masks[band_idx]
    
    w_filtered = w_fft * mask
    
    # Inverse orthonormal FFT
    probe = torch.fft.ifft2(torch.fft.ifftshift(w_filtered), norm="ortho").real
    
    # Normalize to unit RMS
    rms = torch.sqrt(torch.mean(probe ** 2))
    if rms > 1e-10:
        probe = probe / rms
    else:
        probe = torch.zeros_like(probe)
        
    return probe


def round_to_8bit(x: torch.Tensor) -> torch.Tensor:
    """Simulate 8-bit image quantization in [0, 1] range."""
    return torch.clamp(torch.round(x * 255.0) / 255.0, 0.0, 1.0)


def embed_probe(
    x: torch.Tensor,
    band_idx: int,
    psnr_db: float,
    n_bands: int = 8,
    r_max: float = 0.5,
    seed: Optional[int] = None,
    round_8bit: bool = True
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Embed an annular probe into an image tensor x at a specified target PSNR.
    
    Args:
        x: Image tensor of shape (..., 3, H, W) or (..., 1, H, W) with values in [0, 1]
        band_idx: Index of the target frequency annulus [0, n_bands-1]
        psnr_db: Desired PSNR in dB (e.g. 35, 40, 45)
        seed: Random seed for probe generation
        round_8bit: Whether to simulate 8-bit quantization after addition
        
    Returns:
        x_w: Watermarked/probed image tensor
        probe_scaled: The exact added probe tensor (unquantized)
    """
    h, w = x.shape[-2], x.shape[-1]
    probe_unit = generate_band_probe(
        h, w, band_idx=band_idx, n_bands=n_bands, r_max=r_max, seed=seed, device=x.device, dtype=x.dtype
    )
    
    # Scale amplitude to target PSNR on [0, 1] scale:
    # PSNR = 20 * log10(1 / amplitude) -> amplitude = 10^(-PSNR / 20)
    amplitude = 10.0 ** (-psnr_db / 20.0)
    probe_scaled = probe_unit * amplitude
    
    # Broadcast across channel dimensions (luminance addition)
    if x.dim() >= 3 and x.shape[-3] in (1, 3):
        probe_expanded = probe_scaled.unsqueeze(-3)
    else:
        probe_expanded = probe_scaled
        
    x_w = x + probe_expanded
    
    if round_8bit:
        x_w = round_to_8bit(x_w)
    else:
        x_w = torch.clamp(x_w, 0.0, 1.0)
        
    return x_w, probe_scaled
