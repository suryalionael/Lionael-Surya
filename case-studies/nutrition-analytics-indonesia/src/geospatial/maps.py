"""Generates the spatial diagnostic maps required by Phase 5, saved to
reports/maps/. Each map answers one specific question (this project's standing
visual-standards rule -- avoid decorative charts), not a generic "pretty map."
"""

import logging

import geopandas as gpd
import matplotlib.pyplot as plt

from src.utils.config import ROOT

log = logging.getLogger(__name__)

MAPS_DIR = ROOT / "reports" / "maps"

TIER_ORDER = ["Low", "Medium", "High", "Critical"]
TIER_COLORS = {"Low": "#2c7bb6", "Medium": "#ffffbf", "High": "#fdae61", "Critical": "#d7191c"}
LISA_COLORS = {
    "High-High": "#d7191c",
    "Low-Low": "#2c7bb6",
    "High-Low": "#fdae61",
    "Low-High": "#abd9e9",
    "Not significant": "#e0e0e0",
}


def map_npi_score(gdf: gpd.GeoDataFrame, out_path=None) -> None:
    """Choropleth: where is the NPI score highest/lowest -- the most basic
    "what does this index say" view."""
    out_path = out_path or MAPS_DIR / "npi_score_choropleth.png"
    fig, ax = plt.subplots(figsize=(10, 6))
    gdf.plot(column="npi", cmap="OrRd", legend=True, ax=ax, edgecolor="black", linewidth=0.3)
    ax.set_title("Nutrition Priority Index (NPI) Score by Province")
    ax.set_axis_off()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def map_priority_tier(gdf: gpd.GeoDataFrame, tier_col: str = "tier_jenks", out_path=None) -> None:
    """Choropleth: which provinces fall in which priority tier -- the actual
    decision-relevant output, not just the raw continuous score."""
    out_path = out_path or MAPS_DIR / "priority_tier_choropleth.png"
    fig, ax = plt.subplots(figsize=(10, 6))
    for tier in TIER_ORDER:
        subset = gdf[gdf[tier_col] == tier]
        if not subset.empty:
            subset.plot(ax=ax, color=TIER_COLORS[tier], edgecolor="black", linewidth=0.3, label=tier)
    ax.set_title(f"Priority Tier by Province ({tier_col})")
    ax.legend(loc="lower left", title="Tier")
    ax.set_axis_off()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def map_lisa_clusters(lisa_gdf: gpd.GeoDataFrame, out_path=None) -> None:
    """Where are the statistically significant spatial clusters and outliers --
    answers "is this clustering real or just province-by-province noise," which the
    other two maps cannot answer on their own."""
    out_path = out_path or MAPS_DIR / "lisa_clusters.png"
    fig, ax = plt.subplots(figsize=(10, 6))
    for cluster in LISA_COLORS:
        subset = lisa_gdf[lisa_gdf["lisa_cluster"] == cluster]
        if not subset.empty:
            subset.plot(ax=ax, color=LISA_COLORS[cluster], edgecolor="black", linewidth=0.3, label=cluster)
    ax.set_title("LISA Cluster Classification (p < 0.05, KNN k=6)")
    ax.legend(loc="lower left", title="Cluster type")
    ax.set_axis_off()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def map_region(gdf: gpd.GeoDataFrame, out_path=None) -> None:
    """Which provinces belong to Western/Central/Eastern Indonesia -- needed to
    visually cross-reference the regional disparity findings against the map, since
    the WIB/WITA/WIT split isn't geographically obvious without seeing it."""
    from src.geospatial.regions import REGION_ORDER, assign_region

    out_path = out_path or MAPS_DIR / "region_classification.png"
    df = assign_region(gdf)
    colors = {"Western": "#1b9e77", "Central": "#d95f02", "Eastern": "#7570b3"}
    fig, ax = plt.subplots(figsize=(10, 6))
    for region in REGION_ORDER:
        subset = df[df["region"] == region]
        if not subset.empty:
            subset.plot(ax=ax, color=colors[region], edgecolor="black", linewidth=0.3, label=region)
    ax.set_title("Western / Central / Eastern Indonesia (WIB/WITA/WIT time zones)")
    ax.legend(loc="lower left", title="Region")
    ax.set_axis_off()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_all_maps(gdf: gpd.GeoDataFrame, lisa_gdf: gpd.GeoDataFrame) -> None:
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    map_npi_score(gdf)
    map_priority_tier(gdf)
    map_lisa_clusters(lisa_gdf)
    map_region(gdf)
    log.info("Wrote 4 maps to %s", MAPS_DIR)
