import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import TIER_ORDER, load_rankings

st.set_page_config(page_title="Priority Ranking Explorer", layout="wide")
st.title("Priority Ranking Explorer")
st.caption("Full province ranking — sort, filter, search, and export.")

rankings = load_rankings()

col1, col2 = st.columns([2, 1])
with col1:
    search = st.text_input("Search province", "")
with col2:
    tier_filter = st.multiselect("Filter by tier (Jenks)", TIER_ORDER, default=TIER_ORDER)

filtered = rankings[rankings["tier_jenks"].isin(tier_filter)]
if search:
    filtered = filtered[filtered["province"].str.contains(search, case=False, na=False)]

display_cols = ["rank", "province", "percentile", "npi", "tier_jenks", "data_completeness", "stunting_rate"]
st.dataframe(
    filtered[display_cols].sort_values("rank"),
    width='stretch',
    hide_index=True,
    column_config={
        "rank": st.column_config.NumberColumn("Rank"),
        "province": st.column_config.TextColumn("Province"),
        "percentile": st.column_config.ProgressColumn("Percentile", min_value=0, max_value=100, format="%.1f"),
        "npi": st.column_config.NumberColumn("NPI Score", format="%.3f"),
        "tier_jenks": st.column_config.TextColumn("Priority Tier"),
        "data_completeness": st.column_config.TextColumn("Data Completeness"),
        "stunting_rate": st.column_config.NumberColumn("Stunting Rate (%)", format="%.1f"),
    },
)

st.caption(f"Showing {len(filtered)} of {len(rankings)} provinces.")

st.download_button(
    "Download filtered results as CSV",
    data=filtered[display_cols].sort_values("rank").to_csv(index=False),
    file_name="npi_rankings_filtered.csv",
    mime="text/csv",
)

st.caption(
    "Tier labels (Jenks natural breaks) are less stable under methodology "
    "perturbation than rank order — see the Robustness & Uncertainty page before "
    "treating a tier boundary as a hard cutoff."
)
