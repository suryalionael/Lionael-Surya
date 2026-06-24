"""Aligns every NPI input indicator to a consistent "higher = more vulnerable"
direction, driven entirely by config/indicator_directionality.yml -- never a
hardcoded per-indicator assumption in code.
"""

from pathlib import Path

import pandas as pd
import yaml

from src.utils.config import CONFIG_DIR

DIRECTIONALITY_CONFIG_PATH = CONFIG_DIR / "indicator_directionality.yml"


def load_directionality_config(path: Path = DIRECTIONALITY_CONFIG_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def align_to_higher_is_worse(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """Returns a copy of df with every configured indicator column flipped so that
    a higher value always means more vulnerable. df may freely contain other,
    non-indicator columns (province, year, stunting_rate, population, ...) that
    aren't in the config -- those are left untouched. Raises if the config names an
    indicator that ISN'T present in df, which would otherwise silently mean that
    indicator's direction-flip never happened."""
    config = config if config is not None else load_directionality_config()
    df = df.copy()

    candidate_columns = set(config.keys()) & set(df.columns)
    unmapped = [col for col in config if col not in df.columns]
    if unmapped:
        raise KeyError(f"Indicator(s) in config but not in input data: {unmapped}")

    for col in candidate_columns:
        directionality = config[col]["directionality"]
        if directionality == "higher_is_better":
            df[col] = -df[col]
        elif directionality != "higher_is_worse":
            raise ValueError(f"Unknown directionality '{directionality}' for indicator '{col}'")

    return df


def dimension_for(indicator: str, config: dict | None = None) -> str:
    config = config if config is not None else load_directionality_config()
    if indicator not in config:
        raise KeyError(f"No dimension mapping for indicator '{indicator}' in {DIRECTIONALITY_CONFIG_PATH}")
    return config[indicator]["dimension"]
