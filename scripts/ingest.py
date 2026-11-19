"""
scripts/ingest.py - Ingest a returned zip package from Colab into results/v2/.

Usage:
    python scripts/ingest.py --package_zip path/to/returned.zip --task T2

Steps:
1. Unzip to incoming/T<task>/<timestamp>/
2. Read manifest.json from zip: verify SHA-256 checksums of included CSVs
3. Print row counts and column names for each CSV
4. Concatenate chunk CSVs (e.g. results_chunk0.csv, results_chunk1.csv) into one
5. De-duplicate by key columns: image_id, attack, strength, method, band, psnr_target
6. Append to results/v2/T<task>/master.csv (created if not exists)
7. Print summary: rows added, duplicates skipped
"""

import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KEY_COLUMNS = ["image_id", "attack", "strength", "method", "band", "psnr_target"]

# Root of project (this script lives in scripts/, so project root is one up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def sha256_of_file(path: Path) -> str:
    """Return hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_bytes(data: bytes) -> str:
    """Return hex SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest a Colab result zip package into results/v2/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--package_zip",
        required=True,
        metavar="PATH",
        help="Path to the returned .zip file from Colab.",
    )
    parser.add_argument(
        "--task",
        required=True,
        metavar="TX",
        help="Task identifier, e.g. T0, T1, T2.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        default=False,
        help="Preview actions without writing any files.",
    )
    parser.add_argument(
        "--skip_checksum",
        action="store_true",
        default=False,
        help="Skip SHA-256 checksum verification (for debugging).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Step 1: Unzip
# ---------------------------------------------------------------------------

def unzip_package(zip_path: Path, task: str, dry_run: bool) -> Path:
    """Unzip the package to incoming/T<task>/<timestamp>/."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest = PROJECT_ROOT / "incoming" / task / ts

    if dry_run:
        print(f"[DRY RUN] Would unzip {zip_path} → {dest}")
        return dest

    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
    print(f"✓ Unzipped {zip_path.name} → {dest}")
    return dest


# ---------------------------------------------------------------------------
# Step 2: Read and verify manifest
# ---------------------------------------------------------------------------

def load_manifest(extract_dir: Path, zip_path: Path, skip_checksum: bool) -> dict:
    """
    Read manifest.json from the extracted directory.
    Verify SHA-256 checksums of any listed CSV files.
    Returns the parsed manifest dict.
    """
    manifest_path = extract_dir / "manifest.json"
    if not manifest_path.exists():
        # Fallback: try reading from the zip directly
        with zipfile.ZipFile(zip_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                print("⚠ No manifest.json found in package — skipping verification.")
                return {}
            manifest_data = zf.read("manifest.json")
        manifest = json.loads(manifest_data.decode("utf-8"))
    else:
        with open(manifest_path) as f:
            manifest = json.load(f)

    print(f"\n── Manifest ──────────────────────────────")
    print(f"  Task:    {manifest.get('task', 'unknown')}")
    print(f"  Version: {manifest.get('version', 'unknown')}")
    print(f"  Files:   {manifest.get('files', [])}")

    if skip_checksum:
        print("  ⚠ Checksum verification SKIPPED (--skip_checksum)")
        return manifest

    checksums: dict = manifest.get("checksums", {})
    if not checksums:
        print("  ℹ No checksums in manifest — skipping checksum verification.")
        return manifest

    errors = []
    for filename, expected_digest in checksums.items():
        file_path = extract_dir / filename
        if not file_path.exists():
            errors.append(f"  ✗ {filename}: FILE MISSING")
            continue
        actual = sha256_of_file(file_path)
        if actual.lower() == expected_digest.lower():
            print(f"  ✓ {filename}: checksum OK")
        else:
            errors.append(
                f"  ✗ {filename}: CHECKSUM MISMATCH\n"
                f"      expected: {expected_digest}\n"
                f"      actual:   {actual}"
            )

    if errors:
        print("\n".join(errors))
        sys.exit(1)

    print("── End Manifest ──────────────────────────")
    return manifest


# ---------------------------------------------------------------------------
# Step 3: Discover and inspect CSVs
# ---------------------------------------------------------------------------

def discover_csvs(extract_dir: Path) -> list[Path]:
    """Return all CSV files in extract_dir, sorted."""
    csvs = sorted(extract_dir.glob("**/*.csv"))
    if not csvs:
        print("ℹ No CSV files found in package.")
    return csvs


def inspect_csv(path: Path) -> pd.DataFrame:
    """Load a CSV, print row count and columns, return DataFrame."""
    df = pd.read_csv(path)
    print(f"  {path.name:40s}  rows={len(df):6d}  cols={list(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# Step 4: Concatenate chunk CSVs
# ---------------------------------------------------------------------------

def concatenate_chunks(csv_paths: list[Path]) -> pd.DataFrame:
    """
    If multiple CSVs look like chunk files (results_chunk0.csv, results_chunk1.csv, …),
    concatenate them. Non-chunk files are also loaded and concatenated.
    Returns one combined DataFrame.
    """
    if not csv_paths:
        return pd.DataFrame()

    # Separate chunk files from non-chunk files
    chunk_pattern = re.compile(r".*chunk\d+.*\.csv$", re.IGNORECASE)
    chunk_files = [p for p in csv_paths if chunk_pattern.match(p.name)]
    other_files = [p for p in csv_paths if not chunk_pattern.match(p.name)]

    frames = []

    if chunk_files:
        # Sort by chunk index
        def chunk_index(p: Path) -> int:
            m = re.search(r"chunk(\d+)", p.name, re.IGNORECASE)
            return int(m.group(1)) if m else 0

        chunk_files_sorted = sorted(chunk_files, key=chunk_index)
        print(f"\n── Concatenating {len(chunk_files_sorted)} chunk file(s) ──")
        for p in chunk_files_sorted:
            df = inspect_csv(p)
            frames.append(df)

    if other_files:
        print(f"\n── Loading {len(other_files)} non-chunk CSV(s) ──")
        for p in other_files:
            df = inspect_csv(p)
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    print(f"\n  Combined: {len(combined)} rows")
    return combined


# ---------------------------------------------------------------------------
# Step 5–7: De-duplicate and append to master
# ---------------------------------------------------------------------------

def get_key_columns(df: pd.DataFrame) -> list[str]:
    """Return subset of KEY_COLUMNS that actually exist in df."""
    return [c for c in KEY_COLUMNS if c in df.columns]


def append_to_master(
    new_df: pd.DataFrame,
    task: str,
    dry_run: bool,
) -> None:
    """
    De-duplicate new_df against existing master.csv and append new rows.
    Prints summary: rows added vs. duplicates skipped.
    """
    master_dir = PROJECT_ROOT / "results" / "v2" / task
    master_path = master_dir / "master.csv"

    key_cols = get_key_columns(new_df)
    if not key_cols:
        print(
            "⚠ None of the key columns found in incoming data. "
            f"Key columns expected: {KEY_COLUMNS}"
        )

    # Load existing master if present
    if master_path.exists():
        existing_df = pd.read_csv(master_path)
        print(f"\n── Existing master: {len(existing_df)} rows ──")
    else:
        existing_df = pd.DataFrame()
        print("\n── No existing master.csv — will create fresh ──")

    # De-duplicate
    if key_cols and not existing_df.empty:
        # Build a set of existing keys for fast lookup
        existing_keys = set(
            existing_df[key_cols]
            .apply(lambda row: tuple(row), axis=1)
        )
        new_keys = new_df[key_cols].apply(lambda row: tuple(row), axis=1)
        is_new = ~new_keys.isin(existing_keys)
        rows_to_add = new_df[is_new]
        n_duplicates = int((~is_new).sum())
    elif existing_df.empty:
        rows_to_add = new_df
        n_duplicates = 0
    else:
        # No key cols: just append everything (no dedup possible)
        rows_to_add = new_df
        n_duplicates = 0

    n_added = len(rows_to_add)

    print(f"\n── Summary ───────────────────────────────")
    print(f"  Incoming rows:    {len(new_df)}")
    print(f"  Duplicates:       {n_duplicates}  (skipped)")
    print(f"  New rows to add:  {n_added}")

    if dry_run:
        print(f"  [DRY RUN] Would append {n_added} rows to {master_path}")
        return

    if n_added == 0:
        print("  Nothing to write — all rows already in master.")
        return

    master_dir.mkdir(parents=True, exist_ok=True)

    # Append (or create) master.csv
    combined = pd.concat([existing_df, rows_to_add], ignore_index=True)
    combined.to_csv(master_path, index=False)
    print(f"  ✓ master.csv updated → {master_path}")
    print(f"    Total rows now: {len(combined)}")
    print("── End ───────────────────────────────────")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    zip_path = Path(args.package_zip).resolve()
    if not zip_path.exists():
        print(f"✗ Package not found: {zip_path}", file=sys.stderr)
        sys.exit(1)
    if not zipfile.is_zipfile(zip_path):
        print(f"✗ Not a valid zip file: {zip_path}", file=sys.stderr)
        sys.exit(1)

    task = args.task.upper()
    print(f"\n╔══════════════════════════════════════════╗")
    print(f"║  ingest.py  package={zip_path.name}  task={task}")
    print(f"╚══════════════════════════════════════════╝\n")

    # Step 1: Unzip
    extract_dir = unzip_package(zip_path, task, dry_run=args.dry_run)

    # For dry_run we can't inspect files that weren't extracted
    if args.dry_run:
        print("[DRY RUN] Skipping manifest verification and CSV inspection.")
        print("[DRY RUN] Done.")
        return

    # Step 2: Verify manifest
    _manifest = load_manifest(extract_dir, zip_path, skip_checksum=args.skip_checksum)

    # Step 3: Discover and inspect CSVs
    print("\n── CSV Files Found ──────────────────────")
    csv_paths = discover_csvs(extract_dir)
    if not csv_paths:
        print("No CSVs to ingest. Exiting.")
        return

    # Step 4: Concatenate chunks
    combined_df = concatenate_chunks(csv_paths)
    if combined_df.empty:
        print("Combined DataFrame is empty. Nothing to ingest.")
        return

    # Step 5–7: De-duplicate + append to master
    append_to_master(combined_df, task, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
