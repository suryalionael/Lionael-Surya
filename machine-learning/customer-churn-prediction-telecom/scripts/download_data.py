#!/usr/bin/env python
"""
Script to download the IBM Telco Customer Churn dataset.
Saves the raw CSV to data/raw/Telco-Customer-Churn.csv.
"""

import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_URL = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "Telco-Customer-Churn.csv")


def download_dataset():
    """Downloads the IBM Telco Customer Churn dataset if it does not already exist."""
    if not os.path.exists(OUTPUT_DIR):
        logger.info(f"Creating raw data directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    if os.path.exists(OUTPUT_PATH):
        logger.info(f"Dataset already exists at {OUTPUT_PATH}. Skipping download.")
        return

    logger.info(f"Downloading dataset from {DATA_URL} ...")
    try:
        urllib.request.urlretrieve(DATA_URL, OUTPUT_PATH)
        logger.info(f"Successfully downloaded dataset to {OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise e


if __name__ == "__main__":
    download_dataset()
