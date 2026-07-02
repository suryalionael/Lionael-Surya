import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)


class Visualizer:
    def __init__(
        self,
        style: str = "seaborn-v0_8",
        dpi: int = 150,
        figsize: tuple = (12, 6),
        save_path: str = "reports/figures",
    ):
        self.style = style
        self.dpi = dpi
        self.figsize = figsize
        self.save_path = save_path
        plt.style.use(style)

    def save_figure(self, fig: plt.Figure, filename: str, path: str | None = None) -> str:
        path = path or self.save_path
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        filepath = save_path / filename
        fig.savefig(filepath, dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved figure: {filepath}")
        return str(filepath)

    def plot_sales_distribution(self, df: pd.DataFrame, column: str = "sales") -> plt.Figure:
        fig, axes = plt.subplots(1, 2, figsize=self.figsize)
        axes[0].hist(
            df[column].clip(0, df[column].quantile(0.99)), bins=50, edgecolor="black", alpha=0.7
        )
        axes[0].set_title("Sales Distribution (99th percentile capped)")
        axes[0].set_xlabel("Sales")
        axes[0].set_ylabel("Frequency")
        axes[1].boxplot(df[column].clip(0, df[column].quantile(0.99)).dropna())
        axes[1].set_title("Sales Boxplot")
        axes[1].set_ylabel("Sales")
        plt.tight_layout()
        return fig

    def plot_time_series(
        self, df: pd.DataFrame, date_col: str = "date", target: str = "sales"
    ) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)
        daily = df.groupby(date_col)[target].sum().reset_index()
        ax.plot(pd.to_datetime(daily[date_col]), daily[target], linewidth=1, alpha=0.8)
        ax.set_title("Daily Sales Time Series")
        ax.set_xlabel("Date")
        ax.set_ylabel("Total Sales")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_weekly_seasonality(
        self, df: pd.DataFrame, date_col: str = "date", target: str = "sales"
    ) -> plt.Figure:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df["day_of_week"] = df[date_col].dt.dayofweek
        fig, ax = plt.subplots(figsize=self.figsize)
        weekly = df.groupby("day_of_week")[target].mean()
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ax.bar(days, weekly.values, color="steelblue", alpha=0.7, edgecolor="black")
        ax.set_title("Average Sales by Day of Week")
        ax.set_xlabel("Day of Week")
        ax.set_ylabel("Average Sales")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_monthly_seasonality(
        self, df: pd.DataFrame, date_col: str = "date", target: str = "sales"
    ) -> plt.Figure:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df["month"] = df[date_col].dt.month
        fig, ax = plt.subplots(figsize=self.figsize)
        monthly = df.groupby("month")[target].mean()
        months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        ax.bar(months, monthly.values, color="coral", alpha=0.7, edgecolor="black")
        ax.set_title("Average Sales by Month")
        ax.set_xlabel("Month")
        ax.set_ylabel("Average Sales")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_actual_vs_forecast(
        self, y_true: np.ndarray, y_pred: np.ndarray, title: str = "Actual vs Forecast"
    ) -> plt.Figure:
        fig, axes = plt.subplots(1, 2, figsize=self.figsize)
        axes[0].scatter(y_true, y_pred, alpha=0.5, s=10)
        max_val = max(y_true.max(), y_pred.max())
        axes[0].plot([0, max_val], [0, max_val], "r--", linewidth=1)
        axes[0].set_title(title)
        axes[0].set_xlabel("Actual")
        axes[0].set_ylabel("Forecast")
        axes[0].grid(True, alpha=0.3)
        residuals = y_true - y_pred
        axes[1].hist(residuals, bins=50, edgecolor="black", alpha=0.7)
        axes[1].set_title("Residual Distribution")
        axes[1].set_xlabel("Residual")
        axes[1].set_ylabel("Frequency")
        axes[1].axvline(0, color="r", linestyle="--", linewidth=1)
        plt.tight_layout()
        return fig

    def plot_residuals(self, y_true: np.ndarray, y_pred: np.ndarray) -> plt.Figure:
        residuals = y_true - y_pred
        fig, axes = plt.subplots(1, 2, figsize=self.figsize)
        axes[0].scatter(y_pred, residuals, alpha=0.5, s=10)
        axes[0].axhline(0, color="r", linestyle="--", linewidth=1)
        axes[0].set_title("Residuals vs Predicted")
        axes[0].set_xlabel("Predicted")
        axes[0].set_ylabel("Residual")
        axes[0].grid(True, alpha=0.3)
        axes[1].plot(residuals, alpha=0.7)
        axes[1].axhline(0, color="r", linestyle="--", linewidth=1)
        axes[1].set_title("Residual Sequence")
        axes[1].set_xlabel("Sample")
        axes[1].set_ylabel("Residual")
        axes[1].grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_forecast_comparison(
        self,
        y_true: np.ndarray,
        forecasts: dict[str, np.ndarray],
        title: str = "Forecast Comparison",
    ) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)
        x = np.arange(len(y_true))
        ax.plot(x, y_true, label="Actual", linewidth=2, color="black")
        colors = plt.cm.tab10(np.linspace(0, 1, len(forecasts)))
        for (name, pred), color in zip(forecasts.items(), colors, strict=False):
            ax.plot(x[: len(pred)], pred, label=name, linewidth=1.5, alpha=0.8, color=color)
        ax.set_title(title)
        ax.set_xlabel("Time")
        ax.set_ylabel("Sales")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_feature_importance(self, importance_df: pd.DataFrame, top_n: int = 20) -> plt.Figure:
        df = importance_df.head(top_n)
        fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.3)))
        ax.barh(range(len(df)), df["importance"].values, color="steelblue", alpha=0.7)
        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df["feature"].values)
        ax.set_title(f"Top {top_n} Feature Importance")
        ax.set_xlabel("Importance")
        ax.invert_yaxis()
        plt.tight_layout()
        return fig

    def plot_error_distribution(self, errors: dict[str, np.ndarray]) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)
        for name, err in errors.items():
            ax.hist(err, bins=50, alpha=0.5, label=name)
        ax.set_title("Error Distribution by Model")
        ax.set_xlabel("Error (Actual - Predicted)")
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_heatmap(self, df: pd.DataFrame, title: str = "Correlation Heatmap") -> plt.Figure:
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 30:
            numeric_df = numeric_df.iloc[:, :30]
        fig, ax = plt.subplots(figsize=(14, 10))
        sns.heatmap(numeric_df.corr(), annot=False, cmap="RdBu", center=0, ax=ax, linewidths=0.5)
        ax.set_title(title)
        plt.tight_layout()
        return fig

    def plot_promotion_analysis(self, df: pd.DataFrame, target: str = "sales") -> plt.Figure:
        fig, axes = plt.subplots(1, 2, figsize=self.figsize)
        if "is_promotion" in df.columns:
            df = df.copy()
            df["promo_binary"] = (df["is_promotion"] > 0).astype(int)
            promo_stats = df.groupby("promo_binary")[target].mean()
            axes[0].bar(
                ["No Promotion", "Promotion"],
                promo_stats.reindex([0, 1]).fillna(0).values,
                color=["steelblue", "coral"],
                alpha=0.7,
            )
            axes[0].set_title("Average Sales: Promotion vs Non-Promotion")
            axes[0].set_ylabel("Average Sales")
            axes[0].grid(True, alpha=0.3)
        if "is_holiday" in df.columns:
            holiday_stats = df.groupby("is_holiday")[target].mean()
            axes[1].bar(
                ["No Holiday", "Holiday"],
                holiday_stats.reindex([0, 1]).fillna(0).values,
                color=["steelblue", "coral"],
                alpha=0.7,
            )
            axes[1].set_title("Average Sales: Holiday vs Non-Holiday")
            axes[1].set_ylabel("Average Sales")
            axes[1].grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_category_analysis(
        self, df: pd.DataFrame, category_col: str, target: str = "sales"
    ) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)
        cat_stats = df.groupby(category_col)[target].mean().sort_values(ascending=False).head(20)
        ax.bar(range(len(cat_stats)), cat_stats.values, color="teal", alpha=0.7)
        ax.set_xticks(range(len(cat_stats)))
        ax.set_xticklabels(cat_stats.index, rotation=45, ha="right")
        ax.set_title(f"Average Sales by {category_col}")
        ax.set_xlabel(category_col)
        ax.set_ylabel("Average Sales")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_cv_folds(self, folds_info: list[dict]) -> plt.Figure:
        import matplotlib.patches as mpatches

        fig, ax = plt.subplots(figsize=(12, len(folds_info) * 0.6 + 2))
        for i, fold in enumerate(folds_info):
            ax.barh(i, fold["n_train"], left=0, color="steelblue", alpha=0.7)
            ax.barh(i, fold["n_test"], left=fold["n_train"], color="coral", alpha=0.7)
        ax.set_yticks(range(len(folds_info)))
        ax.set_yticklabels([f"Fold {f['fold']+1}" for f in folds_info])
        ax.set_xlabel("Days")
        ax.set_title("Walk-Forward Validation Folds")
        train_patch = mpatches.Patch(color="steelblue", label="Training")
        test_patch = mpatches.Patch(color="coral", label="Test")
        ax.legend(handles=[train_patch, test_patch])
        plt.tight_layout()
        return fig

    def plot_prediction_intervals(
        self,
        dates: pd.Series | np.ndarray,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        lower: np.ndarray | None = None,
        upper: np.ndarray | None = None,
        title: str = "Forecast with Prediction Intervals",
    ) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)
        ax.plot(dates, y_true, label="Actual", color="black", linewidth=1.5)
        ax.plot(dates, y_pred, label="Forecast", color="blue", linewidth=1.5)
        if lower is not None and upper is not None:
            ax.fill_between(
                dates, lower, upper, alpha=0.2, color="blue", label="Uncertainty Interval"
            )
        ax.set_title(title)
        ax.set_xlabel("Date")
        ax.set_ylabel("Sales")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_rolling_forecast(
        self,
        dates: np.ndarray,
        actual: np.ndarray,
        predictions: list[np.ndarray],
        model_names: list[str],
    ) -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.figsize)
        ax.plot(dates, actual, label="Actual", color="black", linewidth=1.5)
        colors = plt.cm.tab10(np.linspace(0, 1, len(predictions)))
        for pred, name, color in zip(predictions, model_names, colors, strict=False):
            ax.plot(dates[: len(pred)], pred, label=name, linewidth=1, alpha=0.8, color=color)
        ax.set_title("Rolling Forecast Comparison")
        ax.set_xlabel("Date")
        ax.set_ylabel("Sales")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig
