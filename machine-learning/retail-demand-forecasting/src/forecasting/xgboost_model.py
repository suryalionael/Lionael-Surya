import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class XGBoostForecaster:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.model = None
        self.fitted = False
        self.feature_names: list[str] = []

    def _build_model(self, **kwargs):
        try:
            from xgboost import XGBRegressor
        except ImportError as e:
            raise ImportError("XGBoost is not installed. pip install xgboost") from e

        params = {
            "n_estimators": self.config.get("n_estimators", 1000),
            "max_depth": self.config.get("max_depth", 6),
            "learning_rate": self.config.get("learning_rate", 0.01),
            "subsample": self.config.get("subsample", 0.8),
            "colsample_bytree": self.config.get("colsample_bytree", 0.8),
            "min_child_weight": self.config.get("min_child_weight", 1),
            "gamma": self.config.get("gamma", 0),
            "reg_alpha": self.config.get("reg_alpha", 0),
            "reg_lambda": self.config.get("reg_lambda", 1),
            "random_state": 42,
            "verbosity": 0,
        }
        params.update(kwargs)
        return XGBRegressor(**params)

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame | None = None,
        y_val: pd.Series | np.ndarray | None = None,
    ) -> "XGBoostForecaster":
        self.feature_names = list(X_train.columns)
        early_stopping_rounds = self.config.get("early_stopping_rounds", 50)
        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = [(X_train.values, y_train), (X_val.values, y_val)]
        self.model = self._build_model()
        self.model.fit(
            X_train.values,
            y_train,
            eval_set=eval_set,
            early_stopping_rounds=early_stopping_rounds if eval_set else None,
            verbose=False,
        )
        self.fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.fitted or self.model is None:
            raise ValueError("Model not fitted yet.")
        return self.model.predict(X.values)

    def get_feature_importance(self) -> pd.DataFrame:
        if not self.fitted or self.model is None:
            raise ValueError("Model not fitted yet.")
        importance = self.model.feature_importances_
        return pd.DataFrame({"feature": self.feature_names, "importance": importance}).sort_values(
            "importance", ascending=False
        )

    def tune_hyperparameters(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame,
        y_val: pd.Series | np.ndarray,
        n_trials: int = 30,
    ) -> dict:
        try:
            import optuna
        except ImportError:
            logger.warning("optuna not installed. Using default parameters.")
            return self.config

        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 100, 2000),
                "max_depth": trial.suggest_int("max_depth", 3, 12),
                "learning_rate": trial.suggest_float("learning_rate", 0.001, 0.1, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.3, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                "gamma": trial.suggest_float("gamma", 0, 5),
                "reg_alpha": trial.suggest_float("reg_alpha", 0, 10),
                "reg_lambda": trial.suggest_float("reg_lambda", 0, 10),
            }
            model = self._build_model(**params)
            model.fit(
                X_train.values,
                y_train,
                eval_set=[(X_train.values, y_train), (X_val.values, y_val)],
                verbose=False,
            )
            preds = model.predict(X_val.values)
            return float(np.mean(np.abs(preds - y_val)))

        study = optuna.create_study(direction="minimize")
        study.optimize(objective, n_trials=n_trials)
        self.config.update(study.best_params)
        logger.info(f"Best XGBoost params: {study.best_params}")
        return self.config
