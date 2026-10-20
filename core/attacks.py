"""
core/attacks.py - Deterministic Attack Wrappers for VAE Regeneration and Baseline Distortions.

Implements Sections 0.4 and 4 (Contract 1):
- Interface: attack(x, strength, seed=None) -> x_attacked
- Inputs: float tensor in [0, 1], shape (B, 3, H, W)
- Deterministic behavior: fixed seed ensures A(x) and A(x_w) undergo identical noise
- Supported families:
  1. CompressAI (bmshj2018-factorized, qualities 1-8)
  2. SD VAE (stabilityai/sd-vae-ft-mse, posterior mean with pre-noise sigma)
  3. Gaussian Noise (sigma)
  4. Gaussian Blur (sigma / kernel_size)
  5. JPEG Compression (quality 100 to 10)
"""

from typing import Dict, Any, List, Optional, Union
import io
import math
import torch
import torch.nn as nn
import numpy as np
from PIL import Image


class AttackBase:
    """Base interface for all attacks matching Contract 1."""
    name: str = "base"
    strengths: List[Any] = []

    def __call__(
        self,
        x: torch.Tensor,
        strength: Any,
        seed: Optional[int] = None
    ) -> torch.Tensor:
        raise NotImplementedError


class GaussianNoiseAttack(AttackBase):
    """Additive Gaussian noise with standard deviation sigma."""
    name = "gaussian_noise"
    strengths = [0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2]

    def __call__(
        self,
        x: torch.Tensor,
        strength: float,
        seed: Optional[int] = None
    ) -> torch.Tensor:
        sigma = float(strength)
        if sigma <= 0.0:
            return x.clone()
        generator = torch.Generator(device=x.device if x.device.type != "mps" else "cpu")
        if seed is not None:
            generator.manual_seed(seed)
        noise = torch.randn(x.shape, generator=generator, device=x.device, dtype=x.dtype) * sigma
        return torch.clamp(x + noise, 0.0, 1.0)


class GaussianBlurAttack(AttackBase):
    """Spatial 2D Gaussian blur with radius sigma."""
    name = "gaussian_blur"
    strengths = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    def __call__(
        self,
        x: torch.Tensor,
        strength: float,
        seed: Optional[int] = None
    ) -> torch.Tensor:
        sigma = float(strength)
        if sigma <= 0.05:
            return x.clone()
        kernel_size = int(math.ceil(sigma * 4)) // 2 * 2 + 1
        radius = kernel_size // 2
        coords = torch.arange(-radius, radius + 1, device=x.device, dtype=x.dtype)
        k1d = torch.exp(-0.5 * (coords / sigma) ** 2)
        k1d = k1d / k1d.sum()
        k2d = torch.outer(k1d, k1d)
        kernel = k2d.view(1, 1, kernel_size, kernel_size).repeat(x.shape[-3], 1, 1, 1)

        pad = radius
        x_pad = torch.nn.functional.pad(x, (pad, pad, pad, pad), mode="reflect")
        blurred = torch.nn.functional.conv2d(x_pad, kernel, groups=x.shape[-3])
        return torch.clamp(blurred, 0.0, 1.0)


class JPEGAttack(AttackBase):
    """Standard 8-bit JPEG compression via PIL."""
    name = "jpeg"
    strengths = [90, 80, 70, 60, 50, 40, 30, 20]

    def __call__(
        self,
        x: torch.Tensor,
        strength: int,
        seed: Optional[int] = None
    ) -> torch.Tensor:
        quality = int(strength)
        device = x.device
        dtype = x.dtype
        # Process batch element-wise
        x_np = (torch.clamp(x, 0.0, 1.0) * 255.0).round().byte().cpu().numpy()
        b = x_np.shape[0] if x.dim() == 4 else 1
        if x.dim() == 3:
            x_np = x_np[np.newaxis, ...]

        out_list = []
        for i in range(b):
            img_arr = np.transpose(x_np[i], (1, 2, 0))  # (H, W, 3)
            img_pil = Image.fromarray(img_arr)
            buffer = io.BytesIO()
            img_pil.save(buffer, format="JPEG", quality=quality)
            buffer.seek(0)
            decompressed = Image.open(buffer)
            rec_arr = np.array(decompressed, dtype=np.float32) / 255.0
            out_list.append(torch.from_numpy(rec_arr.transpose(2, 0, 1)))

        out_tensor = torch.stack(out_list, dim=0).to(device=device, dtype=dtype)
        if x.dim() == 3:
            out_tensor = out_tensor.squeeze(0)
        return out_tensor


