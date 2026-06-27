import os
import json
import joblib
from typing import Any
from src.logger import logger

def save_pkl(obj: Any, file_path: str) -> None:
    """Saves a python object using joblib."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    logger.info(f"Saving object to {file_path}")
    try:
        joblib.dump(obj, file_path)
    except Exception as e:
        logger.error(f"Error saving object to {file_path}: {e}")
        raise e

def load_pkl(file_path: str) -> Any:
    """Loads a python object using joblib."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    logger.info(f"Loading object from {file_path}")
    try:
        return joblib.load(file_path)
    except Exception as e:
        logger.error(f"Error loading object from {file_path}: {e}")
        raise e

def save_json(data: dict, file_path: str) -> None:
    """Saves a dictionary as a formatted JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    logger.info(f"Saving JSON to {file_path}")
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        raise e

def load_json(file_path: str) -> dict:
    """Loads a JSON file as a dictionary."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        raise e
