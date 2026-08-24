-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md B1): What hour of day and day of week see the
-- most KSI collisions -- where should enforcement/safety-campaign resources be timed?
--
-- Metric definition: ksi_collision_count = COUNT(DISTINCT collision_id) WHERE acclass IN
-- ('Fatal Injury', 'Non-Fatal Injury'), grouped by day-of-week and hour-of-day extracted from
-- accdate.
--
-- Grain: one row per (day_of_week, hour_of_day) combination, 7 x 24 = 168 possible rows.
--
-- Limitation: hour is taken from the reported collision timestamp as recorded by police, not
-- independently verified. day_of_week here is dim_date's own numbering (0=Sunday..6=Saturday)
-- for a stable sort order, separate from the display label day_name.
-- =============================================================================

SELECT
    d.day_of_week,
    d.day_name,
    EXTRACT(HOUR FROM f.accdate)::int AS hour_of_day,
    COUNT(DISTINCT f.collision_id) AS ksi_collision_count,
    RANK() OVER (ORDER BY COUNT(DISTINCT f.collision_id) DESC) AS rank_citywide
FROM analytics.fact_collisions f
JOIN analytics.dim_date d ON d.date_key = f.date_key
WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
GROUP BY d.day_of_week, d.day_name, EXTRACT(HOUR FROM f.accdate)
ORDER BY ksi_collision_count DESC
LIMIT 20;
