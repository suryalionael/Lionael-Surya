"""Collapses the (correlated) Socioeconomic Vulnerability indicator trio --
poverty_rate, ipm, expenditure_per_capita -- into one composite score via PCA, per
the hybrid weighting method recommended in docs/phase2_weighting_options.md.

Uses svd_solver="full" deliberately: it's deterministic (no random initialization),
so re-running against identical input always produces identical loadings and
scores -- a reproducibility requirement from docs/phase2_technical_design.md.
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

MIN_VARIANCE_EXPLAINED = 0.5  # below this, the indicators aren't collinear enough to justify PCA -- see raise below


def fit_pca_composite(normalized_df: pd.DataFrame, columns: list[str], n_components: int = 1) -> tuple[pd.Series, dict]:
    """normalized_df: already directionality-aligned (higher = worse) and min-max
    scaled (src/features). Rows with any null in `columns` are excluded from the PCA
    fit and left null in the output -- PCA cannot be fit through missing values, and
    this project never imputes to work around that.

    Returns (composite_score, diagnostics). diagnostics includes loadings and
    variance explained, for the transparency this method specifically needs
    (docs/phase2_weighting_options.md notes PCA is the least interpretable option by
    default -- reporting loadings/variance explained is the mitigation).
    """
    complete_mask = normalized_df[columns].notna().all(axis=1)
    fit_data = normalized_df.loc[complete_mask, columns]

    if fit_data.empty:
        raise ValueError(f"No rows with complete data across {columns} -- cannot fit PCA.")

    pca = PCA(n_components=n_components, svd_solver="full")
    transformed = pca.fit_transform(fit_data.values)

    variance_explained = float(pca.explained_variance_ratio_[0])
    if variance_explained < MIN_VARIANCE_EXPLAINED:
        raise ValueError(
            f"First principal component explains only {variance_explained:.1%} of variance across {columns} "
            f"(threshold: {MIN_VARIANCE_EXPLAINED:.0%}) -- these indicators may not be collinear enough to "
            "justify a single PCA composite. Revisit the methodology in docs/phase2_weighting_options.md "
            "rather than using this composite as-is."
        )

    loadings = dict(zip(columns, pca.components_[0].tolist()))

    # PCA's sign is arbitrary (a component and its negation explain the same variance).
    # Force the convention documented throughout this project: higher composite = more
    # vulnerable. Since inputs are already aligned higher=worse, loadings should be
    # predominantly positive; flip the whole component if they're predominantly negative.
    if sum(loadings.values()) < 0:
        loadings = {k: -v for k, v in loadings.items()}
        transformed = -transformed

    composite = pd.Series(np.nan, index=normalized_df.index, name="socioeconomic_vulnerability")
    composite.loc[complete_mask] = transformed[:, 0]

    diagnostics = {
        "columns": columns,
        "loadings": loadings,
        "variance_explained": variance_explained,
        "n_provinces_fit": int(complete_mask.sum()),
        "n_provinces_excluded": int((~complete_mask).sum()),
    }
    return composite, diagnostics
