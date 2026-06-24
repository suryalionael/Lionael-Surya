"""Generic data-contract validator. Loads a dataset's YAML contract and checks a
pandas DataFrame against it. Raises ContractViolation with full details on any
failure -- callers must treat that as a failed ingestion, never as a pass.
"""

from dataclasses import dataclass, field

import pandas as pd
import yaml

from src.utils.config import CONTRACTS_DIR


class ContractViolation(Exception):
    """Raised when a dataset fails its data contract. Carries every violation found."""

    def __init__(self, dataset: str, violations: list[str]):
        self.dataset = dataset
        self.violations = violations
        super().__init__(f"Dataset '{dataset}' failed validation:\n" + "\n".join(f"  - {v}" for v in violations))


@dataclass
class Contract:
    dataset: str
    required_columns: list[str]
    validation: dict = field(default_factory=dict)

    @classmethod
    def load(cls, dataset: str) -> "Contract":
        path = CONTRACTS_DIR / f"{dataset}.yml"
        if not path.exists():
            raise FileNotFoundError(f"No data contract found for dataset '{dataset}' at {path}")
        with open(path) as f:
            spec = yaml.safe_load(f)
        return cls(dataset=spec["dataset"], required_columns=spec["required_columns"], validation=spec.get("validation", {}))


def validate(df: pd.DataFrame, contract: Contract) -> None:
    violations: list[str] = []

    missing_cols = [c for c in contract.required_columns if c not in df.columns]
    if missing_cols:
        violations.append(f"missing required columns: {missing_cols}")

    if not missing_cols and len(df) == 0:
        violations.append("dataframe has zero rows")

    for column, rules in contract.validation.items():
        if column not in df.columns:
            continue  # already reported above

        if "unique_count_min" in rules or "unique_count_max" in rules:
            n_unique = df[column].nunique()
            if "unique_count_min" in rules and n_unique < rules["unique_count_min"]:
                violations.append(f"column '{column}' has {n_unique} unique values, below minimum {rules['unique_count_min']}")
            if "unique_count_max" in rules and n_unique > rules["unique_count_max"]:
                violations.append(f"column '{column}' has {n_unique} unique values, above maximum {rules['unique_count_max']}")

        if "min" in rules or "max" in rules:
            numeric = pd.to_numeric(df[column], errors="coerce")
            if numeric.isna().any() and not df[column].isna().any():
                violations.append(f"column '{column}' contains non-numeric values that could not be range-checked")
            if "min" in rules and (numeric < rules["min"]).any():
                violations.append(f"column '{column}' has values below minimum {rules['min']}")
            if "max" in rules and (numeric > rules["max"]).any():
                violations.append(f"column '{column}' has values above maximum {rules['max']}")

    if violations:
        raise ContractViolation(contract.dataset, violations)


def validate_dataset(df: pd.DataFrame, dataset: str) -> None:
    validate(df, Contract.load(dataset))
