import numpy as np

from src.evaluation.metrics import (
    bias,
    calculate_all_metrics,
    create_comparison_table,
    forecast_accuracy,
    mae,
    mape,
    rmse,
    smape,
    wape,
)


def test_mae():
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert mae(y_true, y_pred) == 0.0


def test_mae_with_error():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([2.0, 3.0, 4.0])
    assert mae(y_true, y_pred) == 1.0


def test_rmse():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([2.0, 3.0, 4.0])
    assert rmse(y_true, y_pred) == 1.0


def test_mape():
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([110.0, 220.0, 330.0])
    expected = np.mean([10.0 / 100, 20.0 / 200, 30.0 / 300]) * 100
    assert np.isclose(mape(y_true, y_pred), expected)


def test_mape_with_zeros():
    y_true = np.array([0.0, 100.0, 200.0])
    y_pred = np.array([0.0, 110.0, 220.0])
    result = mape(y_true, y_pred)
    assert result > 0


def test_smape():
    y_true = np.array([100.0, 200.0])
    y_pred = np.array([110.0, 180.0])
    expected = np.mean([2 * 10 / 210, 2 * 20 / 380]) * 100
    assert np.isclose(smape(y_true, y_pred), expected)


def test_wape():
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([110.0, 190.0, 310.0])
    expected = np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true)) * 100
    assert np.isclose(wape(y_true, y_pred), expected)


def test_bias():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([2.0, 3.0, 4.0])
    assert bias(y_true, y_pred) == 1.0


def test_forecast_accuracy():
    y_true = np.array([100.0, 200.0])
    y_pred = np.array([100.0, 200.0])
    assert forecast_accuracy(y_true, y_pred) == 100.0


def test_calculate_all_metrics():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    metrics = calculate_all_metrics(y_true, y_pred)
    assert all(v == 0.0 for k, v in metrics.items() if k not in ["forecast_accuracy", "bias"])
    assert metrics["forecast_accuracy"] == 100.0


def test_create_comparison_table():
    results = {"model_a": {"mae": 1.0, "rmse": 2.0}, "model_b": {"mae": 2.0, "rmse": 3.0}}
    table = create_comparison_table(results)
    assert list(table.index) == ["model_a", "model_b"]
    assert table.loc["model_a", "mae"] == 1.0
