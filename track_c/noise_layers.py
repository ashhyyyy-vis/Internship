"""
track_c/noise_layers.py - Modular Differentiable Noise Layers and Spectral-Transfer Surrogate.

Implements Section 8 (C3):
- Differentiable training distortion operators sampled per batch:
  1. Identity
  2. Gaussian Noise (differentiable reparameterization)
  3. Gaussian Blur (differentiable spatial conv)
  4. Spectral-Transfer Surrogate (Merge 1):
     Loads fitted-G JSON, constructs Fourier filter G(f) = P(f) / (P(f) + N_eff),
     and filters the watermark residual:
     x_att = x + ifft2(G * fft2(x_w - x))
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from core.radial import frequency_grid


class DifferentiableGaussianNoise(nn.Module):
    def __init__(self, min_sigma: float = 0.01, max_sigma: float = 0.1):
        super().__init__()
        self.min_sigma = min_sigma
        self.max_sigma = max_sigma

    def forward(self, x_w: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        sigma = torch.empty(1, device=x_w.device).uniform_(self.min_sigma, self.max_sigma).item()
        noise = torch.randn_like(x_w) * sigma
        return torch.clamp(x_w + noise, 0.0, 1.0)


class DifferentiableGaussianBlur(nn.Module):
    def __init__(self, min_sigma: float = 0.5, max_sigma: float = 2.0):
        super().__init__()
        self.min_sigma = min_sigma
        self.max_sigma = max_sigma

    def forward(self, x_w: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        sigma = torch.empty(1, device=x_w.device).uniform_(self.min_sigma, self.max_sigma).item()
        kernel_size = int(math.ceil(sigma * 4)) // 2 * 2 + 1
        radius = kernel_size // 2
        coords = torch.arange(-radius, radius + 1, device=x_w.device, dtype=x_w.dtype)
        k1d = torch.exp(-0.5 * (coords / sigma) ** 2)
        k1d = k1d / k1d.sum()
        k2d = torch.outer(k1d, k1d)
        kernel = k2d.view(1, 1, kernel_size, kernel_size).repeat(x_w.shape[1], 1, 1, 1)

        pad = radius
        padded = F.pad(x_w, (pad, pad, pad, pad), mode="reflect")
        blurred = F.conv2d(padded, kernel, groups=x_w.shape[1])
        return torch.clamp(blurred, 0.0, 1.0)


class SpectralTransferSurrogate(nn.Module):
    """
    Analytical Wiener Spectral-Transfer Surrogate (Merge 1).
    Loads fitted-G parameters (A, alpha, N_eff) and filters the watermark residual:
    x_att = x + ifft2(G * fft2(x_w - x))
    """

    def __init__(self, fitted_g_json_path: Optional[str] = None):
        super().__init__()
        self.fitted_g_json_path = fitted_g_json_path
        self.enabled = False
        self.alpha = 2.0
        self.A = 1.0
        self.n_eff_list: List[float] = []

        if fitted_g_json_path and Path(fitted_g_json_path).exists():
            self.load_parameters(fitted_g_json_path)

    def load_parameters(self, path: str):
        with open(path, "r") as f:
            data = json.load(f)
        self.alpha = float(data.get("dataset_alpha", 2.0))
        self.A = float(math.exp(data.get("dataset_log_A", 0.0)))

        # Gather all fitted N_eff across all strengths
        n_effs = []
        for att_name, strengths in data.get("attacks", {}).items():
            for s, s_data in strengths.items():
                if "N_eff" in s_data:
                    n_effs.append(float(s_data["N_eff"]))

        if len(n_effs) > 0:
            self.n_eff_list = n_effs
            self.enabled = True
            print(f"[Surrogate] Loaded {len(n_effs)} N_eff values from {path}. Surrogate active!")

    def forward(self, x_w: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        if not self.enabled or len(self.n_eff_list) == 0:
            # Until Merge 1: identity passthrough
            return x_w

        b, c, h, w = x_w.shape
        residual = x_w - x  # (B, C, H, W)

        # Sample random N_eff from fitted distribution
        idx = torch.randint(0, len(self.n_eff_list), (1,)).item()
        n_eff = self.n_eff_list[idx]

        # 2D Frequency grid
        _, _, r = frequency_grid(h, w, device=x_w.device)
        # Avoid division by zero at DC
        r_safe = torch.clamp(r, min=1.0 / max(h, w))
        P_f = self.A * (r_safe ** (-self.alpha))
        G_grid = P_f / (P_f + n_eff)  # (H, W) in [0, 1]

        # Unshifted G for direct elementwise multiplication with fft2
        G_unshifted = torch.fft.ifftshift(G_grid).view(1, 1, h, w)

        # Filter watermark residual
        res_fft = torch.fft.fft2(residual, norm="ortho")
        filtered_fft = res_fft * G_unshifted
        filtered_res = torch.fft.ifft2(filtered_fft, norm="ortho").real

        # Linearized model: cover untouched + filtered watermark
        x_att = torch.clamp(x + filtered_res, 0.0, 1.0)
        return x_att


class NoiseMixtureLayer(nn.Module):
    """Samples one distortion per batch according to training curriculum."""

    def __init__(self, fitted_g_json_path: Optional[str] = None):
        super().__init__()
        self.gaussian = DifferentiableGaussianNoise()
        self.blur = DifferentiableGaussianBlur()
        self.surrogate = SpectralTransferSurrogate(fitted_g_json_path)

    def forward(
        self,
        x_w: torch.Tensor,
        x: torch.Tensor,
        mode: str = "mixture"
    ) -> torch.Tensor:
        """
        mode: 'identity', 'gaussian', 'blur', 'surrogate', 'mixture'
        """
        if mode == "identity":
            return x_w
        elif mode == "gaussian":
            return self.gaussian(x_w, x)
        elif mode == "blur":
            return self.blur(x_w, x)
        elif mode == "surrogate":
            return self.surrogate(x_w, x)
        elif mode == "mixture":
            choices = ["identity", "gaussian", "blur"]
            if self.surrogate.enabled:
                choices.append("surrogate")
            sampled_mode = choices[torch.randint(0, len(choices), (1,)).item()]
            return self.forward(x_w, x, mode=sampled_mode)
        else:
            raise ValueError(f"Unknown noise mode: {mode}")
