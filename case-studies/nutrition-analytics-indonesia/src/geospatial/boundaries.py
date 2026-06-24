"""Loads the real, distinct 38-province boundary geometry fetched by
src/ingestion/fetch_geo_boundaries.py --source big_mirror (docs/phase5_geometry_
reconciliation.md), standardizes province names through the existing reference
layer, and simplifies geometry to a resolution practical for province-level spatial
statistics and mapping.

The raw fetched file is ~497MB (38 full-resolution, multi-island provinces -- some
single province files exceed 50MB) and exceeds GDAL's default GeoJSON complexity
guard. This module sets OGR_GEOJSON_MAX_OBJ_SIZE=0 to read it, then immediately
simplifies (Douglas-Peucker, topology-preserving) to ~0.001 degrees (~111m at the
equator) -- confirmed during Phase 5 testing to produce zero invalid geometries
while shrinking total geometry size by roughly 45x (258MB -> 5.6MB of WKB). The raw
file itself is never modified, per this project's standing provenance rules --
simplification happens only on the in-memory copy used for analysis.
"""

import logging
import os
from pathlib import Path

import geopandas as gpd

from src.reference.lookup import load_variant_map, normalize
from src.utils.config import RAW_DIR
from src.utils.provenance import latest_entries

log = logging.getLogger(__name__)

SIMPLIFY_TOLERANCE_DEGREES = 0.001


def _latest_big_mirror_path() -> Path:
    entries = latest_entries()
    boundaries_entry = entries.get("boundaries")
    if boundaries_entry is None:
        raise FileNotFoundError("No manifest entry for 'boundaries' -- run `python -m src.ingestion.fetch_geo_boundaries --source big_mirror` first.")
    path = Path(boundaries_entry["file_path"])
    if "big_mirror" not in path.name:
        raise FileNotFoundError(
            f"Latest boundaries manifest entry ({path.name}) is not a big_mirror fetch. "
            "Phase 5 spatial analysis requires the distinct 38-province geometry -- "
            "run `python -m src.ingestion.fetch_geo_boundaries --source big_mirror`."
        )
    return path


def load_boundaries(simplify_tolerance: float = SIMPLIFY_TOLERANCE_DEGREES) -> gpd.GeoDataFrame:
    path = _latest_big_mirror_path()

    os.environ.setdefault("OGR_GEOJSON_MAX_OBJ_SIZE", "0")
    gdf = gpd.read_file(path)

    if gdf.crs is None:
        raise ValueError(f"{path} has no CRS defined -- refusing to assume one.")

    n_invalid_before = int((~gdf.geometry.is_valid).sum())
    if n_invalid_before:
        log.warning("%d invalid geometries before simplification -- repairing with buffer(0)", n_invalid_before)
        gdf.loc[~gdf.geometry.is_valid, "geometry"] = gdf.loc[~gdf.geometry.is_valid, "geometry"].buffer(0)

    gdf["geometry"] = gdf.geometry.simplify(simplify_tolerance, preserve_topology=True)

    n_invalid_after = int((~gdf.geometry.is_valid).sum())
    if n_invalid_after:
        raise ValueError(f"{n_invalid_after} geometries became invalid after simplification -- refusing to proceed with corrupted geometry.")

    variant_map = load_variant_map()
    gdf["province"] = gdf["WADMPR"].apply(lambda name: normalize(name, variant_map))

    return gdf[["province", "geometry"]]
