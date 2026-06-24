"""Unit tests for src.reference.lookup -- province name normalization. Uses a small
fixture CSV instead of the real generated province_lookup.csv, so this runs offline
without needing a BPS_API_KEY."""

import csv

import pytest

from src.reference.lookup import load_variant_map, normalize


@pytest.fixture
def lookup_csv(tmp_path):
    path = tmp_path / "province_lookup.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["canonical_name", "bps_code", "variant"])
        writer.writeheader()
        writer.writerows(
            [
                {"canonical_name": "DKI Jakarta", "bps_code": "31", "variant": "DKI Jakarta"},
                {"canonical_name": "DKI Jakarta", "bps_code": "31", "variant": "Jakarta"},
                {"canonical_name": "DKI Jakarta", "bps_code": "31", "variant": "Provinsi DKI Jakarta"},
                {"canonical_name": "DI Yogyakarta", "bps_code": "34", "variant": "DI Yogyakarta"},
                {"canonical_name": "DI Yogyakarta", "bps_code": "34", "variant": "Daerah Istimewa Yogyakarta"},
                {"canonical_name": "DI Yogyakarta", "bps_code": "34", "variant": "Yogyakarta"},
            ]
        )
    return path


def test_load_variant_map_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_variant_map(tmp_path / "does_not_exist.csv")


def test_normalize_known_variants(lookup_csv):
    variant_map = load_variant_map(lookup_csv)
    assert normalize("Jakarta", variant_map) == "DKI Jakarta"
    assert normalize("Provinsi DKI Jakarta", variant_map) == "DKI Jakarta"
    assert normalize("Daerah Istimewa Yogyakarta", variant_map) == "DI Yogyakarta"


def test_normalize_is_case_and_whitespace_insensitive(lookup_csv):
    variant_map = load_variant_map(lookup_csv)
    assert normalize("  jakarta  ", variant_map) == "DKI Jakarta"
    assert normalize("YOGYAKARTA", variant_map) == "DI Yogyakarta"


def test_normalize_unknown_variant_raises(lookup_csv):
    variant_map = load_variant_map(lookup_csv)
    with pytest.raises(KeyError, match="Unrecognized province"):
        normalize("Atlantis", variant_map)
