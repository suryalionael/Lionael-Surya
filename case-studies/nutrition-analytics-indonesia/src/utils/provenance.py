"""Audit trail helpers: never-overwrite raw file paths + a checksummed manifest.

Every ingestion run appends one JSON line to data/raw/_manifest.jsonl recording
exactly what was fetched, from where, when, and whether it passed validation.
This is what later phases (and a human reviewer) use to verify the data really
came from a real source at a real time.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.utils.config import MANIFEST_PATH, ROOT


def timestamped_path(base_dir: Path, dataset_slug: str, ext: str) -> Path:
    """Build a path that is never overwritten: data/raw/<slug>/<slug>_<UTC timestamp>.<ext>"""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_dir = base_dir / dataset_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{dataset_slug}_{stamp}.{ext}"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest_entry(
    *,
    dataset: str,
    dataset_version: str,
    source_name: str,
    source_url: str,
    file_path: Path,
    rows: int | None,
    columns: int | None,
    fetch_status: str,
    validation_status: str,
) -> dict:
    entry = {
        "dataset": dataset,
        "dataset_version": dataset_version,
        "source_name": source_name,
        "source_url": source_url,
        "file_path": str(file_path.relative_to(ROOT)) if file_path.is_relative_to(ROOT) else str(file_path),
        "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha256_of(file_path) if file_path.exists() else None,
        "rows": rows,
        "columns": columns,
        "file_size_bytes": file_path.stat().st_size if file_path.exists() else None,
        "fetch_status": fetch_status,
        "validation_status": validation_status,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []
    with open(MANIFEST_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def latest_entries() -> dict[str, dict]:
    """Most recent manifest entry per dataset slug."""
    latest: dict[str, dict] = {}
    for entry in read_manifest():
        latest[entry["dataset"]] = entry
    return latest
