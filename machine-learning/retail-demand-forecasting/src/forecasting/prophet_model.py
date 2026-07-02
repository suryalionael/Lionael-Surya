import logging
import warnings

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ProphetForecaster:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.model = None
        self.fitted = False

    def _build_model(self, **kwargs):
        try:
            from prophet import Prophet
        except ImportError as e:
            raise ImportError("Prophet is not installed. pip install prophet") from e

        params = {
            "yearly_seasonality": self.config.get("yearly_seasonality", True),
            "weekly_seasonality": self.config.get("weekly_seasonality", True),
            "daily_seasonality": self.config.get("daily_seasonality", False),
            "seasonality_mode": self.config.get("seasonality_mode", "multiplicative"),
            "changepoint_prior_scale": self.config.get("changepoint_prior_scale", 0.05),
            "seasonality_prior_scale": self.config.get("seasonality_prior_scale", 10.0),
            "holidays_prior_scale": self.config.get("holidays_prior_scale", 10.0),
            "n_changepoints": self.config.get("n_changepoints", 25),
            "uncertainty_samples": self.config.get("uncertainty_samples", 1000),
        }
        params.update(kwargs)
        return Prophet(**params)

    def fit(
        self,
        df: pd.DataFrame,
        date_col: str = "date",
        target: str = "sales",
        holiday_df: pd.DataFrame | None = None,
        extra_regressors: list[str] | None = None,
    ) -> "ProphetForecaster":
        prophet_df = pd.DataFrame()
        prophet_df["ds"] = pd.to_datetime(df[date_col])
        prophet_df["y"] = df[target].values

        self.model = self._build_model()

        if holiday_df is not None and "date" in holiday_df.columns and "type" in holiday_df.columns:
            holidays = holiday_df.copy()
            holidays["ds"] = pd.to_datetime(holidays["date"])
            self.model = self._build_model(holidays=holidays[["ds", "type"]])

        if extra_regressors:
            for reg in extra_regressors:
                if reg in df.columns:
                    prophet_df[reg] = df[reg].values
                    self.model.add_regressor(reg)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(prophet_df)
        self.fitted = True
        self._last_df = prophet_df
        return self

    def predict(self, horizon: int, freq: str = "D") -> pd.DataFrame:
        if not self.fitted or self.model is None:
            raise ValueError("Model not fitted yet.")
        future = self.model.make_future_dataframe(periods=horizon, freq=freq)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            forecast = self.model.predict(future)
        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(horizon).copy()
        result.columns = ["date", "forecast", "forecast_lower", "forecast_upper"]
        result["model"] = "prophet"
        return result

    def predict_with_series(self, test_df: pd.DataFrame, date_col: str = "date") -> np.ndarray:
        if not self.fitted or self.model is None:
            raise ValueError("Model not fitted yet.")
        future = pd.DataFrame()
        future["ds"] = pd.to_datetime(test_df[date_col])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            forecast = self.model.predict(future)
        return forecast["yhat"].values

    def get_params(self) -> dict:
        return self.config

    def tune_hyperparameters(
        self,
        df: pd.DataFrame,
        date_col: str = "date",
        target: str = "sales",
        n_trials: int = 20,
    ) -> dict:
        try:
            import optuna
        except ImportError:
            logger.warning("optuna not installed. Using default parameters.")
            return self.config

        def objective(trial):
            params = {
                "changepoint_prior_scale": trial.suggest_float(
                    "changepoint_prior_scale", 0.001, 0.5
                ),
                "seasonality_prior_scale": trial.suggest_float(
                    "seasonality_prior_scale", 0.1, 20.0
                ),
                "holidays_prior_scale": trial.suggest_float("holidays_prior_scale", 0.1, 20.0),
                "seasonality_mode": trial.suggest_categorical(
                    "seasonality_mode", ["additive", "multiplicative"]
                ),
            }
            split_idx = int(len(df) * 0.8)
            train_df = df.iloc[:split_idx]
            val_df = df.iloc[split_idx:]
            prophet_df = pd.DataFrame(
                {"ds": pd.to_datetime(train_df[date_col]), "y": train_df[target].values}
            )
            val_prophet = pd.DataFrame(
                {"ds": pd.to_datetime(val_df[date_col]), "y": val_df[target].values}
            )
            model = self._build_model(**params)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(prophet_df)
                forecast = model.predict(val_prophet)
            mae = np.mean(np.abs(forecast["yhat"].values - val_df[target].values))
            return mae

        study = optuna.create_study(direction="minimize")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            study.optimize(objective, n_trials=n_trials)
        self.config.update(study.best_params)
        logger.info(f"Best Prophet params: {study.best_params}")
        return self.config
