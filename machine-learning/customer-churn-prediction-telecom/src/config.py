import os
import yaml
from pathlib import Path

# Resolve the root directory of the repository
ROOT_DIR = Path(__file__).resolve().parent.parent

def load_config(config_path: str = None) -> dict:
    """Loads and returns the project YAML configuration."""
    if config_path is None:
        config_path = ROOT_DIR / "config" / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Resolve paths to absolute paths based on the project root
    for key, value in config.get("paths", {}).items():
        config["paths"][key] = str(ROOT_DIR / value)

    return config

# Global config instance
CONFIG = load_config()

# Helper function to get config values
def get_config(*keys, default=None):
    """Retrieves a configuration value from the nested config dictionary."""
    val = CONFIG
    for key in keys:
        if isinstance(val, dict) and key in val:
            val = val[key]
        else:
            return default
    return val
