"""Min-max scales each indicator column to [0, 1] -- "0 = least vulnerable province
observed, 1 = most" once columns are already directionality-aligned
(src/features/directionality.py). Scaling statistics (min/max) are fit only on
present values; nulls are never filled in order to compute them, and stay null in
the output.
"""

import pandas as pd


def min_max_scale(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, dict]:
    """Returns (scaled_df, diagnostics). diagnostics records the real min/max used per
    column, for transparency/reporting -- never hidden inside the transformation."""
    df = df.copy()
    diagnostics = {}

    for col in columns:
        values = df[col].dropna()
        col_min, col_max = values.min(), values.max()
        diagnostics[col] = {"min": col_min, "max": col_max, "n_present": len(values), "n_missing": int(df[col].isna().sum())}

        if col_max == col_min:
            raise ValueError(f"Column '{col}' has zero variance (min == max == {col_min}) -- cannot min-max scale.")

        df[col] = (df[col] - col_min) / (col_max - col_min)

    return df, diagnostics
