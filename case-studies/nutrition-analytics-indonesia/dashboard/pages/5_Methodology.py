import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import load_summary

st.set_page_config(page_title="Methodology", layout="wide")
st.title("Methodology")
st.caption("Every decision below is documented in full, with real evidence, in this repository's docs/ folder. No hidden methodology.")

summary = load_summary()
assets_dir = Path(__file__).parent.parent.parent / "reports" / "portfolio_assets"

st.markdown("## Data Pipeline")
pipeline_img = assets_dir / "data_pipeline_diagram.png"
if pipeline_img.exists():
    st.image(str(pipeline_img), width='stretch')
st.markdown(
    """
**7 real datasets**, sourced from BPS (Statistics Indonesia) via its WebAPI with
every variable id confirmed by live query — never guessed — and Kemenkes/TP2S for
stunting prevalence (manually exported, no scriptable source exists, see
`docs/known_limitations.md`). Province boundaries sourced from a scriptable
mirror of BIG's official shapefiles, giving distinct geometry for all 38 current
provinces.
"""
)

st.markdown("## Cleaning Pipeline")
st.markdown(
    """
Every raw dataset is standardized through a single province-name reference layer
(`src/reference/`), with non-province aggregate rows (e.g. an `INDONESIA` national
total row BPS includes alongside the 38 real provinces) dropped explicitly, never
matched by coincidence. Missing values are never imputed — `population` and
`participation_rate` are genuinely missing for the 4 provinces created by
Indonesia's 2022 administrative split, because BPS has not yet republished those
two series for them; this is documented and handled via per-province dimension-
weight renormalization, not estimation.
"""
)

st.markdown("## Validation Framework")
st.markdown(
    f"""
Every dataset has a YAML data contract (`docs/data_contracts/`) enforced before a
fetch counts as successful — schema, plausible province count, numeric ranges.
The scoring methodology itself was validated against real outcomes before any
ranking was published: outcome correlation (Spearman r = {summary['outcome_correlation']['spearman_r_all']:.2f}),
weight-perturbation sensitivity, leave-one-indicator-out analysis, and PCA basis
stability (`docs/phase3_validation_results.md`).
"""
)

st.markdown("## PCA vs. Single-Indicator Comparison")
methodology_img = assets_dir / "methodology_diagram.png"
if methodology_img.exists():
    st.image(str(methodology_img), width='stretch')
st.markdown(
    f"""
The Socioeconomic Vulnerability dimension combines `poverty_rate`, `ipm`, and
`expenditure_per_capita` — three indicators confirmed collinear (PCA's first
component explains **{summary['methodology']['pca_variance_explained']:.1%}** of
their combined variance, `docs/phase2_indicator_audit.md`). Two approaches were
empirically compared, not just discussed in the abstract:

- **PCA composite** — the textbook-correct way to combine genuinely collinear
  indicators without double-counting.
- **Single representative indicator** (`expenditure_per_capita` alone) —
  empirically performed at least as well on outcome correlation and rank
  stability, while being far more interpretable to a non-technical audience.

**Decision:** `expenditure_per_capita`-only was promoted to the primary
methodology; PCA is retained as a documented sensitivity benchmark, not deleted —
see `docs/phase3_final_methodology_decision.md` for the full decision matrix
(predictive performance, interpretability, robustness, reproducibility, policy
communication).
"""
)

st.markdown("## Architecture")
arch_img = assets_dir / "architecture_diagram.png"
if arch_img.exists():
    st.image(str(arch_img), width='stretch')

st.markdown("## Full documentation index")
st.markdown(
    """
| Phase | Documents |
|---|---|
| 0 — Data acquisition | `docs/data_inventory.md`, `docs/known_limitations.md` |
| 1 — Cleaning | `docs/province_reconciliation.md`, `docs/missing_data_report.md` |
| 2 — NPI design | `docs/phase2_indicator_audit.md`, `docs/phase2_framework_design.md`, `docs/phase2_weighting_options.md` |
| 3 — Scoring & validation | `docs/phase3_validation_results.md`, `docs/phase3_methodology_comparison.md`, `docs/phase3_final_methodology_decision.md` |
| 4 — Ranking & tiers | `docs/phase4_ranking_design.md`, `docs/phase4_ranking_results.md` |
| 5 — Spatial analysis | `docs/phase5_geometry_reconciliation.md`, `docs/phase5_spatial_results.md` |
"""
)
