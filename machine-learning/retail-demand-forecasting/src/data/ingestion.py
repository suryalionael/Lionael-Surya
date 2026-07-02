import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class DataIngestionError(Exception):
    pass


class DataIngestion:
    def __init__(self, raw_path: str = "data/raw"):
        self.raw_path = Path(raw_path)

    def load_online_retail(self, filepath: str | None = None) -> pd.DataFrame:
        if filepath is None:
            filepath = str(self.raw_path / "online_retail_II.xlsx")
        path = Path(filepath)
        if not path.exists():
            raise DataIngestionError(f"File not found: {path}")
        xls = pd.ExcelFile(path)
        sheets = xls.sheet_names
        logger.info(f"Loading {len(sheets)} sheets: {sheets}")
        dfs = []
        for sheet in sheets:
            df = pd.read_excel(path, sheet_name=sheet)
            logger.info(f"Sheet '{sheet}': {df.shape[0]:,} rows, {df.shape[1]} cols")
            dfs.append(df)
        combined = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined: {combined.shape[0]:,} rows")
        return combined

    def load_data(self, dataset: str = "online_retail") -> dict[str, pd.DataFrame]:
        if dataset == "online_retail":
            df = self.load_online_retail()
            return {"transactions": df}
        raise DataIngestionError(f"Unknown dataset: {dataset}")
