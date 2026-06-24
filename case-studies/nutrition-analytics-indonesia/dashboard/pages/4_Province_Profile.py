import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import load_lisa, load_merged_indicators, load_rankings

st.set_page_config(page_title="Province Profile", layout="wide")
st.title("Province Profile")

rankings = load_rankings()
merged = load_merged_indicators()
lisa = load_lisa()

province = st.selectbox("Select a province", sorted(rankings["province"].unique()))

row = rankings[rankings["province"] == province].iloc[0]
ind = merged[merged["province"] == province].iloc[0]
lisa_row = lisa[lisa["province"] == province]
lisa_label = lisa_row.iloc[0]["lisa_cluster"] if not lisa_row.empty else "Not significant"

st.markdown(f"## {province}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rank", f"{int(row['rank'])} / {len(rankings)}")
c2.metric("Percentile", f"{row['percentile']:.1f}")
c3.metric("NPI Score", f"{row['npi']:.3f}")
c4.metric("Priority Tier", row["tier_jenks"])

st.metric("Spatial classification (LISA)", lisa_label, help="Significant only if p < 0.05; 'Not significant' means no detectable local spatial clustering for this province.")

st.markdown("### Indicators vs. national median")

indicator_specs = [
    ("Poverty rate (%)", "poverty_rate", "inverse"),
    ("Human Development Index", "ipm", "normal"),
    ("Population (thousands)", "population", "off"),  # scale/reach metric, not a vulnerability indicator -- see docs/phase2_framework_design.md
    ("School participation rate, age 7-12 (%)", "participation_rate", "normal"),
    ("Household expenditure per capita (thousand IDR/year)", "expenditure_per_capita", "normal"),
    ("Child stunting prevalence (%)", "stunting_rate", "inverse"),
]

cols = st.columns(3)
for i, (label, col, delta_color) in enumerate(indicator_specs):
    value = ind[col]
    median = merged[col].median()
    with cols[i % 3]:
        if pd.isna(value):
            st.metric(label, "Not available", help="BPS has not yet republished this series for this province (real data gap, not imputed).")
        else:
            delta = value - median
            st.metric(label, f"{value:,.1f}", delta=f"{delta:+.1f} vs. national median", delta_color=delta_color)

st.caption(
    "Stunting prevalence and category are reported as outcome context, not a "
    "weighted input to the NPI score (see Methodology page) — included here for "
    "interpretation, not as part of the ranking calculation."
)
st.markdown(f"**Stunting category (Kemenkes):** {ind['stunting_category']}")
