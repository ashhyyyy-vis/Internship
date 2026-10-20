"""
track_b/watermark.py - Classical 32-bit Spread-Spectrum Annular Watermarker.

Implements Section 7 (B1) & Section 4 (Contract 2):
- Message: k = 32 bits (b_i in {0, 1})
- Carriers: c_i band-limited white noise inside annulus b, seeded by (key, bit_index, band), unit RMS
- Modulation: s = sum_{i=1}^k (2 * b_i - 1) * c_i
- Energy normalization: s normalized to RMS = 10^(-PSNR/20) and added across RGB
- Blind correlation decoding:
  y_norm = y - mean(y)
  b_hat_i = 1 if <y_norm, c_i> > 0 else 0
"""

from typing import Tuple, Optional, List
import math
import torch
import numpy as np

from core.bands import band_masks
from core.radial import rgb_to_luminance
from core.probes import round_to_8bit


class ClassicalSpreadSpectrumWatermarker:
    """Implements Contract 2 for the classical annular spread-spectrum baseline."""

    def __init__(
        self,
        n_bits: int = 32,
        n_bands: int = 8,
        h: int = 256,
        w: int = 256,
        secret_key: int = 42,
        device: Optional[torch.device] = None,
    ):
        self.n_bits = n_bits
        self.n_bands = n_bands
        self.h = h
        self.w = w
        self.secret_key = secret_key
        self.device = device or torch.device("cpu")
        self._carriers_cache = {}

    def get_carriers(self, band_idx: int) -> torch.Tensor:
        """
        Generate or retrieve cached set of k unit-RMS carriers for band_idx.
        Returns: Tensor of shape (n_bits, H, W)
        """
        if band_idx in self._carriers_cache:
            return self._carriers_cache[band_idx]

        masks = band_masks(self.h, self.w, n_bands=self.n_bands, r_max=0.5, shifted=True, device=self.device)
        mask = masks[band_idx]

        carriers = []
        for bit_idx in range(self.n_bits):
            # Seed per (key, bit_index, band)
            carrier_seed = (self.secret_key * 10007 + bit_idx * 997 + band_idx * 31) & 0x7FFFFFFF
            gen = torch.Generator(device=self.device).manual_seed(carrier_seed)
            w_noise = torch.randn(self.h, self.w, generator=gen, device=self.device, dtype=torch.float32)

            w_fft = torch.fft.fftshift(torch.fft.fft2(w_noise, norm="ortho"))
            w_band = w_fft * mask
            c_spatial = torch.fft.ifft2(torch.fft.ifftshift(w_band), norm="ortho").real

            # Unit RMS
            rms = torch.sqrt(torch.mean(c_spatial ** 2))
            if rms > 1e-10:
                c_unit = c_spatial / rms
            else:
                c_unit = torch.zeros_like(c_spatial)

            carriers.append(c_unit)

        stacked_carriers = torch.stack(carriers, dim=0)  # (n_bits, H, W)
        self._carriers_cache[band_idx] = stacked_carriers
        return stacked_carriers

    def embed(
        self,
        x: torch.Tensor,
        msg: torch.Tensor,
        band_idx: int,
        psnr_db: float,
        round_8bit: bool = True,
    ) -> torch.Tensor:
        """
        Embed message into image x at specified target PSNR and band.
        
        Args:
            x: Tensor of shape (..., 3, H, W) in [0, 1]
            msg: Binary tensor of shape (..., n_bits) with values in {0, 1}
            band_idx: Annulus index [0, 7]
            psnr_db: Target PSNR in dB
            round_8bit: Whether to round to 8-bit precision
            
        Returns:
            x_w: Watermarked image tensor in [0, 1]
        """
        carriers = self.get_carriers(band_idx).to(device=x.device, dtype=x.dtype)  # (k, H, W)

        # Modulated signal: s = sum_i (2 * b_i - 1) * c_i
        # b in {0, 1} -> bipolar symbols in {-1, +1}
        bipolar = (2.0 * msg.float() - 1.0)  # (..., k)

        # Einsum: multiply each carrier by bit symbol and sum
        # bipolar: (..., k), carriers: (k, H, W) -> signal: (..., H, W)
        signal = torch.einsum("...k,khw->...hw", bipolar, carriers)

        # Total signal RMS normalization
        # Target RMS = 10^(-PSNR / 20)
        target_rms = 10.0 ** (-psnr_db / 20.0)
        sig_rms = torch.sqrt(torch.mean(signal ** 2, dim=(-2, -1), keepdim=True))
        sig_scaled = (signal / (sig_rms + 1e-12)) * target_rms

        # Add pattern across RGB channels (luminance shift)
        if x.dim() >= 3 and x.shape[-3] in (1, 3):
            sig_expanded = sig_scaled.unsqueeze(-3)
        else:
            sig_expanded = sig_scaled

        x_w = x + sig_expanded

        if round_8bit:
            x_w = round_to_8bit(x_w)
        else:
            x_w = torch.clamp(x_w, 0.0, 1.0)

        return x_w

    def decode(
        self,
        y: torch.Tensor,
        band_idx: int,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Blind correlation decoder.
        
        Args:
            y: Received image tensor (..., 3, H, W) in [0, 1]
            band_idx: The band to correlate against
            
        Returns:
            hard_bits: Binary tensor (..., n_bits)
            correlations: Raw correlation values (..., n_bits)
        """
        # Convert received image to luminance
        if y.dim() >= 3 and y.shape[-3] == 3:
            y_lum = rgb_to_luminance(y)
        else:
            y_lum = y.squeeze(-3) if y.dim() >= 3 else y

        # Zero-mean luminance
        y_mean = y_lum.mean(dim=(-2, -1), keepdim=True)
        y_zero_mean = y_lum - y_mean

        carriers = self.get_carriers(band_idx).to(device=y.device, dtype=y.dtype)  # (k, H, W)

        # Correlation: <y_norm, c_i> = mean(y_norm * c_i)
        # y_zero_mean: (..., H, W), carriers: (k, H, W) -> (..., k)
        corr = torch.einsum("...hw,khw->...k", y_zero_mean, carriers) / (self.h * self.w)

        # Hard decision: b_hat = 1 if corr > 0 else 0
        hard_bits = (corr > 0.0).long()

        return hard_bits, corr
