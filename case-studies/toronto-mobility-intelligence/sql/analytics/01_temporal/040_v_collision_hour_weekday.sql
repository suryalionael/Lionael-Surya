-- =============================================================================
-- [Phase 4] Power BI-facing view version of 020_weekday_hour_pattern.sql's analysis. That file
-- is a curated top-20 "which combo is worst" query (kept as-is, unmodified); this view returns
-- the FULL (day_of_week x hour_of_day) grid -- all 168 combinations, including zero-count
-- cells -- because a Power BI heatmap/matrix visual needs the complete grid to render properly,
-- not a pre-filtered top-N.
--
-- Analytical question (ANALYTICAL_QUESTIONS.md B1): What hour of day and day of week see the
-- most KSI collisions?
--
-- Metric definition: ksi_collision_count = COUNT(DISTINCT collision_id) WHERE acclass IN
-- ('Fatal Injury', 'Non-Fatal Injury'), grouped by day-of-week and hour-of-day.
--
-- Grain: one row per (day_of_week, hour_of_day) combination, 7 x 24 = 168 rows always present.
--
-- Limitation: same as 020_weekday_hour_pattern.sql -- hour is the reported collision
-- timestamp, not independently verified; day_of_week (0=Sunday..6=Saturday) is dim_date's own
-- numbering, included for a stable sort order distinct from the display label day_name.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.v_collision_hour_weekday AS
SELECT
    dow.day_of_week,
    dow.day_name,
    hr.hour_of_day,
    COUNT(DISTINCT f.collision_id) AS ksi_collision_count
FROM (SELECT DISTINCT day_of_week, day_name FROM analytics.dim_date) dow
CROSS JOIN (SELECT generate_series(0, 23) AS hour_of_day) hr
LEFT JOIN analytics.dim_date d ON d.day_of_week = dow.day_of_week
LEFT JOIN analytics.fact_collisions f
    ON f.date_key = d.date_key
   AND EXTRACT(HOUR FROM f.accdate)::int = hr.hour_of_day
   AND f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
GROUP BY dow.day_of_week, dow.day_name, hr.hour_of_day
ORDER BY dow.day_of_week, hr.hour_of_day;
