"""
track_c/model.py - Learned Watermark Encoder, Dynamic Band-Allocation Layer, and Decoder.

Implements Section 8 (C1 & C2):
- Encoder: Message (k bits) -> Linear spatial projection -> Concat with image -> Conv residual generator
- Band-Allocation Layer (Contribution):
  1. Take 2D FFT of residual
  2. Split with 8 disjoint annular band masks
  3. Normalize each band to unit RMS
  4. Scale by sqrt(g_b * E_total), where g_b = softmax(theta)
  5. By Parseval's theorem & disjoint bands, total residual energy == E_total (exact PSNR, no amplitude cheating)
- Straight-Through Estimator (STE) 8-bit rounding
- Decoder: 7 strided conv layers + BatchNorm + GAP + Linear -> k logits
"""

from typing import Tuple, Optional
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from core.bands import band_masks


class STEQuantize(torch.autograd.Function):
    """Straight-Through Estimator for simulated 8-bit rounding."""

    @staticmethod
    def forward(ctx, x):
        # Round to 1/255 grid in [0, 1]
        return torch.clamp(torch.round(x * 255.0) / 255.0, 0.0, 1.0)

    @staticmethod
    def backward(ctx, grad_output):
        # Straight-through: pass gradients untouched
        return grad_output


def ste_round_8bit(x: torch.Tensor) -> torch.Tensor:
    return STEQuantize.apply(x)


class BandAllocationLayer(nn.Module):
    """
    Dynamic Frequency Band Allocation Layer.
    Splits spatial residual into 8 disjoint frequency bands, normalizes each band to unit energy,
    and scales each by sqrt(g_b * E_total), where g = softmax(theta).
    
    Guarantees:
    - sum(g) == 1.0
    - RMS(residual) == 10^(-PSNR / 20) exactly
    """

    def __init__(
        self,
        n_bands: int = 8,
        psnr_target: float = 40.0,
        h: int = 256,
        w: int = 256,
        fixed_regime: Optional[str] = None,  # None, 'low', 'mid', 'high'
    ):
        super().__init__()
        self.n_bands = n_bands
        self.psnr_target = psnr_target
        self.h = h
        self.w = w
        self.fixed_regime = fixed_regime

        # Target total energy E_total on [0, 1] scale
        # RMS = 10^(-PSNR/20) -> E_total = RMS^2 = 10^(-PSNR/10)
        self.target_rms = 10.0 ** (-psnr_target / 20.0)
        self.target_energy = self.target_rms ** 2

        if fixed_regime is not None:
            # Control model: fixed theta
            init_theta = torch.full((n_bands,), -1e5)
            if fixed_regime == "low":
                init_theta[0:3] = 0.0  # bands 0, 1, 2
            elif fixed_regime == "mid":
                init_theta[3:6] = 0.0  # bands 3, 4, 5
            elif fixed_regime == "high":
                init_theta[6:8] = 0.0  # bands 6, 7
            else:
                raise ValueError(f"Unknown fixed regime: {fixed_regime}")
            self.theta = nn.Parameter(init_theta, requires_grad=False)
        else:
            # Learnable band allocations
            self.theta = nn.Parameter(torch.zeros(n_bands), requires_grad=True)

        # Precompute centered masks
        masks = band_masks(h, w, n_bands=n_bands, r_max=0.5, shifted=True)
        self.register_buffer("masks", masks)  # (8, H, W)

    def get_g(self) -> torch.Tensor:
        """Return the normalized band energy fractions g_b in [0, 1]."""
        return F.softmax(self.theta, dim=0)

    def forward(self, residual: torch.Tensor) -> torch.Tensor:
        """
        residual: (B, C, H, W) where C in {1, 3}
        Returns: filtered residual with exact target energy and dynamic band allocation
        """
        b, c, h, w = residual.shape
        g = self.get_g()  # (8,)

        # Compute 2D orthonormal FFT
        res_fft = torch.fft.fftshift(torch.fft.fft2(residual, norm="ortho"), dim=(-2, -1))

        # Split into bands and reconstruct
        # masks: (8, H, W) -> expand to (1, 1, 8, H, W)
        # res_fft: (B, C, 1, H, W)
        masks_exp = self.masks.unsqueeze(0).unsqueeze(0)  # (1, 1, 8, H, W)
        res_bands_fft = res_fft.unsqueeze(2) * masks_exp  # (B, C, 8, H, W)

        # Inverse FFT per band
        res_bands_spatial = torch.fft.ifft2(
            torch.fft.ifftshift(res_bands_fft, dim=(-2, -1)), norm="ortho"
        ).real  # (B, C, 8, H, W)

        # Measure RMS per band
        band_rms = torch.sqrt(torch.mean(res_bands_spatial ** 2, dim=(-2, -1), keepdim=True) + 1e-12)
        unit_bands = res_bands_spatial / band_rms

        # Scale each band by sqrt(g_b * E_total)
        # g: (8,) -> scale: (1, 1, 8, 1, 1)
        band_scales = torch.sqrt(g * self.target_energy).view(1, 1, self.n_bands, 1, 1)
        scaled_bands = unit_bands * band_scales

        # Sum disjoint bands to obtain synthesized residual
        total_res = scaled_bands.sum(dim=2)  # (B, C, H, W)

        # Renormalize to ensure exact target RMS
        actual_rms = torch.sqrt(torch.mean(total_res ** 2, dim=(-2, -1), keepdim=True) + 1e-12)
        final_res = total_res * (self.target_rms / actual_rms)

        return final_res


