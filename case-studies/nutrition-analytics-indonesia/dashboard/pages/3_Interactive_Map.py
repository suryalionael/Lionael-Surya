import json
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import TIER_ORDER, load_lisa, load_spatial

st.set_page_config(page_title="Interactive Map", layout="wide")
st.title("Interactive Map")
st.caption("Switch between NPI score, priority tier, and spatial cluster (LISA) views.")

gdf = load_spatial()
lisa = load_lisa()
gdf = gdf.merge(lisa, on="province", how="left")

view = st.radio("View", ["NPI Score", "Priority Tier", "Spatial Cluster (LISA)"], horizontal=True)

geojson = json.loads(gdf.to_json())
hover_data = {"rank": True, "tier_jenks": True, "npi": ":.3f", "stunting_rate": ":.1f"}

if view == "NPI Score":
    fig = px.choropleth(
        gdf, geojson=geojson, locations="province", featureidkey="properties.province",
        color="npi", color_continuous_scale="OrRd", hover_name="province", hover_data=hover_data,
    )
elif view == "Priority Tier":
    fig = px.choropleth(
        gdf, geojson=geojson, locations="province", featureidkey="properties.province",
        color="tier_jenks", category_orders={"tier_jenks": TIER_ORDER},
        color_discrete_map={"Low": "#2c7bb6", "Medium": "#ffffbf", "High": "#fdae61", "Critical": "#d7191c"},
        hover_name="province", hover_data=hover_data,
    )
else:
    fig = px.choropleth(
        gdf, geojson=geojson, locations="province", featureidkey="properties.province",
        color="lisa_cluster",
        color_discrete_map={"High-High": "#d7191c", "Low-Low": "#2c7bb6", "High-Low": "#fdae61", "Low-High": "#abd9e9", "Not significant": "#e0e0e0"},
        hover_name="province", hover_data={**hover_data, "local_p_sim": ":.3f"},
    )

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(height=650, margin=dict(l=0, r=0, t=20, b=0))
st.plotly_chart(fig, width='stretch')

if view == "Spatial Cluster (LISA)":
    st.caption(
        "Significant clusters only (p < 0.05, two-sided permutation test, KNN k=6 neighbors). "
        "'Not significant' provinces show no statistically detectable local clustering — "
        "shown in gray, not hidden."
    )
