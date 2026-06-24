"""Unit tests for src.utils.provenance: never-overwrite paths + manifest schema."""

import json
import time

from src.utils import provenance


def test_timestamped_path_never_collides(tmp_path):
    first = provenance.timestamped_path(tmp_path, "poverty", "csv")
    time.sleep(1.1)  # manifest timestamps are second-resolution
    second = provenance.timestamped_path(tmp_path, "poverty", "csv")
    assert first != second
    assert first.parent == second.parent == tmp_path / "poverty"


def test_sha256_of_is_deterministic(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello world")
    assert provenance.sha256_of(f) == provenance.sha256_of(f)
    assert len(provenance.sha256_of(f)) == 64


def test_write_manifest_entry_schema(tmp_path, monkeypatch):
    manifest_path = tmp_path / "_manifest.jsonl"
    monkeypatch.setattr(provenance, "MANIFEST_PATH", manifest_path)

    data_file = tmp_path / "poverty.csv"
    data_file.write_text("province,year,poverty_rate\nAceh,2024,12.3\n")

    entry = provenance.write_manifest_entry(
        dataset="poverty",
        dataset_version="2024",
        source_name="BPS",
        source_url="https://webapi.bps.go.id/",
        file_path=data_file,
        rows=1,
        columns=3,
        fetch_status="success",
        validation_status="passed",
    )

    assert manifest_path.exists()
    lines = manifest_path.read_text().strip().splitlines()
    assert len(lines) == 1
    on_disk = json.loads(lines[0])

    required_fields = {
        "dataset", "dataset_version", "source_name", "source_url", "file_path",
        "fetched_at_utc", "sha256", "rows", "columns", "file_size_bytes",
        "fetch_status", "validation_status",
    }
    assert required_fields <= on_disk.keys()
    assert on_disk["dataset"] == "poverty"
    assert on_disk["sha256"] == entry["sha256"]
    assert on_disk["sha256"] is not None


def test_latest_entries_keeps_most_recent_per_dataset(tmp_path, monkeypatch):
    manifest_path = tmp_path / "_manifest.jsonl"
    monkeypatch.setattr(provenance, "MANIFEST_PATH", manifest_path)

    data_file = tmp_path / "poverty.csv"
    data_file.write_text("x")

    provenance.write_manifest_entry(
        dataset="poverty", dataset_version="2023", source_name="BPS", source_url="u",
        file_path=data_file, rows=1, columns=1, fetch_status="success", validation_status="passed",
    )
    provenance.write_manifest_entry(
        dataset="poverty", dataset_version="2024", source_name="BPS", source_url="u",
        file_path=data_file, rows=2, columns=1, fetch_status="success", validation_status="passed",
    )

    latest = provenance.latest_entries()
    assert latest["poverty"]["dataset_version"] == "2024"
