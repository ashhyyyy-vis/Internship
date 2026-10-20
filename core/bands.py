"""
core/bands.py - Frequency Band Partitioning and Annular Masks.

Implements Section 0.2:
- 8 disjoint annuli over [0, 0.5] cycles per pixel (linear spacing: width = 0.0625)
- Annular boolean/float masks on centered (fftshift) or unshifted Fourier grids
"""

from typing import Tuple, List, Optional
import torch
import numpy as np
from core.radial import frequency_grid


def band_edges(n_bands: int = 8, r_max: float = 0.5) -> torch.Tensor:
    """
    Return the 1D boundary edges of the disjoint frequency bands over [0, r_max].
    Default: 8 linear bands -> 9 edges: [0.0, 0.0625, 0.125, ..., 0.5]
    """
    return torch.linspace(0.0, r_max, n_bands + 1)


def band_centers(n_bands: int = 8, r_max: float = 0.5) -> torch.Tensor:
    """
    Return midpoints of each of the n_bands disjoint frequency bands.
    """
    edges = band_edges(n_bands, r_max)
    return 0.5 * (edges[:-1] + edges[1:])


def band_masks(
    h: int,
    w: int,
    n_bands: int = 8,
    r_max: float = 0.5,
    shifted: bool = True,
    device: Optional[torch.device] = None,
    dtype: torch.dtype = torch.float32
) -> torch.Tensor:
    """
    Generate n_bands disjoint annular masks covering radius [0, r_max].
    
    Args:
        h, w: Spatial height and width of the 2D image
        n_bands: Number of disjoint annuli (default 8)
        r_max: Maximum radius in cycles per pixel (default 0.5)
        shifted: If True, masks align with centered fftshift spectrum.
                 If False, masks are ifftshifted to directly multiply unshifted fft2 outputs.
        device: PyTorch device
        dtype: Output tensor dtype (default torch.float32)
        
    Returns:
        masks: Tensor of shape (n_bands, h, w) with values in {0, 1}
               Guaranteed disjoint: sum along dim=0 <= 1 everywhere.
    """
    _, _, r = frequency_grid(h, w, device=device)
    edges = band_edges(n_bands, r_max).to(device=device)
    
    masks = []
    for b in range(n_bands):
        r_low = edges[b]
        r_high = edges[b + 1]
        if b == n_bands - 1:
            # Include upper boundary on the last band
            mask_b = (r >= r_low) & (r <= r_high)
        else:
            mask_b = (r >= r_low) & (r < r_high)
            
        mask_tensor = mask_b.to(dtype=dtype)
        if not shifted:
            # Shift back to standard FFT origin at (0, 0)
            mask_tensor = torch.fft.ifftshift(mask_tensor)
        masks.append(mask_tensor)
        
    return torch.stack(masks, dim=0)


def band_masks_numpy(
    h: int,
    w: int,
    n_bands: int = 8,
    r_max: float = 0.5,
    shifted: bool = True
) -> np.ndarray:
    """
    NumPy implementation of band_masks.
    Returns: np.ndarray of shape (n_bands, h, w)
    """
    fy = np.fft.fftshift(np.fft.fftfreq(h))
    fx = np.fft.fftshift(np.fft.fftfreq(w))
    gy, gx = np.meshgrid(fy, fx, indexing="ij")
    r = np.sqrt(gx**2 + gy**2)
    
    edges = np.linspace(0.0, r_max, n_bands + 1)
    masks = []
    for b in range(n_bands):
        r_low = edges[b]
        r_high = edges[b + 1]
        if b == n_bands - 1:
            m = (r >= r_low) & (r <= r_high)
        else:
            m = (r >= r_low) & (r < r_high)
            
        m_float = m.astype(np.float32)
        if not shifted:
            m_float = np.fft.ifftshift(m_float)
        masks.append(m_float)
        
    return np.stack(masks, axis=0)
