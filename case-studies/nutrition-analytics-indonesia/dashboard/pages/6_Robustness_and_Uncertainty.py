import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import load_summary

st.set_page_config(page_title="Robustness & Uncertainty", layout="wide")
st.title("Robustness & Uncertainty")

summary = load_summary()

st.warning(
    "**Ranks are highly stable; adaptive tiers are less stable.** "
    "Read this page before treating any tier boundary as a hard cutoff.",
    icon="⚠️",
)

st.markdown("## Weight Sensitivity")
st.markdown(
    """
The NPI's top-level weighting (50% Socioeconomic Vulnerability, 50% Education
Access) was perturbed ±20% in 10-point increments. Rank order stayed highly
stable throughout: **Spearman rank correlation never dropped below 0.99**, and
the top-5 and top-10 province sets were unchanged or nearly unchanged at every
grid point (`docs/phase4_ranking_results.md`).
"""
)

st.markdown("## Rank Stability vs. Tier Instability")
col1, col2 = st.columns(2)
with col1:
    st.metric("Rank order Spearman r (±20% weight range)", "> 0.99", help="Highly stable across every tested perturbation.")
with col2:
    st.metric("Provinces reclassified to a different Jenks tier (±20% weight range)", "up to 76%", help="Recomputing breakpoints fresh on each scenario can dramatically change tier labels even when rank order barely moves.")

st.markdown(
    """
**Why these two numbers disagree so much:** Jenks natural breaks recomputes its
tier boundaries fresh against whatever score distribution it's given. When the
underlying scores shift slightly, the algorithm adaptively redraws its boundaries
to fit the new distribution — which can mask real score movement (because the
boundary moves *with* the data) or, conversely, reclassify many provinces near a
boundary even though their relative *rank* barely changed. Applying a **fixed**
reference breakpoint instead — "did this score cross a fixed line" — reveals
real movement that an adaptively-recomputed breakpoint hides
(`docs/phase4_ranking_results.md`).

**Practical takeaway:** trust the rank and percentile columns more than the tier
label for any province sitting near a tier boundary — `npi_rankings.csv` flags
these explicitly with a `tier_boundary_flag` column (8 of 38 provinces, 21%, are
flagged).
"""
)

st.markdown("## Methodology Comparison Summary")
st.markdown(
    f"""
| Criterion | PCA | Single-indicator (expenditure_per_capita) | Winner |
|---|---|---|---|
| Predictive performance (outcome correlation) | Spearman r = 0.72 | Spearman r = 0.74 | Single-indicator |
| Interpretability | Requires explaining a statistical component | "Average spending per person" | Single-indicator |
| Robustness (weight sensitivity) | Stable | Stable | Tied |
| Reproducibility | Loadings depend on the dataset's current covariance | No fitted parameters | Single-indicator |
| Policy communication | Lower (opaque to non-technical audiences) | Higher | Single-indicator |
| **Decision matrix score** | **13/25** | **23/25** | **Single-indicator promoted to primary** |

PCA's textbook rationale (avoid double-counting 3 collinear indicators,
confirmed at **{summary['methodology']['pca_variance_explained']:.1%}** variance
explained) was correct — it simply didn't translate into a measurably better
index on this dataset's current snapshot. PCA is retained as a documented
sensitivity benchmark precisely so a future data update can be checked against
it (`docs/phase3_final_methodology_decision.md`).
"""
)

st.markdown("## Outcome Correlation Caveat")
st.markdown(
    f"""
The headline outcome correlation (Spearman r = **{summary['outcome_correlation']['spearman_r_all']:.2f}**, all 38
provinces) is partly inflated by the 4 partial-coverage provinces' statistical
extremity. The more conservative, honest figure — restricted to the 34 provinces
with complete indicator coverage — is **{summary['outcome_correlation']['spearman_r_full_coverage_only']:.2f}**.
Both are reported throughout this project's documentation; neither is hidden in
favor of the more flattering number.
"""
)

st.markdown("## Spatial Robustness")
st.markdown(
    """
The spatial clustering finding (Page 3, and `docs/phase5_spatial_results.md`) was
tested against 4 different neighbor definitions (KNN k=4/6/8, Queen contiguity)
and 2 different province-geometry reconciliation choices — every configuration
remained statistically significant at p = 0.001. The one meaningful difference
found (a single province flipping to a spurious spatial outlier under the
less-precise geometry choice) is evidence *for* this project's chosen geometry
source, not a weakness in the finding.
"""
)
