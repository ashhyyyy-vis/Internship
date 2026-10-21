"""
track_d/metrics.py - Evaluation Metrics, Binomial Null Statistics, and Empirical Null Validation.

Implements Section 9 (Track D):
- PSNR (8-bit RGB [0, 255] or [0, 1])
- SSIM (structural similarity)
- Bit Accuracy (mean agreement over k bits)
- Binomial TPR@FPR:
  tau = smallest bit-agreement count whose binomial tail sf(tau-1, k, 0.5) <= target_fpr
  TPR = fraction of attacked watermarked images with bit agreement >= tau
- Empirical Null Check:
  Decodes unwatermarked attacked images to verify bit agreement averages 50% (+- 1%) with no per-bit bias
"""

from typing import Tuple, List, Dict, Optional, Union, Any
import math
import torch
import numpy as np
from scipy.stats import binom


def compute_bit_accuracy(pred_bits: torch.Tensor, target_bits: torch.Tensor) -> float:
    """Compute elementwise bit accuracy in [0, 1]."""
    if not isinstance(pred_bits, torch.Tensor):
        pred_bits = torch.tensor(pred_bits)
    if not isinstance(target_bits, torch.Tensor):
        target_bits = torch.tensor(target_bits)
    matches = (pred_bits == target_bits).float()
    return float(matches.mean().item())


def calculate_tau(n_bits: int = 32, target_fpr: float = 0.01) -> int:
    """
    Returns the minimum bit agreement threshold tau such that:
    P(X >= tau | H0: p=0.5) <= target_fpr.
    """
    for tau in range(n_bits, 0, -1):
        if binom.sf(tau - 1, n_bits, 0.5) <= target_fpr:
            continue
        else:
            return tau + 1
    return n_bits


def compute_tpr_at_fpr(
    bit_agreements: Union[torch.Tensor, np.ndarray, List[int]],
    n_bits: int = 32,
    target_fpr: float = 0.01
) -> Tuple[float, int]:
    """
    Calculate True Positive Rate (TPR) at target False Positive Rate (FPR) using binomial null.
    Returns: (tpr, tau)
    """
    tau = calculate_tau(n_bits=n_bits, target_fpr=target_fpr)
    arr = np.asarray(bit_agreements)
    tpr = float(np.mean(arr >= tau))
    return tpr, tau


def empirical_null_check(
    watermarker: Any,
    unwatermarked_images: List[torch.Tensor],
    attacks: List[Any],
    band_idx: int = 3,
    n_bits: int = 32,
) -> Dict[str, Any]:
    """
    Sanity null check: Decodes unwatermarked, attacked images to verify
    bit agreement averages ~50% with no per-bit bias.
    """
    total_bits = 0
    total_correct = 0
    bit_accumulator = torch.zeros(n_bits)

    dummy_target = torch.randint(0, 2, (1, n_bits))

    for x in unwatermarked_images:
        for att in attacks:
            for s in att.strengths[:2]:
                x_att = att(x, strength=s, seed=123)
                if hasattr(watermarker, "decode"):
                    decoded, _ = watermarker.decode(x_att, band_idx=band_idx)
                else:
                    decoded = (watermarker(x_att) > 0.0).long()

                matches = (decoded.cpu() == dummy_target).squeeze(0)
                bit_accumulator += matches.float()
                total_correct += matches.sum().item()
                total_bits += n_bits

    empirical_acc = total_correct / max(total_bits, 1)
    per_bit_freq = (bit_accumulator / max(len(unwatermarked_images) * len(attacks) * 2, 1)).tolist()

    print(f"[Null Check] Empirical null bit accuracy: {empirical_acc:.4f} (expected ~0.5000)")
    assert abs(empirical_acc - 0.5) < 0.05, f"Biased null decoder! Bit accuracy = {empirical_acc}"

    return {
        "mean_null_acc": empirical_acc,
        "per_bit_freq": per_bit_freq,
        "passed": abs(empirical_acc - 0.5) < 0.05,
    }
