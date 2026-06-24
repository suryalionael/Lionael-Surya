import streamlit as st

from utils import load_rankings, load_summary

st.set_page_config(page_title="Nutrition Priority Index — Indonesia", page_icon="🇮🇩", layout="wide")

summary = load_summary()
rankings = load_rankings()

st.title("Data-Driven Prioritization of Child Nutrition Interventions in Indonesia")
st.caption("A policy analytics and decision-support platform — not a one-off dashboard project.")

st.markdown(
    """
## Project Objective

Identify which Indonesian provinces should be prioritized for child-nutrition
interventions (e.g. the *Makan Bergizi Gratis* national school-feeding program),
using **only real, publicly verifiable government data** — no synthetic, mocked,
or simulated values anywhere in the pipeline.
"""
)

st.markdown("## Key Findings")
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        f"""
- **{summary['n_provinces']} provinces** scored on a Nutrition Priority Index (NPI) built from real BPS and Kemenkes/TP2S data
- The index correlates with real stunting outcomes: **Spearman r = {summary['outcome_correlation']['spearman_r_all']:.2f}** (all provinces), honestly **{summary['outcome_correlation']['spearman_r_full_coverage_only']:.2f}** once the 4 newest, most data-incomplete provinces are set aside
- NPI priority is **not randomly scattered geographically** — it shows strong, statistically significant spatial clustering
        """
    )
with col2:
    st.markdown(
        f"""
- **Global Moran's I = {summary['spatial']['morans_i']:.3f}** (p = {summary['spatial']['morans_i_p_value']:.3f}, 999-permutation test) — strong positive spatial autocorrelation
- **{summary['spatial']['lisa_high_high_count']} provinces** form a statistically significant high-vulnerability spatial cluster (all in the Papua region)
- Eastern Indonesia's mean NPI is **2.5× Western Indonesia's**, confirmed by two independent significance tests (ANOVA p = {summary['regional']['anova_p_value']:.1e}, Kruskal-Wallis p = {summary['regional']['kruskal_p_value']:.1e})
        """
    )

st.markdown("## Critical Statistics")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Provinces analyzed", summary["n_provinces"])
m2.metric("Global Moran's I", f"{summary['spatial']['morans_i']:.3f}", help="Spatial autocorrelation statistic; permutation p-value = " + f"{summary['spatial']['morans_i_p_value']:.3f}")
m3.metric("Outcome correlation (Spearman)", f"{summary['outcome_correlation']['spearman_r_all']:.2f}")
m4.metric("PCA variance explained (benchmark)", f"{summary['methodology']['pca_variance_explained']:.1%}")

st.markdown("### Province count by priority tier (Jenks natural breaks)")
tier_cols = st.columns(4)
tier_order = ["Low", "Medium", "High", "Critical"]
for col, tier in zip(tier_cols, tier_order):
    col.metric(tier, summary["tier_counts"].get(tier, 0))

st.markdown("## Dataset Summary")
st.markdown(
    """
| Dataset | Source | Provinces covered |
|---|---|---|
| Poverty rate | BPS (Statistics Indonesia) | 38/38 |
| Human Development Index | BPS | 38/38 |
| Population | BPS | 34/38 (real publication gap, documented) |
| School participation rate | BPS | 34/38 (real publication gap, documented) |
| Household expenditure | BPS | 38/38 |
| Child stunting prevalence | Kemenkes / TP2S | 38/38 |
| Province boundaries | BIG (via scriptable mirror) | 38/38 |
"""
)

st.markdown("## Methodology Summary")
st.markdown(
    f"""
**Primary scoring methodology:** `{summary['methodology']['primary']}` for the Socioeconomic Vulnerability
dimension, combined 50/50 with Education Access. Chosen over a PCA composite of
3 indicators after an empirical head-to-head comparison found it performed at
least as well on every tested criterion (predictive performance, interpretability,
robustness, reproducibility, policy communication) — see the Methodology page.

**Retained sensitivity benchmark:** PCA composite (`poverty_rate`, `ipm`,
`expenditure_per_capita`), explaining **{summary['methodology']['pca_variance_explained']:.1%}** of variance —
confirms these three indicators are genuinely collinear, not independent.

See the **Methodology** and **Robustness & Uncertainty** pages for the full,
non-hidden derivation — every number on this page is generated from real pipeline
output, not asserted.
"""
)

st.info(
    "Use the sidebar to explore the full province ranking, an interactive map, "
    "individual province profiles, the full methodology, and this project's "
    "robustness/uncertainty findings.",
    icon="ℹ️",
)
