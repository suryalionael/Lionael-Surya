import logging

import pandas as pd

logger = logging.getLogger(__name__)


class ForecastingDatasetBuilder:
    def build_daily_sku_demand(self, df: pd.DataFrame) -> pd.DataFrame:
        invoice_col = next(
            c for c in df.columns if "invoice" in c.lower() and "date" not in c.lower()
        )
        date_col = next(c for c in df.columns if "invoicedate" in c.lower() or "date" in c.lower())
        sku_col = next(c for c in df.columns if "stockcode" in c.lower())
        qty_col = next(c for c in df.columns if "quantity" in c.lower() or "qty" in c.lower())
        price_col = next(c for c in df.columns if "price" in c.lower())

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df["date"] = df[date_col].dt.date
        df["revenue"] = df[qty_col] * df[price_col]

        daily = (
            df.groupby(["date", sku_col], observed=True)
            .agg(
                daily_demand=(qty_col, "sum"),
                revenue=("revenue", "sum"),
                num_transactions=(invoice_col, "nunique"),
                avg_price=(price_col, "mean"),
            )
            .reset_index()
        )
        daily.columns = [
            "date",
            "stockcode",
            "daily_demand",
            "revenue",
            "num_transactions",
            "avg_price",
        ]
        daily["date"] = pd.to_datetime(daily["date"])
        daily = daily.sort_values(["stockcode", "date"]).reset_index(drop=True)
        logger.info(
            f"Built daily SKU demand dataset: {len(daily):,} rows, {daily['stockcode'].nunique():,} SKUs"
        )
        return daily

    def get_top_skus(self, df: pd.DataFrame, n: int = 20) -> list:
        if "stockcode" in df.columns and "daily_demand" in df.columns:
            top = (
                df.groupby("stockcode")["daily_demand"]
                .sum()
                .sort_values(ascending=False)
                .head(n)
                .index.tolist()
            )
            return top
        return []

    def build_aggregated_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        if "stockcode" not in df.columns or "daily_demand" not in df.columns:
            return df
        daily = df.groupby("date")["daily_demand"].sum().reset_index()
        daily.columns = ["date", "total_demand"]
        daily = daily.sort_values("date")
        return daily
