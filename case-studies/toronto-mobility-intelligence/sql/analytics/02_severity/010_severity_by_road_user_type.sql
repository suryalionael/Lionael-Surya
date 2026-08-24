-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md A2 extended): Among KSI collisions, does the
-- fatal share differ depending on which road-user type was involved?
--
-- Metric definition: fatal_share_pct = 100 * COUNT(DISTINCT collision_id WHERE acclass =
-- 'Fatal Injury') / COUNT(DISTINCT collision_id), computed separately for collisions flagged
-- as involving a pedestrian, a cyclist, a motorcyclist, and collisions with none of those
-- three flags set (i.e. vehicle-occupant-only collisions).
--
-- Grain: one row per road-user category (5 rows: 3 vulnerable-user categories + a
-- vehicle-only baseline + the citywide total for reference).
--
-- Limitation: `pedestrian`/`cyclist`/`motorcyclist` are collision-level flags (confirmed in
-- Phase 2/3 build: identical across every person-row of a given collision_id), so
-- COUNT(DISTINCT collision_id) is the correct grain here -- this counts *collisions involving*
-- that road-user type, not the number of pedestrians/cyclists/motorcyclists themselves (see
-- 03_road_users/ for person-level counts via the `road_user` field). Categories are not
-- mutually exclusive: a single collision can involve both a pedestrian and a cyclist, so rows
-- do not sum to the citywide total.
-- =============================================================================

WITH categories AS (
    SELECT 'pedestrian_involved' AS category,
           COUNT(DISTINCT collision_id) AS ksi_collision_count,
           COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury') AS fatal_collision_count
    FROM analytics.fact_collisions
    WHERE pedestrian AND acclass IN ('Fatal Injury', 'Non-Fatal Injury')

    UNION ALL
    SELECT 'cyclist_involved',
           COUNT(DISTINCT collision_id),
           COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury')
    FROM analytics.fact_collisions
    WHERE cyclist AND acclass IN ('Fatal Injury', 'Non-Fatal Injury')

    UNION ALL
    SELECT 'motorcyclist_involved',
           COUNT(DISTINCT collision_id),
           COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury')
    FROM analytics.fact_collisions
    WHERE motorcyclist AND acclass IN ('Fatal Injury', 'Non-Fatal Injury')

    UNION ALL
    SELECT 'vehicle_occupants_only',
           COUNT(DISTINCT collision_id),
           COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury')
    FROM analytics.fact_collisions
    WHERE NOT pedestrian AND NOT cyclist AND NOT motorcyclist
      AND acclass IN ('Fatal Injury', 'Non-Fatal Injury')

    UNION ALL
    SELECT 'all_ksi_collisions_citywide',
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
