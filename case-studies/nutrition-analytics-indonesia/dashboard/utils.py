"""Shared data loading for the dashboard. Reads only the committed snapshot in
dashboard/data/ (built by dashboard/prepare_data.py) -- the dashboard never
recomputes or reinterprets any methodology, per Phase 6 scope.
"""

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_rankings() -> pd.DataFrame:
    return pd.read_json(DATA_DIR / "npi_rankings.json")


@st.cache_data
def load_spatial() -> gpd.GeoDataFrame:
    return gpd.read_file(DATA_DIR / "npi_spatial.geojson")


@st.cache_data
def load_lisa() -> pd.DataFrame:
    return pd.read_json(DATA_DIR / "lisa_results.json")


@st.cache_data
def load_summary() -> dict:
    with open(DATA_DIR / "summary_stats.json") as f:
        return json.load(f)


@st.cache_data
def load_merged_indicators() -> pd.DataFrame:
    return pd.read_json(DATA_DIR / "merged_provincial_indicators.json")


TIER_COLORS = {"Low": "#2c7bb6", "Medium": "#ffffbf", "High": "#fdae61", "Critical": "#d7191c"}
TIER_ORDER = ["Low", "Medium", "High", "Critical"]
LISA_COLORS = {
    "High-High": "#d7191c",
    "Low-Low": "#2c7bb6",
    "High-Low": "#fdae61",
    "Low-High": "#abd9e9",
    "Not significant": "#e0e0e0",
}
