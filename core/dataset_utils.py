"""
core/dataset_utils.py - Resilient Dataset Resolution and Image Discovery.

Provides automatic directory detection so scripts seamlessly find images whether
extracted to data/fit, data/processed/fit, data/test, data/train, or data/raw/val2017.
"""

from pathlib import Path
from typing import Optional, List, Union


CANDIDATE_DIRS = [
    Path("data/processed/fit"),
    Path("data/fit"),
    Path("data/processed/test"),
    Path("data/test"),
    Path("data/processed/train"),
    Path("data/train"),
    Path("data/raw/val2017"),
    Path("data/val2017"),
]


def resolve_image_path(images_dir: Union[str, Path], fname: str) -> Path:
    """
    Search for an image by filename across images_dir and common fallback paths.
    Tries both original filename and .png/.jpg stem substitutions.
    Raises FileNotFoundError with full search diagnosis if not found.
    """
    p_dir = Path(images_dir)
    stem = Path(fname).stem
    candidates = [
        p_dir / fname,
        p_dir / f"{stem}.png",
        p_dir / f"{stem}.jpg",
        p_dir / "fit" / f"{stem}.png",
        p_dir / "test" / f"{stem}.png",
        p_dir / "train" / f"{stem}.png",
    ]

    for extra in CANDIDATE_DIRS:
        candidates.append(extra / fname)
        candidates.append(extra / f"{stem}.png")
        candidates.append(extra / f"{stem}.jpg")

    for path in candidates:
        if path.exists() and path.is_file():
            return path

    searched_str = "\n  - " + "\n  - ".join(str(c.resolve()) for c in candidates[:8])
    raise FileNotFoundError(
        f"Could not locate image '{fname}' (stem: '{stem}'). Checked locations:{searched_str}\n"
        f"Please verify that the dataset splits are extracted in data/."
    )
