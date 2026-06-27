import os
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from src.config import CONFIG
from src.logger import logger
from src.validation import validate_dataset

def load_raw_data(data_path: str = None) -> pd.DataFrame:
    """Loads raw data from the configured csv file path."""
    if data_path is None:
        data_path = CONFIG["paths"]["raw_data"]
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Raw data file not found at: {data_path}. Please run download_data.py first.")
        
    logger.info(f"Loading raw data from {data_path}")
    return pd.read_csv(data_path)

def clean_data(df: pd.DataFrame, is_train: bool = True) -> pd.DataFrame:
    """
    Cleans raw data:
    1. Converts TotalCharges to numeric, handles blank/space values
    2. Maps Churn to binary values (1: Yes, 0: No) if is_train is True
    """
    df_clean = df.copy()
    
    # Clean TotalCharges
    if "TotalCharges" in df_clean.columns:
        # Convert any empty string or string containing only spaces to NaN
        df_clean["TotalCharges"] = df_clean["TotalCharges"].replace(r"^\s*$", np.nan, regex=True)
        # Convert to numeric
        df_clean["TotalCharges"] = pd.to_numeric(df_clean["TotalCharges"], errors="coerce")
        
        # Smart fill for missing TotalCharges: if tenure is 0, set to 0. Otherwise tenure * MonthlyCharges
        mask_nan = df_clean["TotalCharges"].isnull()
        if mask_nan.any():
            logger.info(f"Filling {mask_nan.sum()} missing values in TotalCharges.")
            df_clean.loc[mask_nan & (df_clean["tenure"] == 0), "TotalCharges"] = 0.0
            # For any others, fill with tenure * MonthlyCharges
            mask_nan_remaining = df_clean["TotalCharges"].isnull()
            if mask_nan_remaining.any():
                df_clean.loc[mask_nan_remaining, "TotalCharges"] = (
                    df_clean.loc[mask_nan_remaining, "tenure"] * df_clean.loc[mask_nan_remaining, "MonthlyCharges"]
                )
                
    # Clean SeniorCitizen to ensure it is categorical or numeric consistently
    if "SeniorCitizen" in df_clean.columns:
        df_clean["SeniorCitizen"] = df_clean["SeniorCitizen"].astype(int)

    # Clean Churn target column
    target_col = CONFIG["data"]["target"]
    if is_train and target_col in df_clean.columns:
        logger.info(f"Mapping target '{target_col}' column to binary values.")
        df_clean[target_col] = df_clean[target_col].map({"Yes": 1, "No": 0})
        
    return df_clean

def preprocess_pipeline(data_path: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Fully reproducible preprocessing pipeline:
    1. Loads raw data
    2. Runs schema and data quality validation
    3. Cleans data
    4. Separates X and y (and customerID)
    Returns: df_clean, X, y
    """
    df = load_raw_data(data_path)
    
    # Run validation checks
    validation_report = validate_dataset(df, is_train=True)
    if not validation_report["passed_all"]:
        logger.warning("Data validation failed some quality or schema checks. Proceeding with caution.")
    else:
        logger.info("Data validation checks passed successfully.")
        
    # Clean the dataset
    df_clean = clean_data(df, is_train=True)
    
    # Separate features and target
    id_col = CONFIG["data"]["id_column"]
    target_col = CONFIG["data"]["target"]
    
    X = df_clean.drop(columns=[target_col])
    y = df_clean[target_col]
    
    # Ensure processed directory exists
    processed_dir = CONFIG["paths"]["processed_data_dir"]
    os.makedirs(processed_dir, exist_ok=True)
    
    # Save clean dataset
    clean_data_path = os.path.join(processed_dir, "cleaned_customer_churn.csv")
    df_clean.to_csv(clean_data_path, index=False)
    logger.info(f"Saved cleaned dataset to {clean_data_path}")
    
    return df_clean, X, y
