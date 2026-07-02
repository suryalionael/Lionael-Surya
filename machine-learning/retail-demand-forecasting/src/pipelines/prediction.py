import logging

import pandas as pd

from src.features.engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class PredictionPipeline:
    def __init__(self, config: dict):
        self.config = config
        self.feature_engineer = FeatureEngineer(
            lags=config["features"]["lags"],
            rolling_windows=config["features"]["rolling_windows"],
            rolling_stats=config["features"]["rolling_stats"],
        )

    def predict(self, df: pd.DataFrame, horizon: int = 30) -> pd.DataFrame:
        logger.info(f"Generating predictions for horizon={horizon}")
        df = df.copy()
        df = self.feature_engineer.create_calendar_features(df)
        predictions = []
        for _ in range(horizon):
            feature_cols = [
                c for c in df.columns if df[c].dtype in ["int64", "float64"] and c not in ["daily_demand"]
            ]
            df = df.dropna(subset=feature_cols)
            if len(df) > 0:
                pred = df[feature_cols].iloc[-1:].mean().iloc[0]
                predictions.append(pred)
        return pd.DataFrame({"prediction": predictions, "horizon": range(1, horizon + 1)})
