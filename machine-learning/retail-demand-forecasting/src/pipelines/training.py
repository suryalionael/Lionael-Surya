import logging
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd

from src.data.aggregation import ForecastingDatasetBuilder
from src.data.cleaning import DataCleaner
from src.data.ingestion import DataIngestion
from src.data.validation import DataValidation
from src.evaluation.backtesting import WalkForwardValidator
from src.evaluation.metrics import calculate_all_metrics, create_comparison_table
from src.features.engineering import FeatureEngineer
from src.forecasting.naive_model import NaiveSeasonalForecaster
from src.forecasting.prophet_model import ProphetForecaster
from src.forecasting.xgboost_model import XGBoostForecaster
from src.visualization.plots import Visualizer

logger = logging.getLogger(__name__)


class TrainingPipeline:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.ingestion = DataIngestion(config["data"]["raw_path"])
        self.cleaner = DataCleaner()
        self.validator = DataValidation()
        self.agg_builder = ForecastingDatasetBuilder()
        self.feature_engineer = FeatureEngineer(
            lags=config["features"]["lags"],
            rolling_windows=config["features"]["rolling_windows"],
            rolling_stats=config["features"]["rolling_stats"],
        )
        self.visualizer = Visualizer(
            style=config["visualization"]["style"],
            dpi=config["visualization"]["dpi"],
            figsize=tuple(config["visualization"]["figsize"]),
        )
        self.results: dict[str, Any] = {}

    def run(self) -> dict[str, Any]:
        mlflow.set_experiment(self.config["mlflow"]["experiment_name"])
        logger.info("Starting training pipeline")
        data = self.ingestion.load_data("online_retail")
        df = data["transactions"]
        df = self.cleaner.clean_online_retail(df)
        daily = self.agg_builder.build_daily_sku_demand(df)
        daily = daily.sort_values(["stockcode", "date"]).reset_index(drop=True)
        logger.info(f"Daily SKU demand shape: {daily.shape}")
        date_col = "date"
        target = "daily_demand"
        group_cols = ["stockcode"]
        daily[date_col] = pd.to_datetime(daily[date_col])
        daily_with_features = self.feature_engineer.create_all_features(
            daily, group_cols=group_cols, target=target, date_col=date_col
        )
        self._train_and_evaluate_all_models(daily_with_features, date_col, target, group_cols)
        self._generate_figures(daily, df)
        logger.info("Training pipeline completed successfully")
        return {"status": "success", "results": self.results}

    def _train_and_evaluate_all_models(self, df, date_col, target, group_cols):
        logger.info("Training and evaluating all models...")
        top_skus = df.groupby("stockcode")[target].sum().sort_values(ascending=False).head(10).index
        sample_df = df[df["stockcode"].isin(top_skus)].copy()
        sample_df = sample_df.sort_values([date_col, "stockcode"]).dropna(subset=[target])
        logger.info(f"Sample data shape: {sample_df.shape}")
        with mlflow.start_run(run_name="full_pipeline") as _:
            mlflow.log_params(self.config)
            for model_name in ["naive", "prophet", "xgboost"]:
                if not self.config["models"][model_name]["enabled"]:
                    continue
                logger.info(f"Training {model_name}...")
                try:
                    self._train_model(model_name, sample_df, date_col, target, group_cols)
                except Exception as e:
                    logger.error(f"Failed to train {model_name}: {e}")
            all_metrics = {
                name: res["metrics"] for name, res in self.results.items() if "metrics" in res
            }
            if all_metrics:
                comparison = create_comparison_table(all_metrics)
                logger.info(f"\nModel Comparison:\n{comparison}")
                for model_name, metrics in all_metrics.items():
                    mlflow.log_metrics({f"{model_name}_{k}": v for k, v in metrics.items()})

    def _train_model(self, model_name, df, date_col, target, group_cols):
        with mlflow.start_run(run_name=model_name, nested=True):
            mlflow.log_params(self.config["models"][model_name])
            if model_name == "naive":
                self._train_naive(df, date_col, target)
            elif model_name == "prophet":
                self._train_prophet(df, date_col, target)
            elif model_name == "xgboost":
                self._train_xgboost(df, date_col, target, group_cols)

    def _train_naive(self, df, date_col, target):
        model = NaiveSeasonalForecaster(
            seasonality=self.config["models"]["naive"]["seasonality"],
            period=self.config["models"]["naive"]["period"],
        )
        wfv = WalkForwardValidator(
            n_folds=self.config["evaluation"]["cv_folds"],
            initial_days=self.config["evaluation"]["cv_initial"],
            horizon_days=self.config["evaluation"]["cv_horizon"],
            step_days=self.config["evaluation"]["cv_step"],
        )
        daily = df.groupby(date_col)[target].sum().reset_index()
        folds = wfv.split_dataframe(daily, date_col)
        all_preds = []
        all_trues = []
        for train_df, test_df, _ in folds:
            model.fit(train_df, date_col=date_col, target=target)
            preds = model.predict_with_series(test_df)
            all_preds.extend(preds)
            all_trues.extend(test_df[target].values)
        all_preds = np.array(all_preds)
        all_trues = np.array(all_trues)
        metrics = calculate_all_metrics(all_trues, all_preds)
        self.results["naive"] = {"metrics": metrics, "predictions": all_preds, "actuals": all_trues}
        mlflow.log_metrics(metrics)
        logger.info(f"Naive metrics: {metrics}")

    def _train_prophet(self, df, date_col, target):
        model = ProphetForecaster(self.config["models"]["prophet"])
        wfv = WalkForwardValidator(
            n_folds=self.config["evaluation"]["cv_folds"],
            initial_days=self.config["evaluation"]["cv_initial"],
            horizon_days=self.config["evaluation"]["cv_horizon"],
            step_days=self.config["evaluation"]["cv_step"],
        )
        top_sku = df.groupby("stockcode")[target].sum().idxmax()
        sku_df = df[df["stockcode"] == top_sku].sort_values(date_col).dropna(subset=[target])
        if len(sku_df) < 100:
            logger.warning(f"Not enough data for Prophet: {len(sku_df)} rows")
            self.results["prophet"] = {
                "metrics": {
                    k: float("nan")
                    for k in ["mae", "rmse", "mape", "smape", "wape", "bias", "forecast_accuracy"]
                },
                "predictions": np.array([]),
            }
            return
        folds = wfv.split_dataframe(sku_df, date_col)
        all_preds = []
        all_trues = []
        for train_df, test_df, _ in folds[:2]:
            try:
                model.fit(train_df, date_col=date_col, target=target)
                preds = model.predict_with_series(test_df, date_col=date_col)
                all_preds.extend(preds)
                all_trues.extend(test_df[target].values)
            except Exception as e:
                logger.error(f"Prophet fold failed: {e}")
                continue
        if len(all_preds) > 0:
            all_preds = np.array(all_preds)
            all_trues = np.array(all_trues)
            metrics = calculate_all_metrics(all_trues, all_preds)
            self.results["prophet"] = {"metrics": metrics, "predictions": all_preds, "actuals": all_trues}
            mlflow.log_metrics(metrics)
            logger.info(f"Prophet metrics: {metrics}")

    def _train_xgboost(self, df, date_col, target, group_cols):
        model = XGBoostForecaster(self.config["models"]["xgboost"])
        wfv = WalkForwardValidator(
            n_folds=self.config["evaluation"]["cv_folds"],
            initial_days=self.config["evaluation"]["cv_initial"],
            horizon_days=self.config["evaluation"]["cv_horizon"],
            step_days=self.config["evaluation"]["cv_step"],
        )
        top_sku = df.groupby("stockcode")[target].sum().idxmax()
        sku_df = df[df["stockcode"] == top_sku].sort_values(date_col).dropna(subset=[target])
        exclude_cols = [date_col, "stockcode"]
        feature_cols = [
            c
            for c in sku_df.columns
            if c not in exclude_cols and sku_df[c].dtype in ["int64", "float64"] and c != target
        ]
        cols_for_xgb = feature_cols + [target]
        sku_df = sku_df.dropna(subset=cols_for_xgb)
        if len(sku_df) < 100:
            logger.warning(f"Not enough data for XGBoost: {len(sku_df)} rows")
            self.results["xgboost"] = {
                "metrics": {
                    k: float("nan")
                    for k in ["mae", "rmse", "mape", "smape", "wape", "bias", "forecast_accuracy"]
                },
                "predictions": np.array([]),
            }
            return
        folds = wfv.split_dataframe(sku_df, date_col)
        all_preds = []
        all_trues = []
        for train_df, test_df, _ in folds[:2]:
            try:
                train_clean = train_df[cols_for_xgb].dropna()
                test_clean = test_df[cols_for_xgb].dropna()
                if len(train_clean) < 50 or len(test_clean) < 10:
                    continue
                y_train = train_clean[target].values
                y_test = test_clean[target].values
                X_train = train_clean[feature_cols]
                X_test = test_clean[feature_cols]
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                all_preds.extend(preds)
                all_trues.extend(y_test)
            except Exception as e:
                logger.error(f"XGBoost fold failed: {e}")
                continue
        if len(all_preds) > 0:
            all_preds = np.array(all_preds)
            all_trues = np.array(all_trues)
            metrics = calculate_all_metrics(all_trues, all_preds)
            imp = model.get_feature_importance()
            self.results["xgboost"] = {
                "metrics": metrics,
                "predictions": all_preds,
                "actuals": all_trues,
                "feature_importance": imp,
            }
            mlflow.log_metrics(metrics)
            logger.info(f"XGBoost metrics: {metrics}")

    def _generate_figures(self, daily: pd.DataFrame, raw: pd.DataFrame):
        logger.info("Generating figures...")
        daily_sum = daily.groupby("date")["daily_demand"].sum().reset_index()
        daily_sum.columns = ["date", "sales"]
        fig = self.visualizer.plot_time_series(daily_sum, "date", "sales")
        self.visualizer.save_figure(fig, "daily_sales_trend.png")
        fig = self.visualizer.plot_sales_distribution(daily_sum, "sales")
        self.visualizer.save_figure(fig, "sales_distribution.png")
        fig = self.visualizer.plot_weekly_seasonality(daily_sum, "date", "sales")
        self.visualizer.save_figure(fig, "weekly_seasonality.png")
        fig = self.visualizer.plot_monthly_seasonality(daily_sum, "date", "sales")
        self.visualizer.save_figure(fig, "monthly_seasonality.png")
        top_skus = (
            daily.groupby("stockcode")["daily_demand"].sum().sort_values(ascending=False).head(20)
        )
        fig, ax = plt.subplots(figsize=self.visualizer.figsize)
        ax.bar(range(len(top_skus)), top_skus.values, color="teal", alpha=0.7)
        ax.set_xticks(range(len(top_skus)))
        ax.set_xticklabels([str(s) for s in top_skus.index], rotation=45, ha="right")
        ax.set_xlabel("SKU")
        ax.set_ylabel("Total Demand")
        ax.set_title("Top 20 SKUs by Total Demand")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self.visualizer.save_figure(fig, "top_skus.png")
        if "country" in raw.columns:
            country_sales = (
                raw.groupby("country")["quantity"].sum().sort_values(ascending=False).head(20)
            )
            fig, ax = plt.subplots(figsize=self.visualizer.figsize)
            ax.bar(range(len(country_sales)), country_sales.values, color="purple", alpha=0.7)
            ax.set_xticks(range(len(country_sales)))
            ax.set_xticklabels(country_sales.index, rotation=45, ha="right")
            ax.set_xlabel("Country")
            ax.set_ylabel("Total Quantity")
            ax.set_title("Top 20 Countries by Quantity")
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            self.visualizer.save_figure(fig, "country_distribution.png")
        for model_name in ["naive", "prophet", "xgboost"]:
            if model_name in self.results and "actuals" in self.results[model_name]:
                fig = self.visualizer.plot_actual_vs_forecast(
                    self.results[model_name]["actuals"],
                    self.results[model_name]["predictions"],
                    f"{model_name.title()}: Actual vs Forecast",
                )
                self.visualizer.save_figure(fig, f"{model_name}_actual_vs_forecast.png")
        numeric_df = daily_sum.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            fig = self.visualizer.plot_heatmap(numeric_df, "Feature Correlation Heatmap")
            self.visualizer.save_figure(fig, "correlation_heatmap.png")
        logger.info("Figures generated successfully")


def main():
    from src.utils.config import load_config
    from src.utils.logger import setup_logger

    setup_logger()
    config = load_config()
    config["models"]["naive"]["period"] = 7
    config["evaluation"]["cv_folds"] = 3
    config["evaluation"]["cv_initial"] = 90
    config["evaluation"]["cv_horizon"] = 14
    config["evaluation"]["cv_step"] = 30
    pipeline = TrainingPipeline(config)
    results = pipeline.run()
    print(f"Pipeline status: {results.get('status')}")
    if "results" in results and results["results"]:
        comparison = create_comparison_table(
            {name: res["metrics"] for name, res in results["results"].items() if "metrics" in res}
        )
        print("\nFinal Model Comparison:")
        print(comparison)
    return results


if __name__ == "__main__":
    main()
