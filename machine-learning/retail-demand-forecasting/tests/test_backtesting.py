import pandas as pd

from src.evaluation.backtesting import WalkForwardValidator


def test_split():
    dates = pd.date_range("2023-01-01", periods=500, freq="D")
    df = pd.DataFrame({"date": dates, "sales": range(500)})
    wfv = WalkForwardValidator(n_folds=3, initial_days=100, horizon_days=20, step_days=30)
    folds = wfv.split(df, "date")
    assert len(folds) == 3
    for fold in folds:
        assert "fold" in fold
        assert "train_dates" in fold
        assert "test_dates" in fold
        assert len(fold["test_dates"]) <= 20


def test_split_dataframe():
    dates = pd.date_range("2023-01-01", periods=200, freq="D")
    df = pd.DataFrame({"date": dates, "sales": range(200), "store": [1] * 200})
    wfv = WalkForwardValidator(n_folds=2, initial_days=50, horizon_days=10, step_days=30)
    splits = wfv.split_dataframe(df, "date")
    assert len(splits) == 2
    for train, test, _info in splits:
        assert len(train) > 0
        assert len(test) > 0


def test_plot_folds():
    dates = pd.date_range("2023-01-01", periods=365, freq="D")
    df = pd.DataFrame({"date": dates, "sales": range(365)})
    wfv = WalkForwardValidator(n_folds=3, initial_days=100, horizon_days=20, step_days=30)
    fig = wfv.plot_folds(df, "date")
    assert fig is not None
