"""Combines the Socioeconomic Vulnerability composite (src/scoring/pca_composite.py)
and the Education Access dimension into the Nutrition Priority Index, per
docs/phase2_framework_design.md and docs/phase2_weighting_options.md, applying the
missing-data policy from docs/phase3_missing_data_decision.md.

Deliberately produces only a continuous score and diagnostics in this module --
NOT a sorted ranking, percentile, or priority tier. Turning the score into an
ordered ranking is an explicitly separate, not-yet-authorized step (see
docs/phase3_dry_run.md); building that here would make this module's mere existence
produce a ranking artifact every time it runs.
"""

import yaml

import pandas as pd

from src.features.directionality import align_to_higher_is_worse, load_directionality_config
from src.features.missing_value_policy import completeness_flag, renormalize_weights_per_row
from src.features.normalize import min_max_scale
from src.scoring.pca_composite import fit_pca_composite
from src.utils.config import CONFIG_DIR

NPI_WEIGHTS_PATH = CONFIG_DIR / "npi_weights.yml"

SOCIOECONOMIC_COLUMNS = ["poverty_rate", "ipm", "expenditure_per_capita"]
EDUCATION_COLUMN = "participation_rate"


def load_npi_weights(path=NPI_WEIGHTS_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def compute_npi(
    merged_df: pd.DataFrame,
    dimension_weights: dict | None = None,
    socioeconomic_columns: list[str] | None = None,
    include_education: bool = True,
    socioeconomic_single_indicator: str | None = None,
) -> tuple[pd.DataFrame, dict]:
    """merged_df: data/processed/merged_provincial_indicators.csv, loaded.

    dimension_weights/socioeconomic_columns/include_education let validation code
    (src/scoring/validation.py) recompute under a perturbed weighting or a dropped
    indicator without writing temporary config files -- they default to this
    project's actual configured methodology, never silently change it.

    socioeconomic_single_indicator (e.g. "poverty_rate") bypasses PCA entirely and
    uses that one normalized indicator directly as the Socioeconomic Vulnerability
    score -- the "pick one representative indicator" alternative compared in
    docs/phase2_weighting_options.md and evaluated for real in
    docs/phase3_methodology_comparison.md / docs/phase3_final_methodology_decision.md.
    Mutually exclusive with socioeconomic_columns (which controls the PCA-trio
    composition instead).

    If NEITHER override is given, the method is read from
    config/npi_weights.yml's socioeconomic_vulnerability_method.type -- currently
    "single_indicator" (expenditure_per_capita), promoted to primary in Phase 3C.
    The PCA-trio composite remains fully available by passing socioeconomic_columns
    explicitly (used as the retained sensitivity benchmark in
    src/scoring/validation.py and docs/phase4_ranking_results.md).

    Returns (result_df, diagnostics). result_df has one row per province: the two
    dimension scores, the combined npi score, the reach-modifier metric, and the
    data_completeness flag -- no rank, percentile, or tier column (see
    src/scoring/ranking.py for that, built once ranking was explicitly authorized
    in Phase 4).
    """
    npi_config = load_npi_weights()
    directionality_config = load_directionality_config()
    weights = dict(dimension_weights) if dimension_weights is not None else dict(npi_config["dimension_weights"])
    if not include_education:
        weights.pop("education_access", None)

    if socioeconomic_columns is None and socioeconomic_single_indicator is None:
        method_config = npi_config["socioeconomic_vulnerability_method"]
        if method_config["type"] == "single_indicator":
            socioeconomic_single_indicator = method_config["indicator"]
        elif method_config["type"] == "pca":
            socioeconomic_columns = npi_config.get("pca_benchmark", {}).get("columns", SOCIOECONOMIC_COLUMNS)
        else:
            raise ValueError(f"Unknown socioeconomic_vulnerability_method.type: {method_config['type']!r}")

    aligned = align_to_higher_is_worse(merged_df, directionality_config)

    edu_diag = {}
    if include_education:
        edu_input, edu_diag = min_max_scale(aligned, [EDUCATION_COLUMN])

    if socioeconomic_single_indicator is not None:
        socio_input, socio_diag = min_max_scale(aligned, [socioeconomic_single_indicator])
        socioeconomic_vulnerability = socio_input[socioeconomic_single_indicator]
        pca_diag = {"method": "single_indicator", "indicator": socioeconomic_single_indicator}
    else:
        socio_input, socio_diag = min_max_scale(aligned, socioeconomic_columns)
        pca_benchmark_config = npi_config.get("pca_benchmark", {})
        socioeconomic_vulnerability, pca_diag = fit_pca_composite(
            socio_input, socioeconomic_columns, n_components=pca_benchmark_config.get("n_components", 1)
        )
        pca_diag["method"] = "pca"

        # Rescale the PCA composite to [0, 1] for interpretability alongside education_access,
        # which is already on a [0, 1] scale from min_max_scale.
        socioeconomic_vulnerability, socio_pca_scale_diag = min_max_scale(
            pd.DataFrame({"socioeconomic_vulnerability": socioeconomic_vulnerability}), ["socioeconomic_vulnerability"]
        )
        socioeconomic_vulnerability = socioeconomic_vulnerability["socioeconomic_vulnerability"]

    dimension_scores = pd.DataFrame({"socioeconomic_vulnerability": socioeconomic_vulnerability}, index=merged_df.index)
    if include_education:
        dimension_scores["education_access"] = edu_input[EDUCATION_COLUMN]

    effective_weights, npi = renormalize_weights_per_row(dimension_scores, weights)
    completeness = completeness_flag(dimension_scores, weights)

    result = pd.DataFrame(
        {
            "province": merged_df["province"],
            "socioeconomic_vulnerability": dimension_scores["socioeconomic_vulnerability"],
            "education_access": dimension_scores["education_access"] if include_education else float("nan"),
            "npi": npi,
            "data_completeness": completeness,
            "estimated_children_affected": merged_df["population"] * merged_df["stunting_rate"] / 100.0,
            "stunting_rate": merged_df["stunting_rate"],
            "stunting_category": merged_df["stunting_category"],
        }
    )

    diagnostics = {
        "normalization": {**socio_diag, **edu_diag},
        "pca": pca_diag,
        "effective_weights_sample": effective_weights,
    }
    return result, diagnostics
