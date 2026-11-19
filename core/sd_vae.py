"""
core/sd_vae.py - Standalone Pure PyTorch Implementation of Stable Diffusion AutoencoderKL.

Loads 'stabilityai/sd-vae-ft-mse' weights directly from HuggingFace safetensors
with ZERO external dependencies on diffusers, transformers, peft, or accelerate.
Provides the exact same interface:
    vae.encode(x).latent_dist.mean
    vae.decode(z).sample
"""

import os
from pathlib import Path
from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class ResnetBlock2D(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.norm1 = nn.GroupNorm(num_groups=32, num_channels=in_channels, eps=1e-6)
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, stride=1, padding=1)
        self.norm2 = nn.GroupNorm(num_groups=32, num_channels=out_channels, eps=1e-6)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, stride=1, padding=1)
        if in_channels != out_channels:
            self.conv_shortcut = nn.Conv2d(in_channels, out_channels, 1, stride=1, padding=0)
        else:
            self.conv_shortcut = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.conv1(F.silu(self.norm1(x)))
        h = self.conv2(F.silu(self.norm2(h)))
        if self.conv_shortcut is not None:
            x = self.conv_shortcut(x)
        return x + h


class Attention(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.group_norm = nn.GroupNorm(num_groups=32, num_channels=channels, eps=1e-6)
        self.to_q = nn.Linear(channels, channels)
        self.to_k = nn.Linear(channels, channels)
        self.to_v = nn.Linear(channels, channels)
        self.to_out = nn.ModuleList([nn.Linear(channels, channels)])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        resid = x
        normed = self.group_norm(x).permute(0, 2, 3, 1).reshape(b, h * w, c)
        q = self.to_q(normed)
        k = self.to_k(normed)
        v = self.to_v(normed)
        out = F.scaled_dot_product_attention(q.unsqueeze(1), k.unsqueeze(1), v.unsqueeze(1)).squeeze(1)
        out = self.to_out[0](out).reshape(b, h, w, c).permute(0, 3, 1, 2)
        return resid + out


class Downsample2D(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.conv = nn.Conv2d(channels, channels, 3, stride=2, padding=0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Asymmetric pad matching diffusers / CompVis Downsample2D
        return self.conv(F.pad(x, (0, 1, 0, 1), mode="constant", value=0))


class Upsample2D(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.conv = nn.Conv2d(channels, channels, 3, stride=1, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(F.interpolate(x, scale_factor=2.0, mode="nearest"))


class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv_in = nn.Conv2d(3, 128, 3, padding=1)
        self.down_blocks = nn.ModuleList([
            nn.ModuleDict({
                "resnets": nn.ModuleList([ResnetBlock2D(128, 128), ResnetBlock2D(128, 128)]),
                "downsamplers": nn.ModuleList([Downsample2D(128)])
            }),
            nn.ModuleDict({
                "resnets": nn.ModuleList([ResnetBlock2D(128, 256), ResnetBlock2D(256, 256)]),
                "downsamplers": nn.ModuleList([Downsample2D(256)])
            }),
            nn.ModuleDict({
                "resnets": nn.ModuleList([ResnetBlock2D(256, 512), ResnetBlock2D(512, 512)]),
                "downsamplers": nn.ModuleList([Downsample2D(512)])
            }),
            nn.ModuleDict({
                "resnets": nn.ModuleList([ResnetBlock2D(512, 512), ResnetBlock2D(512, 512)])
            }),
        ])
        self.mid_block = nn.ModuleDict({
            "resnets": nn.ModuleList([ResnetBlock2D(512, 512), ResnetBlock2D(512, 512)]),
            "attentions": nn.ModuleList([Attention(512)])
        })
        self.conv_norm_out = nn.GroupNorm(32, 512, eps=1e-6)
        self.conv_act = nn.SiLU()
        self.conv_out = nn.Conv2d(512, 8, 3, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.conv_in(x)
        for block in self.down_blocks:
            for r in block["resnets"]:
                h = r(h)
            if "downsamplers" in block:
                for d in block["downsamplers"]:
                    h = d(h)
        h = self.mid_block["resnets"][0](h)
        h = self.mid_block["attentions"][0](h)
        h = self.mid_block["resnets"][1](h)
        h = self.conv_norm_out(h)
        h = self.conv_act(h)
        return self.conv_out(h)


class Decoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv_in = nn.Conv2d(4, 512, 3, padding=1)
        self.mid_block = nn.ModuleDict({
            "resnets": nn.ModuleList([ResnetBlock2D(512, 512), ResnetBlock2D(512, 512)]),
            "attentions": nn.ModuleList([Attention(512)])
        })
        self.up_blocks = nn.ModuleList([
            nn.ModuleDict({
                "resnets": nn.ModuleList([ResnetBlock2D(512, 512), ResnetBlock2D(512, 512), ResnetBlock2D(512, 512)]),
                "upsamplers": nn.ModuleList([Upsample2D(512)])
            }),
            nn.ModuleDict({
                "resnets": nn.ModuleList([ResnetBlock2D(512, 512), ResnetBlock2D(512, 512), ResnetBlock2D(512, 512)]),
                "upsamplers": nn.ModuleList([Upsample2D(512)])
            }),
            nn.ModuleDict({
                "resnets": nn.ModuleList([ResnetBlock2D(512, 256), ResnetBlock2D(256, 256), ResnetBlock2D(256, 256)]),
                "upsamplers": nn.ModuleList([Upsample2D(256)])
            }),
            nn.ModuleDict({
                "resnets": nn.ModuleList([ResnetBlock2D(256, 128), ResnetBlock2D(128, 128), ResnetBlock2D(128, 128)])
            }),
        ])
        self.conv_norm_out = nn.GroupNorm(32, 128, eps=1e-6)
        self.conv_act = nn.SiLU()
        self.conv_out = nn.Conv2d(128, 3, 3, padding=1)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        h = self.conv_in(z)
        h = self.mid_block["resnets"][0](h)
        h = self.mid_block["attentions"][0](h)
        h = self.mid_block["resnets"][1](h)
        for block in self.up_blocks:
            for r in block["resnets"]:
                h = r(h)
            if "upsamplers" in block:
                for u in block["upsamplers"]:
                    h = u(h)
        h = self.conv_norm_out(h)
        h = self.conv_act(h)
        return self.conv_out(h)


class PureAutoencoderKL(nn.Module):
    """
    Pure PyTorch drop-in replacement for diffusers.AutoencoderKL.
    Provides identical interface:
        encode(x).latent_dist.mean
        decode(z).sample
    """
    def __init__(self):
        super().__init__()
        self.encoder = Encoder()
        self.decoder = Decoder()
        self.quant_conv = nn.Conv2d(8, 8, 1)
        self.post_quant_conv = nn.Conv2d(4, 4, 1)

    class LatentDist:
        def __init__(self, mean: torch.Tensor):
            self.mean = mean

    class Output:
        def __init__(self, sample: torch.Tensor):
            self.sample = sample

    def encode(self, x: torch.Tensor):
        h = self.encoder(x)
        moments = self.quant_conv(h)
        mean, _ = torch.chunk(moments, 2, dim=1)
        res = type("", (), {})()
        res.latent_dist = self.LatentDist(mean)
        return res

    def decode(self, z: torch.Tensor):
        z = self.post_quant_conv(z)
        rec = self.decoder(z)
        res = type("", (), {})()
        res.sample = rec
        return res


def load_sd_vae(model_id: str = "stabilityai/sd-vae-ft-mse", device: Optional[torch.device] = None) -> nn.Module:
    """
    Downloads and loads SD-VAE weights directly into PureAutoencoderKL.
    Requires only huggingface_hub and safetensors.
    """
    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PureAutoencoderKL().to(device=device, dtype=torch.float32)

    try:
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file
        weights_path = hf_hub_download(repo_id=model_id, filename="diffusion_pytorch_model.safetensors")
        state_dict = load_file(weights_path)
    except Exception as e:
        # Fallback to .bin PyTorch format if safetensors fails
        from huggingface_hub import hf_hub_download
        weights_path = hf_hub_download(repo_id=model_id, filename="diffusion_pytorch_model.bin")
        state_dict = torch.load(weights_path, map_location=device)

    # Load weights into pure PyTorch model
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing:
        print(f"Warning: {len(missing)} missing keys when loading {model_id}: {missing[:5]}")
    model.eval()
    for p in model.parameters():
        p.requires_grad = False
    print(f"✓ Pure PyTorch AutoencoderKL loaded successfully from {weights_path}")
    return model
