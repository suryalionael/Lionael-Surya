-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md B2): Is there a seasonal pattern in collision
-- frequency or severity, and does it coincide with winter road surface conditions?
--
-- Metric definition:
--   ksi_collision_count = COUNT(DISTINCT collision_id) per season
--   fatal_share_pct     = 100 * fatal collisions / ksi_collision_count
--   winter_condition_share_pct = 100 * (collisions with rdsfcond IN
--       ('Ice','Loose Snow','Packed Snow','Slush')) / ksi_collision_count
--       -- these are the winter-specific road-surface categories present in the source data
--       (confirmed by direct inspection; 'Wet' is excluded as it is a year-round rain
--       condition, not winter-specific)
--
-- Grain: one row per season (Winter/Spring/Summer/Fall), across all years 2006-2026.
--
-- Limitation: rdsfcond is self-reported by the investigating officer at the scene, not an
-- independent weather-station measurement. This can show that winter collisions coincide with
-- winter road conditions far more often than other seasons' collisions do -- it cannot, by
-- itself, establish that the condition caused the collision. "Season" here is meteorological
-- (Dec 21-Mar 19 = Winter, etc.), matching dim_date's own season definition.
-- =============================================================================

SELECT
    d.season,
    COUNT(DISTINCT f.collision_id) AS ksi_collision_count,
    COUNT(DISTINCT f.collision_id) FILTER (WHERE f.acclass = 'Fatal Injury') AS fatal_collision_count,
    ROUND(
        100.0 * COUNT(DISTINCT f.collision_id) FILTER (WHERE f.acclass = 'Fatal Injury')
        / NULLIF(COUNT(DISTINCT f.collision_id), 0),
        2
    ) AS fatal_share_pct,
    ROUND(
        100.0 * COUNT(DISTINCT f.collision_id) FILTER (
            WHERE f.rdsfcond IN ('Ice', 'Loose Snow', 'Packed Snow', 'Slush')
        ) / NULLIF(COUNT(DISTINCT f.collision_id), 0),
        2
    ) AS winter_condition_share_pct
FROM analytics.fact_collisions f
JOIN analytics.dim_date d ON d.date_key = f.date_key
WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
GROUP BY d.season
ORDER BY ksi_collision_count DESC;
