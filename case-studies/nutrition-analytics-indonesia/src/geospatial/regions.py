"""Groups provinces into Western / Central / Eastern Indonesia using Indonesia's
official, legally-defined time zones (WIB/WITA/WIT) as the regional boundary --
chosen instead of inventing an ad hoc grouping, since the time zones are a real,
government-defined partition of the country that maps directly onto "Western /
Central / Eastern" without any subjective boundary-drawing by this project.
"""

import pandas as pd
from scipy import stats

REGION_MAP: dict[str, str] = {
    # WIB (Western Indonesia Time, UTC+7) -> Western Indonesia: Sumatra, Java, West/Central Kalimantan
    "Aceh": "Western", "Sumatera Utara": "Western", "Sumatera Barat": "Western", "Riau": "Western",
    "Kep. Riau": "Western", "Jambi": "Western", "Sumatera Selatan": "Western", "Bengkulu": "Western",
    "Lampung": "Western", "Kep. Bangka Belitung": "Western", "Dki Jakarta": "Western", "Jawa Barat": "Western",
    "Jawa Tengah": "Western", "Di Yogyakarta": "Western", "Jawa Timur": "Western", "Banten": "Western",
    "Kalimantan Barat": "Western", "Kalimantan Tengah": "Western",
    # WITA (Central Indonesia Time, UTC+8) -> Central Indonesia: Bali, Nusa Tenggara, South/East/North Kalimantan, Sulawesi
    "Bali": "Central", "Nusa Tenggara Barat": "Central", "Nusa Tenggara Timur": "Central",
    "Kalimantan Selatan": "Central", "Kalimantan Timur": "Central", "Kalimantan Utara": "Central",
    "Sulawesi Utara": "Central", "Sulawesi Tengah": "Central", "Sulawesi Selatan": "Central",
    "Sulawesi Tenggara": "Central", "Gorontalo": "Central", "Sulawesi Barat": "Central",
    # WIT (Eastern Indonesia Time, UTC+9) -> Eastern Indonesia: Maluku, Papua region
    "Maluku": "Eastern", "Maluku Utara": "Eastern", "Papua": "Eastern", "Papua Barat": "Eastern",
    "Papua Barat Daya": "Eastern", "Papua Pegunungan": "Eastern", "Papua Selatan": "Eastern", "Papua Tengah": "Eastern",
}

REGION_ORDER = ["Western", "Central", "Eastern"]


def assign_region(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["region"] = df["province"].map(REGION_MAP)
    unmapped = df.loc[df["region"].isna(), "province"].tolist()
    if unmapped:
        raise KeyError(f"No region mapping for: {unmapped} -- add to REGION_MAP rather than silently leaving them unclassified.")
    return df


def regional_summary(df: pd.DataFrame, value_col: str = "npi") -> pd.DataFrame:
    """Mean, median, variance, and tier distribution per region. Provinces are
    independent observations within a region; this does not (and should not) double
    as a spatial-autocorrelation test -- that's the LISA analysis's job."""
    df = assign_region(df)
    summary = (
        df.groupby("region")[value_col]
        .agg(n="count", mean="mean", median="median", variance="var", std="std")
        .reindex(REGION_ORDER)
    )
    return summary


def regional_tier_distribution(df: pd.DataFrame, tier_col: str = "tier_jenks") -> pd.DataFrame:
    df = assign_region(df)
    return pd.crosstab(df["region"], df[tier_col]).reindex(REGION_ORDER)


def regional_disparity_test(df: pd.DataFrame, value_col: str = "npi") -> dict:
    """Tests whether the 3 regions' NPI distributions genuinely differ, using both
    one-way ANOVA (parametric) and Kruskal-Wallis (rank-based, robust to the
    right-skewed NPI distribution already confirmed in docs/phase4_ranking_design.md)
    -- reporting both rather than picking whichever gives the more flattering
    p-value."""
    df = assign_region(df)
    groups = [df.loc[df["region"] == region, value_col].dropna().values for region in REGION_ORDER]

    f_stat, anova_p = stats.f_oneway(*groups)
    h_stat, kruskal_p = stats.kruskal(*groups)

    return {
        "anova_f_statistic": float(f_stat),
        "anova_p_value": float(anova_p),
        "kruskal_h_statistic": float(h_stat),
        "kruskal_p_value": float(kruskal_p),
        "significant_at_0.05_anova": bool(anova_p < 0.05),
        "significant_at_0.05_kruskal": bool(kruskal_p < 0.05),
        "group_sizes": {region: len(g) for region, g in zip(REGION_ORDER, groups)},
    }
