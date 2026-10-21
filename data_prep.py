"""
data_prep.py - COCO val2017 Download, Split Partitioning, and Preprocessing.

Implements Sections 2.1 & 5 (Phase 0.1):
1. Downloads COCO val2017 (5,000 images, ~1 GB) or works from an existing local copy.
2. Creates non-overlapping deterministic manifests:
   - 300 images -> data/manifests/fit_manifest.json (for Tracks A & B)
   - 500 images -> data/manifests/test_manifest.json (held-out for Merge 2)
   - Remaining ~4,200 images -> data/manifests/train_manifest.json (for Track C)
3. Preprocessing:
   - Resize shorter edge to 256 (bicubic)
   - Center crop to exactly 256x256
   - Save fit and test sets as 8-bit PNGs
4. Packs fit and test sets into a compact zip (data/processed_splits.zip) for 1-click Colab upload.
"""

import os
import json
import random
import zipfile
import urllib.request
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
from tqdm import tqdm


DATA_DIR = Path(__file__).resolve().parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MANIFEST_DIR = DATA_DIR / "manifests"

COCO_VAL2017_URL = "http://images.cocodataset.org/zips/val2017.zip"


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "fit").mkdir(exist_ok=True)
    (PROCESSED_DIR / "test").mkdir(exist_ok=True)
    (PROCESSED_DIR / "train").mkdir(exist_ok=True)


def download_val2017() -> Path:
    """Download COCO val2017 archive if not already downloaded."""
    ensure_dirs()
    zip_path = RAW_DIR / "val2017.zip"
    extracted_dir = RAW_DIR / "val2017"

    if extracted_dir.exists() and len(list(extracted_dir.glob("*.jpg"))) >= 5000:
        print(f"[data_prep] Using existing extracted COCO val2017 at {extracted_dir}")
        return extracted_dir

    if not zip_path.exists() and not extracted_dir.exists():
        print(f"[data_prep] Downloading COCO val2017 from {COCO_VAL2017_URL}...")
        urllib.request.urlretrieve(COCO_VAL2017_URL, zip_path)
        print("[data_prep] Download complete.")

    if not extracted_dir.exists():
        print(f"[data_prep] Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(RAW_DIR)
        print(f"[data_prep] Extracted to {extracted_dir}")
        if zip_path.exists():
            zip_path.unlink()
            print("[data_prep] Removed raw zip archive to conserve disk space.")
    return extracted_dir


def create_manifests(
    image_dir: Path,
    n_fit: int = 300,
    n_test: int = 500,
    seed: int = 42
) -> Tuple[List[str], List[str], List[str]]:
    """
    Partition images into non-overlapping splits:
    n_fit: exactly 300
    n_test: exactly 500
    train: remaining (~4,200)
    """
    all_files = sorted([f.name for f in image_dir.glob("*.jpg")])
    if len(all_files) < (n_fit + n_test):
        raise ValueError(f"Found only {len(all_files)} images, need at least {n_fit + n_test}")

    rng = random.Random(seed)
    rng.shuffle(all_files)

    fit_files = sorted(all_files[:n_fit])
    test_files = sorted(all_files[n_fit:n_fit + n_test])
    train_files = sorted(all_files[n_fit + n_test:])

    # Verify zero overlap
    set_fit = set(fit_files)
    set_test = set(test_files)
    set_train = set(train_files)
    assert len(set_fit & set_test) == 0, "Overlap between fit and test splits!"
    assert len(set_fit & set_train) == 0, "Overlap between fit and train splits!"
    assert len(set_test & set_train) == 0, "Overlap between test and train splits!"

    with open(MANIFEST_DIR / "fit_manifest.json", "w") as f:
        json.dump(fit_files, f, indent=2)

    with open(MANIFEST_DIR / "test_manifest.json", "w") as f:
        json.dump(test_files, f, indent=2)

    with open(MANIFEST_DIR / "train_manifest.json", "w") as f:
        json.dump(train_files, f, indent=2)

    print(f"[data_prep] Saved manifests: {len(fit_files)} fit, {len(test_files)} test, {len(train_files)} train.")
    return fit_files, test_files, train_files


def preprocess_image(src_path: Path, dst_path: Path, target_size: int = 256):
    """
    Resize shorter side to target_size (bicubic) and center crop to target_size x target_size.
    Save as 8-bit RGB PNG.
    """
    with Image.open(src_path) as img:
        img = img.convert("RGB")
        w, h = img.size

        # Resize shorter edge to target_size
        if w < h:
            new_w = target_size
            new_h = int(round(h * (target_size / w)))
        else:
            new_h = target_size
            new_w = int(round(w * (target_size / h)))

        img_resized = img.resize((new_w, new_h), Image.Resampling.BICUBIC)

        # Center crop
        left = (new_w - target_size) // 2
        top = (new_h - target_size) // 2
        right = left + target_size
        bottom = top + target_size

        img_cropped = img_resized.crop((left, top, right, bottom))
        img_cropped.save(dst_path, format="PNG")


def preprocess_splits(raw_dir: Path, fit_files: List[str], test_files: List[str], train_files: Optional[List[str]] = None, max_train: int = 1000):
    """Process and save fit (300), test (500), and train sets as 256x256 PNGs."""
    print("[data_prep] Preprocessing fit split (300 images)...")
    fit_out = PROCESSED_DIR / "fit"
    for fname in tqdm(fit_files):
        stem = Path(fname).stem
        preprocess_image(raw_dir / fname, fit_out / f"{stem}.png")

    print("[data_prep] Preprocessing test split (500 images)...")
    test_out = PROCESSED_DIR / "test"
    for fname in tqdm(test_files):
        stem = Path(fname).stem
        preprocess_image(raw_dir / fname, test_out / f"{stem}.png")

    if train_files:
        train_subset = train_files[:max_train]
        print(f"[data_prep] Preprocessing train split ({len(train_subset)} images)...")
        train_out = PROCESSED_DIR / "train"
        for fname in tqdm(train_subset):
            stem = Path(fname).stem
            preprocess_image(raw_dir / fname, train_out / f"{stem}.png")

    print("[data_prep] Packing processed fit & test splits into zip for Colab upload...")
    zip_target = DATA_DIR / "processed_splits.zip"
    with zipfile.ZipFile(zip_target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in fit_out.glob("*.png"):
            zf.write(p, arcname=f"fit/{p.name}")
        for p in test_out.glob("*.png"):
            zf.write(p, arcname=f"test/{p.name}")
        if (PROCESSED_DIR / "train").exists():
            for p in (PROCESSED_DIR / "train").glob("*.png"):
                zf.write(p, arcname=f"train/{p.name}")
        zf.write(MANIFEST_DIR / "fit_manifest.json", arcname="manifests/fit_manifest.json")
        zf.write(MANIFEST_DIR / "test_manifest.json", arcname="manifests/test_manifest.json")
        zf.write(MANIFEST_DIR / "train_manifest.json", arcname="manifests/train_manifest.json")

    print(f"[data_prep] Packed {zip_target} (Size: {zip_target.stat().st_size / (1024*1024):.2f} MB).")


def run(max_train: int = 1000):
    ensure_dirs()
    raw_dir = download_val2017()
    fit_files, test_files, train_files = create_manifests(raw_dir)
    preprocess_splits(raw_dir, fit_files, test_files, train_files, max_train=max_train)
    print("[data_prep] Phase 0 data preparation complete.")


if __name__ == "__main__":
    run()
