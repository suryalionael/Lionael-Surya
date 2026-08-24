-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md A1/A2/B3): Is the citywide count of people
-- killed or seriously injured trending up, down, or flat since 2006, and what share of that
-- is fatal in a given year?
--
-- Metric definition:
--   ksi_collision_count = COUNT(DISTINCT collision_id) WHERE acclass IN
--                          ('Fatal Injury', 'Non-Fatal Injury')
--   fatal_collision_count = COUNT(DISTINCT collision_id) WHERE acclass = 'Fatal Injury'
--   fatal_share_pct       = 100 * fatal_collision_count / ksi_collision_count
--   yoy_ksi_change_pct    = 100 * (this year - last year) / last year, via LAG()
--
-- Grain: one row per calendar year (2006-2026).
--
-- Limitation: acclass is confirmed collision-level (identical across every person-row of a
-- given collision_id -- verified with zero exceptions during Phase 2 build), so COUNT(DISTINCT
-- collision_id) is exact, not an approximation. The final year in the series is a partial year
-- (flagged via is_current_year_partial) and the trailing ~1-3 months of any year are likely
-- under-reported due to KSI's documented verification lag (DATASET_RESEARCH.md) -- do not read
-- a dip in the most recent year(s) as a real decline without checking G3's reporting-lag check.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.v_annual_ksi AS
WITH yearly AS (
    SELECT
        d.year,
        COUNT(DISTINCT f.collision_id)
            FILTER (WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')) AS ksi_collision_count,
        COUNT(DISTINCT f.collision_id)
            FILTER (WHERE f.acclass = 'Fatal Injury') AS fatal_collision_count
    FROM analytics.fact_collisions f
    JOIN analytics.dim_date d ON d.date_key = f.date_key
    GROUP BY d.year
)
SELECT
    year,
    ksi_collision_count,
    fatal_collision_count,
    ROUND(100.0 * fatal_collision_count / NULLIF(ksi_collision_count, 0), 2) AS fatal_share_pct,
    ROUND(
        100.0 * (ksi_collision_count - LAG(ksi_collision_count) OVER (ORDER BY year))
        / NULLIF(LAG(ksi_collision_count) OVER (ORDER BY year), 0),
        2
    ) AS yoy_ksi_change_pct,
    (year = EXTRACT(YEAR FROM CURRENT_DATE)::int) AS is_current_year_partial
FROM yearly
ORDER BY year;