class CompressAIAttack(AttackBase):
    """
    CompressAI bmshj2018-factorized regeneration VAE.
    Strengths correspond to quality factor q in [1, 8].
    """
    name = "compressai_bmshj2018"
    strengths = [1, 2, 3, 4, 5, 6, 7, 8]

    def __init__(self, device: Optional[torch.device] = None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._models: Dict[int, nn.Module] = {}

    def get_model(self, quality: int) -> nn.Module:
        if quality not in self._models:
            import compressai.zoo as zoo
            model = zoo.bmshj2018_factorized(quality=quality, pretrained=True)
            model.eval().to(self.device)
            # Freeze parameters
            for p in model.parameters():
                p.requires_grad = False
            self._models[quality] = model
        return self._models[quality]

    def __call__(
        self,
        x: torch.Tensor,
        strength: int,
        seed: Optional[int] = None
    ) -> torch.Tensor:
        quality = int(strength)
        model = self.get_model(quality)
        orig_device = x.device
        orig_dtype = x.dtype
        inp = x.to(device=self.device, dtype=torch.float32)

        if seed is not None:
            torch.manual_seed(seed)

        with torch.no_grad():
            out = model(inp)
            x_hat = out["x_hat"]

        return torch.clamp(x_hat, 0.0, 1.0).to(device=orig_device, dtype=orig_dtype)


class StableDiffusionVAEAttack(AttackBase):
    """
    Stable Diffusion VAE (stabilityai/sd-vae-ft-mse).
    Noise-then-reconstruct regeneration pattern:
    - Add Gaussian pre-noise with std = sigma
    - Encode to posterior distribution
    - Take posterior mean
    - Decode reconstruction back to image space
    """
    name = "sd_vae"
    strengths = [0.0, 0.02, 0.05, 0.1, 0.15, 0.2]

    def __init__(self, model_id: str = "stabilityai/sd-vae-ft-mse", device: Optional[torch.device] = None):
        self.model_id = model_id
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._vae: Optional[nn.Module] = None

    def get_vae(self) -> nn.Module:
        if self._vae is None:
            from diffusers import AutoencoderKL
            vae = AutoencoderKL.from_pretrained(self.model_id)
            vae.eval().to(self.device)
            for p in vae.parameters():
                p.requires_grad = False
            self._vae = vae
        return self._vae

    def __call__(
        self,
        x: torch.Tensor,
        strength: float,
        seed: Optional[int] = None
    ) -> torch.Tensor:
        sigma = float(strength)
        orig_device = x.device
        orig_dtype = x.dtype

        # Add deterministic pre-noise
        generator = torch.Generator(device=x.device if x.device.type != "mps" else "cpu")
        if seed is not None:
            generator.manual_seed(seed)
        if sigma > 0.0:
            noise = torch.randn(x.shape, generator=generator, device=x.device, dtype=x.dtype) * sigma
            x_noisy = torch.clamp(x + noise, 0.0, 1.0)
        else:
            x_noisy = x

        vae = self.get_vae()
        # SD VAE expects input normalized to [-1, 1]
        x_scaled = (x_noisy * 2.0 - 1.0).to(device=self.device, dtype=torch.float32)

        with torch.no_grad():
            latent_dist = vae.encode(x_scaled).latent_dist
            # As required by guide Section 0.4: take posterior mean
            z = latent_dist.mean
            rec = vae.decode(z).sample

        # Convert back from [-1, 1] to [0, 1]
        x_out = torch.clamp((rec + 1.0) / 2.0, 0.0, 1.0)
        return x_out.to(device=orig_device, dtype=orig_dtype)


def get_attack_family(name: str) -> AttackBase:
    """Factory function for retrieving an attack wrapper by family name."""
    name_clean = name.lower().strip()
    if name_clean in ("gaussian_noise", "noise"):
        return GaussianNoiseAttack()
    elif name_clean in ("gaussian_blur", "blur"):
        return GaussianBlurAttack()
    elif name_clean in ("jpeg", "jpg"):
        return JPEGAttack()
    elif name_clean in ("compressai", "bmshj2018", "compressai_bmshj2018"):
        return CompressAIAttack()
    elif name_clean in ("sd_vae", "sdvae", "diffusion_vae"):
        return StableDiffusionVAEAttack()
    else:
        raise ValueError(f"Unknown attack family: {name}")
