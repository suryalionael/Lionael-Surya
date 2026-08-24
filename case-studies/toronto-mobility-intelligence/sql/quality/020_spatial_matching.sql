-- Spatial matching checks. The 44.71% match rate found here at load time is compared against
-- the ~44.7% predicted empirically in docs/DATA_MODEL.md S2.4 -- a WARN (not FAIL) outside
-- tolerance means the underlying data shape changed enough to revisit that analysis, not that
-- the pipeline is broken.

WITH match_counts AS (
    SELECT
        count(*) AS total,
        count(*) FILTER (WHERE match_status = 'matched') AS matched,
        count(*) FILTER (WHERE match_status = 'unmatched_outside_radius') AS unmatched_outside,
        count(*) FILTER (WHERE match_status = 'unmatched_no_candidate') AS unmatched_none
    FROM analytics.bridge_collision_intersection
)
SELECT 'spatial_match_rate' AS check_name,
       CASE WHEN matched_pct BETWEEN 35 AND 55 THEN 'PASS'
            WHEN matched_pct BETWEEN 25 AND 65 THEN 'WARN'
            ELSE 'FAIL' END AS status,
       format('%s%% matched (%s of %s) at the approved 20m radius -- docs/DATA_MODEL.md S2.4 predicted ~44.7%%',
              matched_pct, matched, total) AS detail
FROM (SELECT total, matched, round(100.0 * matched / NULLIF(total, 0), 2) AS matched_pct FROM match_counts) x

UNION ALL
SELECT 'spatial_unmatched_no_candidate_share',
       CASE WHEN unmatched_none = 0 THEN 'PASS'
            WHEN round(100.0 * unmatched_none / NULLIF(total, 0), 2) <= 1 THEN 'WARN'
            ELSE 'FAIL' END,
       format('%s of %s collisions (%s%%) have no usable geometry to match against at all',
              unmatched_none, total, round(100.0 * unmatched_none / NULLIF(total, 0), 2))
FROM match_counts

UNION ALL
SELECT 'spatial_match_radius_respected',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s matched rows exceed the 20.00m approved radius', count(*))
FROM analytics.bridge_collision_intersection
WHERE match_status = 'matched' AND match_distance_m > 20.0

UNION ALL
SELECT 'spatial_status_consistency',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s rows violate the matched<->intersection_key/distance consistency rule', count(*))
FROM analytics.bridge_collision_intersection
WHERE (match_status = 'matched' AND (intersection_key IS NULL OR match_distance_m IS NULL))
   OR (match_status <> 'matched' AND intersection_key IS NOT NULL)

UNION ALL
SELECT 'spatial_unmatched_collisions_preserved',
       CASE WHEN count(*) = (SELECT count(DISTINCT collision_id) FROM clean.collisions) THEN 'PASS' ELSE 'FAIL' END,
       format('bridge table has %s rows; clean.collisions has %s distinct collision_id values -- every collision must appear in the bridge exactly once, matched or not',
              count(*), (SELECT count(DISTINCT collision_id) FROM clean.collisions))
FROM analytics.bridge_collision_intersection

ORDER BY 1;
