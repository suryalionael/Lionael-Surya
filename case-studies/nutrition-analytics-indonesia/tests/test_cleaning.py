"""Unit tests for src.cleaning.standardize and src.cleaning.merge. Uses small
in-memory fixtures (not real project data) to exercise the cleaning logic itself."""

import pandas as pd
import pytest

from src.cleaning import merge as merge_module
from src.cleaning import standardize as standardize_module


@pytest.fixture
def fixture_lookup(monkeypatch):
    # load_variant_map's path default is bound at import time, so monkeypatching the
    # module-level PROVINCE_LOOKUP_PATH afterward would have no effect; patch the
    # function standardize.py actually calls instead.
    variant_map = {"aceh": "Aceh", "bali": "Bali"}
    monkeypatch.setattr(standardize_module, "load_variant_map", lambda: variant_map)


def test_standardize_drops_non_province_rows(monkeypatch, fixture_lookup, tmp_path):
    raw = pd.DataFrame(
        [
            {"province": "ACEH", "year": 2024, "poverty_rate": 12.0},
            {"province": "BALI", "year": 2024, "poverty_rate": 3.0},
            {"province": "INDONESIA", "year": 2024, "poverty_rate": 9.0},
        ]
    )
    raw_path = tmp_path / "poverty.csv"
    raw.to_csv(raw_path, index=False)
    monkeypatch.setattr(standardize_module, "latest_entries", lambda: {"poverty": {"file_path": str(raw_path)}})

    df, report = standardize_module.standardize_dataset("poverty", ["poverty_rate"])

    assert report.rows_in == 3
    assert report.rows_dropped_non_province == 1
    assert sorted(df["province"]) == ["Aceh", "Bali"]


def test_standardize_detects_inconsistent_duplicate_keys(monkeypatch, fixture_lookup, tmp_path):
    raw = pd.DataFrame(
        [
            {"province": "Aceh", "year": 2024, "poverty_rate": 12.0},
            {"province": "Aceh", "year": 2024, "poverty_rate": 99.0},  # same key, different value -- inconsistent
        ]
    )
    raw_path = tmp_path / "poverty.csv"
    raw.to_csv(raw_path, index=False)
    monkeypatch.setattr(standardize_module, "latest_entries", lambda: {"poverty": {"file_path": str(raw_path)}})

    _, report = standardize_module.standardize_dataset("poverty", ["poverty_rate"])

    assert report.inconsistent_keys == [("Aceh", 2024)]


def test_standardize_drops_exact_duplicates(monkeypatch, fixture_lookup, tmp_path):
    raw = pd.DataFrame(
        [
            {"province": "Aceh", "year": 2024, "poverty_rate": 12.0},
            {"province": "Aceh", "year": 2024, "poverty_rate": 12.0},  # exact duplicate
        ]
    )
    raw_path = tmp_path / "poverty.csv"
    raw.to_csv(raw_path, index=False)
    monkeypatch.setattr(standardize_module, "latest_entries", lambda: {"poverty": {"file_path": str(raw_path)}})

    df, report = standardize_module.standardize_dataset("poverty", ["poverty_rate"])

    assert report.rows_dropped_exact_duplicate == 1
    assert len(df) == 1


def test_validate_merged_table_rejects_duplicate_province():
    df = pd.DataFrame(
        {
            "province": ["Aceh", "Aceh"],
            "poverty_rate": [12.0, 12.0],
            "ipm": [70.0, 70.0],
            "population": [100.0, 100.0],
            "participation_rate": [99.0, 99.0],
            "expenditure_per_capita": [10000, 10000],
            "stunting_rate": [20.0, 20.0],
        }
    )
    with pytest.raises(ValueError, match="duplicate province rows"):
        merge_module.validate_merged_table(df)


def test_validate_merged_table_rejects_out_of_range_value():
    df = pd.DataFrame(
        {
            "province": [f"P{i}" for i in range(38)],
            "poverty_rate": [150.0] + [10.0] * 37,  # out of [0, 100]
            "ipm": [70.0] * 38,
            "population": [100.0] * 38,
            "participation_rate": [99.0] * 38,
            "expenditure_per_capita": [10000] * 38,
            "stunting_rate": [20.0] * 38,
        }
    )
    with pytest.raises(ValueError, match="poverty_rate"):
        merge_module.validate_merged_table(df)


def test_validate_merged_table_accepts_valid_table():
    df = pd.DataFrame(
        {
            "province": [f"P{i}" for i in range(38)],
            "poverty_rate": [10.0] * 38,
            "ipm": [70.0] * 38,
            "population": [100.0] * 38,
            "participation_rate": [99.0] * 38,
            "expenditure_per_capita": [10000] * 38,
            "stunting_rate": [20.0] * 38,
        }
    )
    merge_module.validate_merged_table(df)  # should not raise
