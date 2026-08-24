-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md A3, Vision Zero framing): Are pedestrians and
-- cyclists (the "vulnerable road users" Vision Zero prioritizes) becoming a larger or smaller
-- share of KSI collisions over time?
--
-- Metric definition:
--   vru_collision_count = COUNT(DISTINCT collision_id) WHERE pedestrian OR cyclist
--   vru_share_pct       = 100 * vru_collision_count / ksi_collision_count
--   yoy_share_change_pp = this year's vru_share_pct minus last year's (percentage-point
--                          change, via LAG() -- not a percent-of-a-percent change, which
--                          would be harder to read)
--
-- Grain: one row per year.
--
-- Limitation: same collision-level-flag caveat as 010_road_user_involvement_trend.sql --
-- this counts collision EVENTS involving a VRU, not the number of VRU people affected.
-- Small early-2000s-style annual counts make single-year percentage-point swings noisy;
-- read the multi-year direction, not any single year-over-year jump, as the signal.
-- =============================================================================

WITH yearly AS (
    SELECT
        d.year,
        COUNT(DISTINCT f.collision_id) FILTER (WHERE f.pedestrian OR f.cyclist) AS vru_collision_count,
        COUNT(DISTINCT f.collision_id) AS ksi_collision_count
    FROM analytics.fact_collisions f
    JOIN analytics.dim_date d ON d.date_key = f.date_key
    WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
    GROUP BY d.year
)
SELECT
    year,
    vru_collision_count,
    ksi_collision_count,
    ROUND(100.0 * vru_collision_count / NULLIF(ksi_collision_count, 0), 2) AS vru_share_pct,
    ROUND(
        (100.0 * vru_collision_count / NULLIF(ksi_collision_count, 0))
        - LAG(100.0 * vru_collision_count / NULLIF(ksi_collision_count, 0)) OVER (ORDER BY year),
        2
    ) AS yoy_share_change_pp
FROM yearly
ORDER BY year;
