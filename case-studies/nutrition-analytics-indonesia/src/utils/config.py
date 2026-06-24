"""Environment and path configuration shared by all ingestion/validation scripts."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]

load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"
CONFIG_DIR = ROOT / "config"
CONTRACTS_DIR = ROOT / "docs" / "data_contracts"
DOCS_DIR = ROOT / "docs"
MANIFEST_PATH = RAW_DIR / "_manifest.jsonl"
PROVINCE_LOOKUP_PATH = ROOT / "src" / "reference" / "province_lookup.csv"

for _dir in (RAW_DIR, INTERIM_DIR, PROCESSED_DIR, EXTERNAL_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


def get_bps_api_key() -> str:
    key = os.environ.get("BPS_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "BPS_API_KEY is not set. Copy .env.example to .env and fill in your free "
            "API key from https://webapi.bps.go.id/ (sign up, create an application, "
            "use the App ID)."
        )
    return key
