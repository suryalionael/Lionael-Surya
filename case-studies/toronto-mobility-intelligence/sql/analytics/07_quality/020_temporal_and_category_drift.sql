-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md G1/G3, monitoring framing): (1) does the
-- completeness of a key categorical field (road_class) hold steady across years, or has
-- something changed recently in how the source data is populated? (2) which years show an
-- unusually large year-over-year swing in KSI count that would warrant a second look before
-- being reported as a real trend?
--
-- Metric definition:
--   null_road_class_pct = 100 * (collisions with road_class IS NULL) / total_ksi_collisions
--   yoy_ksi_change_pct  = from analytics.v_annual_ksi (01_temporal/010_annual_ksi_trend.sql)
--   unusual_yoy_flag    = |yoy_ksi_change_pct| > 20 -- a threshold chosen by inspecting the
--       actual year-over-year swings in this dataset, most of which fall within +/-15%
--
-- Grain: one row per year.
--
-- Limitation: a NULL-rate spike is a prompt to investigate, not proof of a real data problem
-- -- it could reflect a genuine backlog in the City's own classification process for very
-- recent records rather than an error in this project's pipeline. Cross-check against
-- staging.ingestion_log's city_last_refreshed date and the KSI verification-lag note in
-- docs/DATASET_RESEARCH.md before concluding anything is actually wrong.
-- =============================================================================

WITH completeness AS (
    SELECT
        d.year,
        COUNT(DISTINCT f.collision_id) AS total_ksi_collisions,
        COUNT(DISTINCT f.collision_id) FILTER (WHERE f.road_class IS NULL) AS null_road_class_collisions
    FROM analytics.fact_collisions f
    JOIN analytics.dim_date d ON d.date_key = f.date_key
    WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
    GROUP BY d.year
)
SELECT
    c.year,
    c.total_ksi_collisions,
    ROUND(100.0 * c.null_road_class_collisions / NULLIF(c.total_ksi_collisions, 0), 2) AS null_road_class_pct,
    a.yoy_ksi_change_pct,
    CASE WHEN ABS(a.yoy_ksi_change_pct) > 20 THEN 'REVIEW -- YoY swing exceeds +/-20%' ELSE NULL END AS unusual_yoy_flag,
    CASE WHEN 100.0 * c.null_road_class_collisions / NULLIF(c.total_ksi_collisions, 0) > 10
         THEN 'REVIEW -- road_class completeness dropped below 90%' ELSE NULL END AS category_drift_flag
FROM completeness c
JOIN analytics.v_annual_ksi a ON a.year = c.year
ORDER BY c.year;