class WatermarkEncoder(nn.Module):
    """
    Message-conditioned spatial residual encoder with integrated Band Allocation Layer.
    """

    def __init__(
        self,
        n_bits: int = 32,
        psnr_target: float = 40.0,
        fixed_regime: Optional[str] = None,
    ):
        super().__init__()
        self.n_bits = n_bits

        # Message projection: k bits -> 32 channels of 32x32 -> upsample to 256x256
        self.msg_fc = nn.Linear(n_bits, 32 * 32 * 32)

        # Conv backbone
        self.conv1 = nn.Conv2d(3 + 32, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 32, kernel_size=3, padding=1)
        self.conv4 = nn.Conv2d(32, 3, kernel_size=3, padding=1)

        self.band_layer = BandAllocationLayer(
            n_bands=8, psnr_target=psnr_target, fixed_regime=fixed_regime
        )

    def forward(self, x: torch.Tensor, msg: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        x: (B, 3, 256, 256) in [0, 1]
        msg: (B, k) in {0, 1}
        Returns:
            x_w: Watermarked image with STE 8-bit rounding
            residual: Added residual
        """
        b = x.shape[0]
        # Bipolar msg symbols
        msg_bipolar = 2.0 * msg.float() - 1.0
        msg_feat = self.msg_fc(msg_bipolar).view(b, 32, 32, 32)
        msg_map = F.interpolate(msg_feat, size=(256, 256), mode="bilinear", align_corners=False)

        feat = torch.cat([x, msg_map], dim=1)
        feat = F.relu(self.conv1(feat))
        feat = F.relu(self.conv2(feat))
        feat = F.relu(self.conv3(feat))
        raw_res = self.conv4(feat)

        # Pass through band allocation layer (forces exact target PSNR)
        res = self.band_layer(raw_res)

        # Add residual to image & apply STE 8-bit quantization
        x_w = ste_round_8bit(x + res)
        return x_w, res


class WatermarkDecoder(nn.Module):
    """
    Strided Conv + BatchNorm watermark bit decoder (ResNet-18 scale).
    Outputs k unnormalized logits for binary cross-entropy loss.
    """

    def __init__(self, n_bits: int = 32):
        super().__init__()
        self.n_bits = n_bits

        channels = [3, 32, 64, 128, 256, 256, 512]
        layers = []
        for in_c, out_c in zip(channels[:-1], channels[1:]):
            layers.extend([
                nn.Conv2d(in_c, out_c, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm2d(out_c),
                nn.LeakyReLU(0.2, inplace=True),
            ])

        self.backbone = nn.Sequential(*layers)
        self.gap = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, n_bits)

    def forward(self, y: torch.Tensor) -> torch.Tensor:
        """
        y: (B, 3, 256, 256)
        Returns: logits of shape (B, n_bits)
        """
        feat = self.backbone(y)
        pooled = self.gap(feat).flatten(1)
        logits = self.fc(pooled)
        return logits
