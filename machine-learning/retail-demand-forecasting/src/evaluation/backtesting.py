import logging
from collections.abc import Callable

import pandas as pd

logger = logging.getLogger(__name__)


class WalkForwardValidator:
    def __init__(
        self,
        n_folds: int = 5,
        initial_days: int = 365,
        horizon_days: int = 30,
        step_days: int = 30,
    ):
        self.n_folds = n_folds
        self.initial_days = initial_days
        self.horizon_days = horizon_days
        self.step_days = step_days

    def split(self, df: pd.DataFrame, date_col: str = "date") -> list[dict]:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        dates = sorted(df[date_col].unique())
        folds = []
        start_idx = 0
        for fold_idx in range(self.n_folds):
            train_end = start_idx + self.initial_days + fold_idx * self.step_days
            if train_end >= len(dates):
                break
            test_start = train_end
            test_end = min(test_start + self.horizon_days, len(dates))
            train_dates = dates[:train_end]
            test_dates = dates[test_start:test_end]
            if len(test_dates) == 0:
                break
            folds.append(
                {
                    "fold": fold_idx,
                    "train_start": train_dates[0],
                    "train_end": train_dates[-1],
                    "test_start": test_dates[0],
                    "test_end": test_dates[-1],
                    "train_dates": train_dates,
                    "test_dates": test_dates,
                    "n_train": len(train_dates),
                    "n_test": len(test_dates),
                }
            )
        logger.info(f"Created {len(folds)} walk-forward folds")
        return folds

    def split_dataframe(
        self, df: pd.DataFrame, date_col: str = "date"
    ) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
        folds = self.split(df, date_col)
        splits = []
        for fold in folds:
            train = df[df[date_col].isin(fold["train_dates"])].copy()
            test = df[df[date_col].isin(fold["test_dates"])].copy()
            splits.append((train, test, fold))
        return splits

    def validate(
        self,
        df: pd.DataFrame,
        model_class: type,
        model_params: dict | None = None,
        feature_engineering_fn: Callable | None = None,
        group_cols: list[str] | None = None,
        target: str = "sales",
        date_col: str = "date",
    ) -> tuple[pd.DataFrame, list]:
        if group_cols is None:
            group_cols = ["item_nbr"]
        splits = self.split_dataframe(df, date_col)
        all_results = []
        all_predictions = []
        for train_df, test_df, fold_info in splits:
            if feature_engineering_fn:
                train_df = feature_engineering_fn(train_df, is_train=True)
                test_df = feature_engineering_fn(test_df, is_train=False)
            model = model_class(**(model_params or {}))
            if hasattr(model, "fit") and hasattr(model, "predict"):
                if "X" in model.fit.__code__.co_varnames:
                    feature_cols = [
                        c for c in train_df.columns if c not in [target, date_col] + group_cols
                    ]
                    X_train = train_df[feature_cols].dropna()
                    y_train = X_train[target]
                    model.fit(X_train.drop(columns=[target]), y_train)
                    X_test = test_df[feature_cols].dropna()
                    preds = model.predict(X_test.drop(columns=[target]))
                    fold_preds = X_test.copy()
                    fold_preds["prediction"] = preds
                else:
                    model.fit(train_df, date_col=date_col, target=target)
                    preds = model.predict_with_series(test_df, date_col=date_col)
                    fold_preds = test_df.copy()
                    fold_preds["prediction"] = preds
            else:
                model.fit(train_df, date_col=date_col, target=target)
                preds = model.predict_with_series(test_df)
                fold_preds = test_df.copy()
                fold_preds["prediction"] = preds
            from src.evaluation.metrics import calculate_all_metrics

            valid = fold_preds.dropna(subset=["prediction", target])
            if len(valid) > 0:
                metrics = calculate_all_metrics(valid[target].values, valid["prediction"].values)
                metrics["fold"] = fold_info["fold"]
                metrics["train_start"] = fold_info["train_start"]
                metrics["train_end"] = fold_info["train_end"]
                metrics["test_start"] = fold_info["test_start"]
                metrics["test_end"] = fold_info["test_end"]
                all_results.append(metrics)
            all_predictions.append(fold_preds)
        return pd.DataFrame(all_results), all_predictions

    def plot_folds(self, df: pd.DataFrame, date_col: str = "date") -> None:
        import matplotlib.patches as mpatches
        import matplotlib.pyplot as plt

        folds = self.split(df, date_col)
        fig, ax = plt.subplots(figsize=(12, len(folds) * 0.6 + 2))
        for i, fold in enumerate(folds):
            ax.barh(i, fold["n_train"], left=0, color="steelblue", alpha=0.7)
            ax.barh(
                i,
                fold["n_test"],
                left=fold["n_train"],
                color="coral",
                alpha=0.7,
            )
            ax.text(fold["n_train"] / 2, i, "Train", ha="center", va="center", fontsize=9)
            ax.text(
                fold["n_train"] + fold["n_test"] / 2,
                i,
                "Test",
                ha="center",
                va="center",
                fontsize=9,
            )
        ax.set_yticks(range(len(folds)))
        ax.set_yticklabels([f"Fold {f['fold']+1}" for f in folds])
        ax.set_xlabel("Days")
        ax.set_title("Walk-Forward Validation Folds")
        train_patch = mpatches.Patch(color="steelblue", label="Training")
        test_patch = mpatches.Patch(color="coral", label="Test")
        ax.legend(handles=[train_patch, test_patch])
        plt.tight_layout()
        return fig
