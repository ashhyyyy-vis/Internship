"""
core/radial.py - Orthonormal 2D FFT and Radial Spectrum Profile Utilities.

Implements the radial frequency analysis specified in Section 0.2:
- Luminance conversion (Y channel via BT.601)
- 2D FFT with norm='ortho' followed by fftshift
- Radial distance grid r = sqrt(fx^2 + fy^2) in cycles/pixel [0, 0.5]
- 32 equal-width radial profile bins over [0, 0.5]
"""

from typing import Union, Tuple, Optional
import numpy as np
import torch


def rgb_to_luminance(x: Union[np.ndarray, torch.Tensor]) -> Union[np.ndarray, torch.Tensor]:
    """
    Extract luminance channel Y using ITU-R BT.601 weights:
    Y = 0.299 * R + 0.587 * G + 0.114 * B
    
    Accepts:
        - PyTorch tensor of shape (..., 3, H, W)
        - NumPy array of shape (..., 3, H, W) or (..., H, W, 3)
    """
    if isinstance(x, torch.Tensor):
        if x.dim() >= 3 and x.shape[-3] == 3:
            # (..., 3, H, W)
            weights = torch.tensor([0.299, 0.587, 0.114], dtype=x.dtype, device=x.device).view(1, 3, 1, 1)
            # Match batch dimensions
            while weights.dim() < x.dim():
                weights = weights.unsqueeze(0)
            return (x * weights).sum(dim=-3, keepdim=False)
        elif x.shape[-1] == 3:
            # (..., H, W, 3)
            weights = torch.tensor([0.299, 0.587, 0.114], dtype=x.dtype, device=x.device)
            return (x * weights).sum(dim=-1)
        else:
            raise ValueError(f"Expected 3 channels in tensor with shape {x.shape}")
    else:
        # NumPy array
        x = np.asarray(x)
        if x.ndim >= 3 and x.shape[-3] == 3:
            return 0.299 * x[..., 0, :, :] + 0.587 * x[..., 1, :, :] + 0.114 * x[..., 2, :, :]
        elif x.shape[-1] == 3:
            return 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]
        else:
            raise ValueError(f"Expected 3 channels in array with shape {x.shape}")


def frequency_grid(h: int, w: int, device: Optional[torch.device] = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Build 2D frequency grid centered via fftshift in cycles per pixel.
    fx, fy each in [-0.5, 0.5).
    r = sqrt(fx^2 + fy^2) with center DC at r = 0.
    
    Returns:
        fx: (h, w)
        fy: (h, w)
        r:  (h, w)
    """
    fy = torch.fft.fftshift(torch.fft.fftfreq(h, d=1.0, device=device))
    fx = torch.fft.fftshift(torch.fft.fftfreq(w, d=1.0, device=device))
    grid_y, grid_x = torch.meshgrid(fy, fx, indexing="ij")
    r = torch.sqrt(grid_x**2 + grid_y**2)
    return grid_x, grid_y, r


def compute_power2d(x: torch.Tensor) -> torch.Tensor:
    """
    Compute 2D centered orthonormal power spectrum:
    P = |fftshift(fft2(x, norm='ortho'))|^2
    
    x: shape (H, W) or (B, H, W) float tensor
    Returns: power tensor of same shape
    """
    if not torch.is_floating_point(x):
        x = x.float()
    f = torch.fft.fftshift(torch.fft.fft2(x, norm="ortho"), dim=(-2, -1))
    power = f.real**2 + f.imag**2
    return power


def radial_profile(
    power2d: Union[torch.Tensor, np.ndarray],
    n_bins: int = 32,
    r_max: float = 0.5
) -> Union[torch.Tensor, np.ndarray]:
    """
    Compute the mean power inside each of n_bins equal-width radius bins from 0 to r_max.
    
    Args:
        power2d: 2D centered power spectrum tensor/array of shape (..., H, W)
        n_bins: Number of radial bins (default 32)
        r_max: Maximum radius in cycles per pixel (default 0.5)
        
    Returns:
        radial_means: shape (..., n_bins)
    """
    is_torch = isinstance(power2d, torch.Tensor)
    if is_torch:
        *batch_dims, h, w = power2d.shape
        _, _, r = frequency_grid(h, w, device=power2d.device)
        r_flat = r.flatten()
        
        # Flatten batch dimensions for uniform processing
        power_flat = power2d.reshape(-1, h * w)
        bin_edges = torch.linspace(0.0, r_max, n_bins + 1, device=power2d.device)
        bin_width = r_max / n_bins
        
        # Digitize r: indices from 0 to n_bins-1 for r in [0, r_max)
        # Using bucketize: bins are [bin_edges[k], bin_edges[k+1])
        bin_idx = torch.bucketize(r_flat, bin_edges, right=False) - 1
        
        results = []
        for k in range(n_bins):
            mask = (bin_idx == k)
            if mask.any():
                mean_k = power_flat[:, mask].mean(dim=-1)
            else:
                mean_k = torch.zeros(power_flat.shape[0], device=power2d.device)
            results.append(mean_k)
            
        profile = torch.stack(results, dim=-1)
        if len(batch_dims) > 0:
            return profile.reshape(*batch_dims, n_bins)
        return profile.squeeze(0)
    else:
        # NumPy fallback
        arr = np.asarray(power2d)
        *batch_dims, h, w = arr.shape
        fy = np.fft.fftshift(np.fft.fftfreq(h))
        fx = np.fft.fftshift(np.fft.fftfreq(w))
        gy, gx = np.meshgrid(fy, fx, indexing="ij")
        r = np.sqrt(gx**2 + gy**2)
        
        r_flat = r.flatten()
        arr_flat = arr.reshape(-1, h * w)
        bin_edges = np.linspace(0.0, r_max, n_bins + 1)
        bin_idx = np.digitize(r_flat, bin_edges) - 1
        
        results = []
        for k in range(n_bins):
            mask = (bin_idx == k)
            if np.any(mask):
                mean_k = arr_flat[:, mask].mean(axis=-1)
            else:
                mean_k = np.zeros(arr_flat.shape[0])
            results.append(mean_k)
            
        profile = np.stack(results, axis=-1)
        if len(batch_dims) > 0:
            return profile.reshape(*batch_dims, n_bins)
        return profile.squeeze(0)
