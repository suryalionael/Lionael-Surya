import logging

import pandas as pd

logger = logging.getLogger(__name__)


class FeatureEngineer:
    def __init__(
        self,
        lags: list[int] | None = None,
        rolling_windows: list[int] | None = None,
        rolling_stats: list[str] | None = None,
    ):
        self.lags = lags or [1, 7, 14, 28, 56]
        self.rolling_windows = rolling_windows or [7, 14, 28, 56]
        self.rolling_stats = rolling_stats or ["mean", "median", "std", "min", "max"]

    def create_lag_features(
        self, df: pd.DataFrame, group_cols: list[str], target: str = "daily_demand"
    ) -> pd.DataFrame:
        df = df.copy()
        for lag in self.lags:
            df[f"lag_{lag}"] = df.groupby(group_cols, observed=True)[target].shift(lag)
        return df

    def create_rolling_features(
        self, df: pd.DataFrame, group_cols: list[str], target: str = "daily_demand"
    ) -> pd.DataFrame:
        df = df.copy()
        for window in self.rolling_windows:
            group = df.groupby(group_cols, observed=True)[target]
            if "mean" in self.rolling_stats:
                df[f"rolling_mean_{window}"] = group.transform(
                    lambda x, w=window: x.shift(1).rolling(w, min_periods=1).mean()
                )
            if "median" in self.rolling_stats:
                df[f"rolling_median_{window}"] = group.transform(
                    lambda x, w=window: x.shift(1).rolling(w, min_periods=1).median()
                )
            if "std" in self.rolling_stats:
                df[f"rolling_std_{window}"] = group.transform(
                    lambda x, w=window: x.shift(1).rolling(w, min_periods=1).std()
                )
            if "min" in self.rolling_stats:
                df[f"rolling_min_{window}"] = group.transform(
                    lambda x, w=window: x.shift(1).rolling(w, min_periods=1).min()
                )
            if "max" in self.rolling_stats:
                df[f"rolling_max_{window}"] = group.transform(
                    lambda x, w=window: x.shift(1).rolling(w, min_periods=1).max()
                )
        return df

    def create_ema_features(
        self, df: pd.DataFrame, group_cols: list[str], target: str = "daily_demand"
    ) -> pd.DataFrame:
        df = df.copy()
        for span in [7, 14, 28]:
            df[f"ema_{span}"] = df.groupby(group_cols, observed=True)[target].transform(
                lambda x, s=span: x.shift(1).ewm(span=s, adjust=False).mean()
            )
        return df

    def create_calendar_features(self, df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df["day_of_week"] = df[date_col].dt.dayofweek
        df["week_of_year"] = df[date_col].dt.isocalendar().week.astype(int)
        df["month"] = df[date_col].dt.month
        df["quarter"] = df[date_col].dt.quarter
        df["year"] = df[date_col].dt.year
        df["day_of_month"] = df[date_col].dt.day
        df["day_of_year"] = df[date_col].dt.dayofyear
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        df["is_month_start"] = df[date_col].dt.is_month_start.astype(int)
        df["is_month_end"] = df[date_col].dt.is_month_end.astype(int)
        return df

    def create_all_features(
        self,
        df: pd.DataFrame,
        group_cols: list[str] | None = None,
        target: str = "daily_demand",
        date_col: str = "date",
    ) -> pd.DataFrame:
        if group_cols is None:
            group_cols = ["stockcode"]
        df = df.copy()
        df = self.create_calendar_features(df, date_col)
        df = self.create_lag_features(df, group_cols, target)
        df = self.create_rolling_features(df, group_cols, target)
        df = self.create_ema_features(df, group_cols, target)
        return df
