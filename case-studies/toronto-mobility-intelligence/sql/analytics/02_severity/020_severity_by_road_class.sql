-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md C3): How does collision severity vary by road
-- classification (arterial vs. local vs. collector, etc.)?
--
-- Metric definition: ksi_collision_count and fatal_share_pct (as defined in
-- 01_temporal/010_annual_ksi_trend.sql), grouped by road_class. Only classes with at least 20
-- KSI collisions are shown, to avoid a single-digit-count class producing a noisy 0%/50%/100%
-- fatal share.
--
-- Grain: one row per road_class value.
--
-- Limitation: road_class is a City-assigned category on the collision record itself, not
-- independently cross-checked against the Centreline dataset (out of scope for this project).
-- A road class with a high fatal share and a small collision count is a weaker signal than the
-- same fatal share on a road class with hundreds of collisions -- ksi_collision_count is shown
-- alongside fatal_share_pct specifically so it is never read in isolation.
-- =============================================================================

SELECT
    road_class,
    COUNT(DISTINCT collision_id) AS ksi_collision_count,
    COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury') AS fatal_collision_count,
    ROUND(
        100.0 * COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury')
        / NULLIF(COUNT(DISTINCT collision_id), 0),
        2
    ) AS fatal_share_pct
FROM analytics.fact_collisions
WHERE acclass IN ('Fatal Injury', 'Non-Fatal Injury')
  AND road_class IS NOT NULL
GROUP BY road_class
HAVING COUNT(DISTINCT collision_id) >= 20
ORDER BY fatal_share_pct DESC;
