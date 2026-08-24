-- Unexpected category values: the "expected" sets below were captured from the actual data
-- during Phase 2 build (not guessed) -- a WARN here means the City has introduced a new
-- category value since this project was built, which is exactly the kind of drift this check
-- exists to catch early, not something to silently absorb.

WITH acclass_unexpected AS (
    SELECT DISTINCT acclass FROM analytics.fact_collisions
    WHERE acclass IS NOT NULL
      AND acclass NOT IN ('Fatal Injury', 'Non-Fatal Injury', 'Property Damage Only')
),
road_user_unexpected AS (
    SELECT DISTINCT road_user FROM analytics.fact_collisions
    WHERE road_user IS NOT NULL
      AND road_user NOT IN ('driver', 'passenger', 'pedestrian', 'cyclist', 'motorcyclist',
                             'owner', 'other', 'other_micromobility')
),
match_status_unexpected AS (
    SELECT DISTINCT match_status FROM analytics.bridge_collision_intersection
    WHERE match_status NOT IN ('matched', 'unmatched_no_candidate', 'unmatched_outside_radius')
)
SELECT 'unexpected_category__acclass' AS check_name,
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'WARN' END AS status,
       CASE WHEN count(*) = 0 THEN 'no unexpected acclass values'
            ELSE format('unexpected acclass values: %s', string_agg(acclass, ', ')) END AS detail
FROM acclass_unexpected

UNION ALL
SELECT 'unexpected_category__road_user',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'WARN' END,
       CASE WHEN count(*) = 0 THEN 'no unexpected road_user values'
            ELSE format('unexpected road_user values: %s', string_agg(road_user, ', ')) END
FROM road_user_unexpected

UNION ALL
SELECT 'unexpected_category__match_status',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       CASE WHEN count(*) = 0 THEN 'no unexpected match_status values'
            ELSE format('unexpected match_status values (violates CHECK constraint domain): %s', string_agg(match_status, ', ')) END
FROM match_status_unexpected

ORDER BY 1;
