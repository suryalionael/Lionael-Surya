import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denominator = np.abs(y_true) + np.abs(y_pred)
    mask = denominator != 0
    if not mask.any():
        return 0.0
    return float(np.mean(2.0 * np.abs(y_true[mask] - y_pred[mask]) / denominator[mask]) * 100)


def wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    total_actual = np.sum(np.abs(y_true))
    if total_actual == 0:
        return 0.0
    return float(np.sum(np.abs(y_true - y_pred)) / total_actual * 100)


def bias(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(y_pred - y_true))


def forecast_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mape_val = mape(y_true, y_pred)
    return float(max(0, 100 - mape_val))


METRIC_FUNCTIONS = {
    "mae": mae,
    "rmse": rmse,
    "mape": mape,
    "smape": smape,
    "wape": wape,
    "bias": bias,
    "forecast_accuracy": forecast_accuracy,
}


def calculate_all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {name: func(y_true, y_pred) for name, func in METRIC_FUNCTIONS.items()}


def calculate_metrics_by_group(
    df: pd.DataFrame,
    y_true_col: str,
    y_pred_col: str,
    group_col: str,
) -> pd.DataFrame:
    results = []
    for group, group_df in df.groupby(group_col, observed=True):
        metrics = calculate_all_metrics(group_df[y_true_col].values, group_df[y_pred_col].values)
        metrics["group"] = group
        results.append(metrics)
    return pd.DataFrame(results)


def create_comparison_table(
    results: dict[str, dict[str, float]], metrics: list[str] | None = None
) -> pd.DataFrame:
    if metrics is None:
        metrics = list(METRIC_FUNCTIONS.keys())
    rows = []
    for model_name, model_metrics in results.items():
        row = {"model": model_name}
        for m in metrics:
            row[m] = model_metrics.get(m, float("nan"))
        rows.append(row)
    return pd.DataFrame(rows).set_index("model")
