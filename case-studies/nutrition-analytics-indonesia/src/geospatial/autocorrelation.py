"""Global and local (LISA) spatial autocorrelation of the NPI score across
Indonesia's 38 provinces.

Weights matrix choice, decided here rather than left implicit: Queen contiguity
(shared-border neighbors) leaves 7 of 38 provinces with zero neighbors --
confirmed during Phase 5 testing (Bali, Kep. Bangka Belitung, Kep. Riau, Maluku,
Maluku Utara, Nusa Tenggara Barat, Nusa Tenggara Timur -- all island/archipelagic
provinces with no land border to another province). Indonesia's geography makes
this a real structural property, not a data error, but it would silently exclude
18% of provinces from every local statistic if used as the primary weights matrix.
K-nearest-neighbors (every province guaranteed >=1 neighbor regardless of whether
it physically touches another) is used as the primary weights matrix instead;
Queen contiguity is retained and reported as an explicit robustness comparison
(docs/phase5_spatial_results.md "Spatial Robustness" section), not silently dropped.
"""

import logging

import geopandas as gpd
import numpy as np
from esda.moran import Moran, Moran_Local
from libpysal.weights import KNN, Queen

log = logging.getLogger(__name__)

DEFAULT_K = 6
PERMUTATIONS = 999
SIGNIFICANCE_LEVEL = 0.05


def build_knn_weights(gdf: gpd.GeoDataFrame, k: int = DEFAULT_K):
    w = KNN.from_dataframe(gdf, k=k, ids=gdf["province"].tolist())
    w.transform = "r"
    return w


def build_queen_weights(gdf: gpd.GeoDataFrame):
    w = Queen.from_dataframe(gdf, ids=gdf["province"].tolist(), use_index=False)
    w.transform = "r"
    return w


def global_morans_i(gdf: gpd.GeoDataFrame, value_col: str, w, permutations: int = PERMUTATIONS, seed: int = 12345) -> dict:
    """Permutation-based global Moran's I -- the p-value comes from comparing the
    observed statistic against `permutations` random reassignments of the data to
    locations, not a parametric approximation, since province-level data this small
    (n=38) doesn't reliably satisfy the assumptions a parametric test would need."""
    values = gdf.set_index("province").loc[w.id_order, value_col].values
    np.random.seed(seed)  # this esda version's Moran (unlike Moran_Local) has no seed kwarg of its own
    mi = Moran(values, w, permutations=permutations)

    return {
        "statistic": float(mi.I),
        "expected_under_null": float(mi.EI),
        "p_value_permutation": float(mi.p_sim),
        "p_value_normal_approximation": float(mi.p_norm),
        "z_score": float(mi.z_sim),
        "n_permutations": permutations,
        "significant_at_0.05": bool(mi.p_sim < SIGNIFICANCE_LEVEL),
    }


def local_morans_i(gdf: gpd.GeoDataFrame, value_col: str, w, permutations: int = PERMUTATIONS, seed: int = 12345) -> gpd.GeoDataFrame:
    """Returns a copy of gdf with local_i, local_p, and a LISA quadrant
    classification (High-High / Low-Low / High-Low / Low-High) added -- only for
    provinces with a statistically significant local statistic (p < 0.05);
    everything else is labeled 'Not significant' rather than forced into a
    quadrant that the data doesn't actually support."""
    ordered = gdf.set_index("province").loc[w.id_order].reset_index()
    values = ordered[value_col].values

    # alternative="two-sided" set explicitly (esda's upcoming default) rather than
    # relying on the current "directed" default, which this esda version warns is
    # changing -- pinning the choice here means a future esda upgrade can't silently
    # change which provinces this project reports as significant.
    lisa = Moran_Local(values, w, permutations=permutations, seed=seed, alternative="two-sided")

    z = values - values.mean()
    quadrant_labels = {1: "High-High", 2: "Low-High", 3: "Low-Low", 4: "High-Low"}
    quadrants = np.array([quadrant_labels[q] for q in lisa.q])

    significant = lisa.p_sim < SIGNIFICANCE_LEVEL
    classification = np.where(significant, quadrants, "Not significant")

    result = ordered.copy()
    result["local_i"] = lisa.Is
    result["local_p_sim"] = lisa.p_sim
    result["lisa_quadrant"] = quadrants
    result["lisa_significant"] = significant
    result["lisa_cluster"] = classification
    return result
