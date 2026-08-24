-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md F2): Which neighbourhoods have shown the
-- largest change in KSI collisions -- where is the pattern improving or worsening?
--
-- Metric definition: two non-overlapping, equal-length 5-year windows are compared instead of
-- a year-over-year LAG across all 158 neighbourhoods x 21 years (which would produce ~3,300
-- mostly-noisy single-year deltas). Windows: "recent" = 2021-2025, "prior" = 2016-2020 (both
-- are complete calendar years -- 2026 is excluded as a partial year, see
-- 01_temporal/010_annual_ksi_trend.sql).
--   pct_change = 100 * (recent_count - prior_count) / prior_count
--
-- Grain: one row per neighbourhood, restricted to neighbourhoods with >=10 KSI collisions in
-- the prior window (a minimum base-count threshold, per ANALYTICAL_QUESTIONS.md F2's explicit
-- caution about small-base percentage swings -- a neighbourhood going from 2 to 4 collisions
-- is a meaningless "+100%" and is excluded here, not flagged as a top mover).
--
-- Limitation: five years is still a short window for 158 small-area geographies: even with the
-- >=10 threshold, single-neighbourhood swings can reflect one or two unusual years rather than
-- a durable trend. Read this as a screening list for further investigation, not a verdict.
-- Also note: both windows contain one COVID-affected low-traffic year each (2020 in "prior",
-- 2021 in "recent") -- this is roughly symmetric, not a one-sided bias, but the citywide-wide
-- decline visible across most neighbourhoods in this comparison should not be read as proof of
-- a Vision Zero effect without ruling out reduced overall travel volume as a contributor.
-- =============================================================================

WITH periods AS (
    SELECT
        n.area_name,
        COUNT(DISTINCT f.collision_id) FILTER (
            WHERE d.year BETWEEN 2016 AND 2020
        ) AS prior_5yr_count,
        COUNT(DISTINCT f.collision_id) FILTER (
            WHERE d.year BETWEEN 2021 AND 2025
        ) AS recent_5yr_count
    FROM analytics.fact_collisions f
    JOIN analytics.dim_date d ON d.date_key = f.date_key
    JOIN analytics.dim_neighbourhood n ON n.neighbourhood_key = f.neighbourhood_key
    WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
    GROUP BY n.area_name
)
SELECT
    area_name,
    prior_5yr_count,
    recent_5yr_count,
    ROUND(100.0 * (recent_5yr_count - prior_5yr_count) / NULLIF(prior_5yr_count, 0), 1) AS pct_change,
    RANK() OVER (ORDER BY (recent_5yr_count - prior_5yr_count) DESC) AS rank_worsened,
    RANK() OVER (ORDER BY (recent_5yr_count - prior_5yr_count) ASC) AS rank_improved
FROM periods
WHERE prior_5yr_count >= 10
ORDER BY pct_change DESC;
