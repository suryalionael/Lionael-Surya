import math
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.config import CONFIG


EPSILON = 1e-6


def _to_numeric(series: pd.Series) -> pd.Series:
    """Converts a feature series to numeric values for drift checks."""
    return pd.to_numeric(series, errors="coerce")


def _population_stability_index(expected: np.ndarray, actual: np.ndarray) -> float:
    expected = np.clip(expected.astype(float), EPSILON, None)
    actual = np.clip(actual.astype(float), EPSILON, None)
    return float(np.sum((actual - expected) * np.log(actual / expected)))


def _numeric_bin_edges(values: pd.Series, n_bins: int) -> Optional[List[float]]:
    clean = _to_numeric(values).dropna()
    if clean.empty or clean.nunique() < 2:
        return None

    quantiles = np.linspace(0, 1, n_bins + 1)
    edges = np.unique(clean.quantile(quantiles).to_numpy(dtype=float))
    if len(edges) < 3:
        edges = np.linspace(float(clean.min()), float(clean.max()), n_bins + 1)
        edges = np.unique(edges)

    if len(edges) < 3:
        return None

    return [float(edge) for edge in edges]


def _numeric_distribution(values: pd.Series, edges: List[float]) -> List[float]:
    clean = _to_numeric(values)
    open_edges = [-math.inf] + [float(edge) for edge in edges[1:-1]] + [math.inf]
    binned = pd.cut(clean, bins=open_edges, include_lowest=True)
    counts = binned.value_counts(sort=False).to_numpy(dtype=float)
    denominator = counts.sum()
    if denominator == 0:
        return [0.0 for _ in counts]
    return [float(count / denominator) for count in counts]


def _categorical_distribution(values: pd.Series) -> Dict[str, float]:
    normalized = values.fillna("__MISSING__").astype(str)
    proportions = normalized.value_counts(normalize=True)
    return {str(category): float(share) for category, share in proportions.items()}


def build_drift_reference(
    df: pd.DataFrame, n_bins: Optional[int] = None
) -> Dict[str, Any]:
    """
    Builds a compact reference profile used to monitor production data drift.

    Numeric features are profiled with quantile bins and categorical features
    are profiled by category share. The resulting dictionary is JSON-safe.
    """
    if n_bins is None:
        n_bins = CONFIG.get("drift", {}).get("n_bins", 10)

    reference = {
        "row_count": int(len(df)),
        "numeric_features": {},
        "categorical_features": {},
    }

    for feature in CONFIG["data"]["numerical_features"]:
        if feature not in df.columns:
            continue
        edges = _numeric_bin_edges(df[feature], n_bins)
        if edges is None:
            continue
        reference["numeric_features"][feature] = {
            "bin_edges": edges,
            "distribution": _numeric_distribution(df[feature], edges),
        }

    for feature in CONFIG["data"]["categorical_features"]:
        if feature not in df.columns:
            continue
        reference["categorical_features"][feature] = {
            "distribution": _categorical_distribution(df[feature])
        }

    return reference


def evaluate_drift(
    reference: Dict[str, Any], current_df: pd.DataFrame
) -> Dict[str, Any]:
    """Compares a current batch against a stored drift reference profile."""
    warning_threshold = CONFIG.get("drift", {}).get("warning_psi_threshold", 0.1)
    drift_threshold = CONFIG.get("drift", {}).get("drift_psi_threshold", 0.25)

    features = []

    for feature, profile in reference.get("numeric_features", {}).items():
        if feature not in current_df.columns:
            features.append(
                {
                    "feature": feature,
                    "type": "numeric",
                    "status": "missing",
                    "psi": None,
                    "message": "Feature is missing from current batch.",
                }
            )
            continue

        expected = np.asarray(profile["distribution"], dtype=float)
        actual = np.asarray(
            _numeric_distribution(current_df[feature], profile["bin_edges"]),
            dtype=float,
        )
        psi = _population_stability_index(expected, actual)
        features.append(
            _feature_result(feature, "numeric", psi, warning_threshold, drift_threshold)
        )

    for feature, profile in reference.get("categorical_features", {}).items():
        if feature not in current_df.columns:
            features.append(
                {
                    "feature": feature,
                    "type": "categorical",
                    "status": "missing",
                    "psi": None,
                    "message": "Feature is missing from current batch.",
                }
            )
            continue

        reference_dist = profile["distribution"]
        current_dist = _categorical_distribution(current_df[feature])
        categories = sorted(set(reference_dist) | set(current_dist))
        expected = np.asarray(
            [reference_dist.get(category, 0.0) for category in categories]
        )
        actual = np.asarray(
            [current_dist.get(category, 0.0) for category in categories]
        )
        psi = _population_stability_index(expected, actual)
        result = _feature_result(
            feature, "categorical", psi, warning_threshold, drift_threshold
        )
        unseen_categories = sorted(set(current_dist) - set(reference_dist))
        if unseen_categories:
            result["unseen_categories"] = unseen_categories
        features.append(result)

    drifted_features = [
        item["feature"] for item in features if item.get("status") == "drift"
    ]
    warning_features = [
        item["feature"] for item in features if item.get("status") == "warning"
    ]
    max_psi = max(
        [item["psi"] for item in features if item.get("psi") is not None],
        default=0.0,
    )

    return {
        "row_count": int(len(current_df)),
        "reference_row_count": int(reference.get("row_count", 0)),
        "drift_detected": bool(drifted_features),
        "max_psi": round(float(max_psi), 6),
        "drifted_features": drifted_features,
        "warning_features": warning_features,
        "features": features,
        "thresholds": {
            "warning_psi": warning_threshold,
            "drift_psi": drift_threshold,
        },
    }


def _feature_result(
    feature: str,
    feature_type: str,
    psi: float,
    warning_threshold: float,
    drift_threshold: float,
) -> Dict[str, Any]:
    if psi >= drift_threshold:
        status = "drift"
    elif psi >= warning_threshold:
        status = "warning"
    else:
        status = "stable"

    return {
        "feature": feature,
        "type": feature_type,
        "status": status,
        "psi": round(float(psi), 6),
    }
