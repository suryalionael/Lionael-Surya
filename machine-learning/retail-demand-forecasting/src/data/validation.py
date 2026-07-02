import logging

import pandas as pd

logger = logging.getLogger(__name__)


class DataValidation:
    def check_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = df.isnull().sum()
        missing_pct = (missing / len(df)) * 100
        result = pd.DataFrame({"missing_count": missing, "missing_pct": missing_pct})
        result = result[result["missing_count"] > 0].sort_values("missing_count", ascending=False)
        return result

    def check_duplicates(self, df: pd.DataFrame, subset: list[str] | None = None) -> int:
        return df.duplicated(subset=subset).sum()

    def check_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            {"dtype": df.dtypes, "nunique": df.nunique(), "null_count": df.isnull().sum()}
        )

    def validate_online_retail(self, df: pd.DataFrame) -> dict:
        issues = {}
        if "quantity" in df.columns:
            issues["negative_quantity"] = int((df["quantity"] < 0).sum())
            issues["zero_quantity"] = int((df["quantity"] == 0).sum())
        if "price" in df.columns:
            issues["invalid_price"] = int((df["price"] <= 0).sum())
        if "invoice" in df.columns:
            issues["cancelled_invoices"] = int(df["invoice"].astype(str).str.startswith("C").sum())
        if "invoicedate" in df.columns:
            df = df.copy()
            df["invoicedate"] = pd.to_datetime(df["invoicedate"])
            date_range = (df["invoicedate"].max() - df["invoicedate"].min()).days
            issues["date_range_days"] = date_range
        return issues

    def generate_validation_report(self, df: pd.DataFrame, name: str = "dataset") -> str:
        lines = [f"=== Data Validation Report: {name} ==="]
        lines.append(f"Shape: {df.shape}")
        lines.append(f"Columns: {list(df.columns)}")
        missing = self.check_missing_values(df)
        if len(missing) > 0:
            lines.append("\nMissing values:")
            for col, row in missing.iterrows():
                lines.append(f"  {col}: {row['missing_count']} ({row['missing_pct']:.1f}%)")
        else:
            lines.append("\nNo missing values found.")
        dupes = self.check_duplicates(df)
        lines.append(f"Duplicate rows: {dupes}")
        if "quantity" in df.columns:
            lines.append("\nQuantity stats:")
            lines.append(f"  Mean: {df['quantity'].mean():.2f}")
            lines.append(f"  Median: {df['quantity'].median():.2f}")
            lines.append(f"  Std: {df['quantity'].std():.2f}")
            lines.append(f"  Min: {df['quantity'].min():.2f}")
            lines.append(f"  Max: {df['quantity'].max():.2f}")
        return "\n".join(lines)
