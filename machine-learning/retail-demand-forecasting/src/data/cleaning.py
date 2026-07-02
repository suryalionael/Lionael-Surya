import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataCleaner:
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(r"[^a-z0-9_]", "_", regex=True)
            .str.replace(r"_+", "_", regex=True)
        )
        return df

    def drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        n_before = len(df)
        df = df.drop_duplicates()
        n_removed = n_before - len(df)
        if n_removed > 0:
            logger.info(f"Removed {n_removed} duplicate rows")
        return df

    def parse_invoice_date(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        date_cols = [c for c in df.columns if "invoicedate" in c.lower() or "date" in c.lower()]
        for col in date_cols:
            if df[col].dtype == "object" or not pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    def remove_cancelled_invoices(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        invoice_col = next((c for c in df.columns if "invoice" in c.lower()), None)
        if invoice_col:
            is_cancelled = df[invoice_col].astype(str).str.startswith("C")
            n_cancelled = is_cancelled.sum()
            if n_cancelled > 0:
                df = df[~is_cancelled].copy()
                logger.info(f"Removed {n_cancelled} cancelled invoice rows")
        return df

    def remove_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        qty_col = next(
            (c for c in df.columns if "quantity" in c.lower() or "qty" in c.lower()), None
        )
        if qty_col and qty_col in df.columns:
            is_return = df[qty_col] < 0
            n_returns = is_return.sum()
            if n_returns > 0:
                df = df[~is_return].copy()
                logger.info(f"Removed {n_returns} return rows (negative quantity)")
        return df

    def remove_invalid_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        price_col = next((c for c in df.columns if "price" in c.lower()), None)
        if price_col and price_col in df.columns:
            invalid = df[price_col] <= 0
            n_invalid = invalid.sum()
            if n_invalid > 0:
                df = df[~invalid].copy()
                logger.info(f"Removed {n_invalid} rows with invalid prices")
        return df

    def remove_invalid_quantities(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        qty_col = next(
            (c for c in df.columns if "quantity" in c.lower() or "qty" in c.lower()), None
        )
        if qty_col and qty_col in df.columns:
            invalid = df[qty_col] <= 0
            n_invalid = invalid.sum()
            if n_invalid > 0:
                df = df[~invalid].copy()
                logger.info(f"Removed {n_invalid} rows with invalid quantities")
        return df

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.columns:
            n_missing = df[col].isnull().sum()
            if n_missing == 0:
                continue
            if col in ("description", "customer_id"):
                df[col] = df[col].fillna("unknown")
                logger.info(f"Filled {n_missing} missing values in '{col}' with 'unknown'")
            elif df[col].dtype in ("int64", "float64"):
                df[col] = df[col].fillna(0)
                logger.info(f"Filled {n_missing} missing values in '{col}' with 0")
        return df

    def clean_online_retail(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info(f"Starting cleaning: {len(df):,} rows")
        df = self.clean_column_names(df)
        df = self.drop_duplicates(df)
        df = self.parse_invoice_date(df)
        df = self.remove_cancelled_invoices(df)
        df = self.remove_returns(df)
        df = self.remove_invalid_prices(df)
        df = self.remove_invalid_quantities(df)
        df = self.handle_missing_values(df)
        logger.info(f"Finished cleaning: {len(df):,} rows")
        return df

    def detect_outliers_iqr(
        self, df: pd.DataFrame, column: str, multiplier: float = 1.5
    ) -> pd.Series:
        col = df[column].astype(float)
        Q1 = col.quantile(0.25)
        Q3 = col.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - multiplier * IQR
        upper = Q3 + multiplier * IQR
        return (col < lower) | (col > upper)

    def detect_outliers_zscore(
        self, df: pd.DataFrame, column: str, threshold: float = 3.0
    ) -> pd.Series:
        col = df[column].astype(float)
        mean = col.mean()
        std = col.std()
        if std == 0:
            return pd.Series(False, index=df.index)
        z_scores = np.abs((col - mean) / std)
        return z_scores > threshold

    def cap_outliers(
        self,
        df: pd.DataFrame,
        column: str,
        method: str = "iqr",
        multiplier: float = 1.5,
    ) -> pd.DataFrame:
        df = df.copy()
        df[column] = df[column].astype(float)
        if method == "iqr":
            outliers = self.detect_outliers_iqr(df, column, multiplier)
        else:
            outliers = self.detect_outliers_zscore(df, column, multiplier)
        if method == "iqr":
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - multiplier * IQR
            upper = Q3 + multiplier * IQR
        else:
            mean = df[column].mean()
            std = df[column].std()
            lower = mean - multiplier * std
            upper = mean + multiplier * std
        df.loc[df[column] < lower, column] = lower
        df.loc[df[column] > upper, column] = upper
        n_capped = outliers.sum()
        if n_capped > 0:
            logger.info(f"Capped {n_capped} outliers in '{column}'")
        return df
