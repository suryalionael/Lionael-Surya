"""Generates the 3 static diagrams referenced by the Methodology dashboard page
and the portfolio docs: an architecture diagram, a data pipeline diagram, and a
methodology (PCA vs single-indicator) diagram. Simple box-and-arrow matplotlib
diagrams -- no extra dependency (graphviz etc.) needed, and easy to regenerate if
the pipeline structure changes.

Usage: python -m dashboard.generate_diagrams
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from src.utils.config import ROOT

OUT_DIR = ROOT / "reports" / "portfolio_assets"


def _box(ax, x, y, w, h, text, color="#e8f0fe", fontsize=10):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", facecolor=color, edgecolor="#333333", linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, wrap=True)


def _arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color="#333333", lw=1.5))


def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title("Repository Architecture", fontsize=14, fontweight="bold")

    layers = [
        ("src/ingestion/\n(BPS, Kemenkes,\nBIG fetchers)", "#fde2e2"),
        ("src/cleaning/\n+ src/reference/\n(standardize, merge)", "#fff3cd"),
        ("src/features/\n+ src/scoring/\n(NPI, ranking,\nvalidation)", "#d4edda"),
        ("src/geospatial/\n(Moran's I, LISA,\nregions, maps)", "#d1ecf1"),
        ("dashboard/\n(Streamlit app)", "#e2d9f3"),
    ]
    w = 2.2
    gap = 0.3
    for i, (label, color) in enumerate(layers):
        x = i * (w + gap) + 0.2
        _box(ax, x, 2, w, 1.6, label, color=color, fontsize=9)
        if i > 0:
            _arrow(ax, x - gap, 2.8, x, 2.8)

    _box(ax, 0.2, 0.3, w, 1.0, "data/raw/\ndata/processed/\n(gitignored)", color="#f0f0f0", fontsize=8)
    _box(ax, 4 * (w + gap) + 0.2 - 1.0, 0.3, w, 1.0, "docs/\n(per-phase design\n+ results)", color="#f0f0f0", fontsize=8)

    fig.savefig(OUT_DIR / "architecture_diagram.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_data_pipeline_diagram():
    fig, ax = plt.subplots(figsize=(13, 4))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4)
    ax.axis("off")
    ax.set_title("Data Pipeline: Real Sources to Final Ranking", fontsize=14, fontweight="bold")

    stages = [
        "BPS WebAPI\n(5 datasets)\nKemenkes (stunting)\nBIG (boundaries)",
        "Ingestion +\nvalidation\n(data contracts)",
        "Cleaning +\nprovince\nreconciliation",
        "Feature\nengineering\n(normalize, align)",
        "NPI scoring\n(expenditure-only\n+ PCA benchmark)",
        "Ranking +\npriority tiers",
        "Spatial analysis\n(Moran's I, LISA)",
        "Dashboard",
    ]
    w = 1.4
    gap = 0.2
    for i, label in enumerate(stages):
        x = i * (w + gap) + 0.1
        _box(ax, x, 1.2, w, 1.6, label, color="#e8f0fe", fontsize=7.5)
        if i > 0:
            _arrow(ax, x - gap, 2.0, x, 2.0)

    fig.savefig(OUT_DIR / "data_pipeline_diagram.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_methodology_diagram():
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title("Socioeconomic Vulnerability: Two Methodologies Compared", fontsize=13, fontweight="bold")

    _box(ax, 0.3, 3.2, 2.8, 1.2, "poverty_rate\nipm\nexpenditure_per_capita\n(collinear, r up to 0.88)", color="#fff3cd", fontsize=8.5)
    _arrow(ax, 3.1, 4.3, 4.3, 4.3)
    _box(ax, 4.3, 3.7, 2.6, 1.0, "PCA composite\n(86% variance explained)", color="#d1ecf1", fontsize=8.5)
    _arrow(ax, 3.1, 3.2, 4.3, 3.2)
    _box(ax, 4.3, 2.7, 2.6, 0.8, "expenditure_per_capita\nalone", color="#d4edda", fontsize=8.5)

    _arrow(ax, 6.9, 4.2, 8.1, 3.8)
    _arrow(ax, 6.9, 3.1, 8.1, 3.5)
    _box(ax, 8.1, 3.0, 2.6, 1.2, "Decision matrix:\nexpenditure-only 23/25\nPCA 13/25\n-> primary methodology", color="#e2d9f3", fontsize=8.5)

    ax.text(5.5, 1.5, "PCA retained as a documented sensitivity benchmark, not deleted.\nSee docs/phase3_final_methodology_decision.md", ha="center", fontsize=9, style="italic")

    fig.savefig(OUT_DIR / "methodology_diagram.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_architecture_diagram()
    generate_data_pipeline_diagram()
    generate_methodology_diagram()
    print(f"Wrote 3 diagrams to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
