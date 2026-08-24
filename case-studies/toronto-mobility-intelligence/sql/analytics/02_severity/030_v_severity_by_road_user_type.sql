-- =============================================================================
-- [Phase 5 addition] View version of 010_severity_by_road_user_type.sql (kept as-is,
-- unmodified). Identical query, wrapped in CREATE VIEW.
--
-- Why this exists: docs/POWER_BI_SPEC.md S4.5 originally proposed reproducing this
-- citywide severity-by-road-user-type breakdown from analytics.v_road_user_involvement via a
-- Power BI DAX measure (SUM of that view's per-type columns), specifically to avoid adding an
-- 11th imported table for numbers "already reachable from an imported view." Building the
-- actual DAX measures in Phase 5 found this doesn't work: v_road_user_involvement has no
-- vehicle-occupants-only column, and that category cannot be derived from the other columns
-- either, because pedestrian/cyclist/motorcyclist collisions overlap (a collision can involve
-- more than one type), so "total - ped - cyclist - motorcyclist" would double-subtract. This
-- is a real gap, not a style preference -- see docs/DECISION_LOG.md's Phase 5 entry for the
-- full account of the deviation from the Phase 4 spec.
--
-- Analytical question, metric definition, grain, and limitation: identical to
-- 010_severity_by_road_user_type.sql -- see that file. This view changes nothing about the
-- analysis, only makes the same numbers queryable as a stable object Power BI can import.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.v_severity_by_road_user_type AS
WITH categories AS (
    SELECT 'Pedestrian' AS category,
           COUNT(DISTINCT collision_id) AS ksi_collision_count,
           COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury') AS fatal_collision_count
    FROM analytics.fact_collisions
    WHERE pedestrian AND acclass IN ('Fatal Injury', 'Non-Fatal Injury')

    UNION ALL
    SELECT 'Cyclist',
           COUNT(DISTINCT collision_id),
           COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury')
    FROM analytics.fact_collisions
    WHERE cyclist AND acclass IN ('Fatal Injury', 'Non-Fatal Injury')

    UNION ALL
    SELECT 'Motorcyclist',
           COUNT(DISTINCT collision_id),
           COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury')
    FROM analytics.fact_collisions
    WHERE motorcyclist AND acclass IN ('Fatal Injury', 'Non-Fatal Injury')

    UNION ALL
    SELECT 'Vehicle occupants only',
           COUNT(DISTINCT collision_id),
           COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury')
    FROM analytics.fact_collisions
    WHERE NOT pedestrian AND NOT cyclist AND NOT motorcyclist
      AND acclass IN ('Fatal Injury', 'Non-Fatal Injury')

    UNION ALL
    SELECT 'All KSI collisions (citywide)',
           COUNT(DISTINCT collision_id),
           COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury')
    FROM analytics.fact_collisions
    WHERE acclass IN ('Fatal Injury', 'Non-Fatal Injury')
)
SELECT
    category,
    ksi_collision_count,
    fatal_collision_count,
    ROUND(100.0 * fatal_collision_count / NULLIF(ksi_collision_count, 0), 2) AS fatal_share_pct
FROM categories
ORDER BY fatal_share_pct DESC;
