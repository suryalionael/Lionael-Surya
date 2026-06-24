"""Unit tests for src.validation.contracts. Uses small in-memory fixture DataFrames --
these are test fixtures exercising validation logic, not project datasets, so they are
not subject to the project's real-data-only rule (which governs actual ingested data).
"""

import pandas as pd
import pytest

from src.validation.contracts import Contract, ContractViolation, validate

POVERTY_CONTRACT = Contract(
    dataset="poverty",
    required_columns=["province", "year", "poverty_rate"],
    validation={
        "province": {"unique_count_min": 3, "unique_count_max": 5},
        "poverty_rate": {"min": 0, "max": 100},
    },
)


def _df(rows):
    return pd.DataFrame(rows)


def test_valid_dataframe_passes():
    df = _df(
        [
            {"province": "Aceh", "year": 2024, "poverty_rate": 12.3},
            {"province": "Bali", "year": 2024, "poverty_rate": 4.1},
            {"province": "Jambi", "year": 2024, "poverty_rate": 7.6},
        ]
    )
    validate(df, POVERTY_CONTRACT)  # should not raise


def test_missing_required_column_fails():
    df = _df([{"province": "Aceh", "year": 2024}])
    with pytest.raises(ContractViolation, match="missing required columns"):
        validate(df, POVERTY_CONTRACT)


def test_empty_dataframe_fails():
    df = pd.DataFrame(columns=["province", "year", "poverty_rate"])
    with pytest.raises(ContractViolation, match="zero rows"):
        validate(df, POVERTY_CONTRACT)


def test_value_out_of_range_fails():
    df = _df(
        [
            {"province": "Aceh", "year": 2024, "poverty_rate": 150},
            {"province": "Bali", "year": 2024, "poverty_rate": 4.1},
            {"province": "Jambi", "year": 2024, "poverty_rate": 7.6},
        ]
    )
    with pytest.raises(ContractViolation, match="above maximum"):
        validate(df, POVERTY_CONTRACT)


def test_too_few_unique_provinces_fails():
    df = _df(
        [
            {"province": "Aceh", "year": 2024, "poverty_rate": 12.3},
            {"province": "Aceh", "year": 2023, "poverty_rate": 13.0},
        ]
    )
    with pytest.raises(ContractViolation, match="below minimum"):
        validate(df, POVERTY_CONTRACT)


def test_contract_load_missing_file_raises(tmp_path, monkeypatch):
    import src.validation.contracts as contracts_module

    monkeypatch.setattr(contracts_module, "CONTRACTS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        Contract.load("nonexistent")
