-- =============================================================================
-- [Phase 4] Power BI-facing view version of 030_seasonal_pattern.sql (kept as-is, unmodified).
--
-- Analytical question (ANALYTICAL_QUESTIONS.md B2): Is there a seasonal pattern in collision
-- frequency or severity, and does it coincide with winter road surface conditions?
--
-- Metric definition: identical to 030_seasonal_pattern.sql -- ksi_collision_count,
-- fatal_collision_count, fatal_share_pct, winter_condition_share_pct (share of collisions
-- with rdsfcond IN ('Ice','Loose Snow','Packed Snow','Slush')).
--
-- Grain: one row per season (Winter/Spring/Summer/Fall), always 4 rows.
--
-- Limitation: same as 030_seasonal_pattern.sql -- rdsfcond is self-reported at the scene, not
-- an independent weather measurement; this shows association/coincidence only, never causation.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.v_collision_seasonal_pattern AS
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
