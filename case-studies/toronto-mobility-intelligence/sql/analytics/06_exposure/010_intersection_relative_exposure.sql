-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md E1, per the approved Phase 1 methodology in
-- docs/DATA_MODEL.md S1.5/S4.2): among matched intersections, which have a disproportionately
-- high recent collision count relative to their most recently observed traffic volume?
--
-- ================================ READ THIS FIRST =============================
-- This is a CROSS-SECTIONAL (point-in-time) comparison of intersections to each other, as of
-- now. It is explicitly NOT a historical trend and NOT a true annual collision rate. The
-- reason, established empirically in Phase 1 (docs/DATA_MODEL.md S1): TMC traffic counts are
-- ad hoc (~1 recount every 3.6 years per intersection on average, many intersections recounted
-- only once in 20+ years), so a same-year volume denominator does not exist for most
-- intersection-years. Building a year-by-year rate would require faking a denominator for
-- years that were never actually counted -- the Phase 1 decision was explicitly not to do
-- that. This view instead divides several YEARS of collisions by a single DAY's volume count,
-- which is a legitimate "typical exposure" proxy for ranking intersections against each other
-- right now, but must never be read as "the collision rate in year X."
-- =================================================================================
--
-- Metric definition:
--   numerator   = matched_ksi_collisions_2021_2025: COUNT(DISTINCT collision_id) from
--                 bridge_collision_intersection (match_status = 'matched'), restricted to the
--                 5 most recent complete years (2021-2025)
--   denominator = total_movements: total_vehicle + total_bike + total_pedestrian from this
--                 intersection's single MOST RECENT fact_traffic_volume row (traffic_count_date)
--   collisions_per_10k_movements = 10,000 * numerator / denominator
--   count_recency_years = years between traffic_count_date and today -- exposed on every row,
--                 NOT filtered out, so a stale count is visible rather than hidden
--   recency_reliable = count_recency_years <= 10 -- a usability flag, not a filter; the
--                 analyst decides whether to trust or exclude stale-count rows
--
-- Grain: one row per intersection that has at least one TMC volume observation (of any date)
-- AND a non-zero total movement count. Intersections with zero matched collisions in
-- 2021-2025 are included with collisions_per_10k_movements = 0, not dropped.
--
-- Limitation: see the boxed note above. Additionally: this only covers intersections that
-- both (a) matched at least one TMC count and (b) are in dim_intersection (signalized) --
-- unsignalized high-volume locations are entirely absent from this view, not scored as zero.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.v_intersection_exposure AS
WITH most_recent_volume AS (
    SELECT DISTINCT ON (intersection_key)
        intersection_key,
        count_date AS traffic_count_date,
        (COALESCE(total_vehicle, 0) + COALESCE(total_bike, 0) + COALESCE(total_pedestrian, 0)) AS total_movements
    FROM analytics.fact_traffic_volume
    WHERE intersection_key IS NOT NULL
    ORDER BY intersection_key, count_date DESC
),
matched_recent AS (
    SELECT b.intersection_key, COUNT(DISTINCT b.collision_id) AS matched_ksi_collisions_2021_2025
    FROM analytics.bridge_collision_intersection b
    JOIN analytics.fact_collisions f ON f.collision_id = b.collision_id
    JOIN analytics.dim_date d ON d.date_key = f.date_key
    WHERE b.match_status = 'matched' AND d.year BETWEEN 2021 AND 2025
    GROUP BY b.intersection_key
)
SELECT
    di.px,
    di.main_street,
    di.side1_street,
    COALESCE(m.matched_ksi_collisions_2021_2025, 0) AS matched_ksi_collisions_2021_2025,
    v.traffic_count_date,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, v.traffic_count_date))::int AS count_recency_years,
    v.total_movements,
    ROUND(
        COALESCE(m.matched_ksi_collisions_2021_2025, 0)::numeric / NULLIF(v.total_movements, 0) * 10000,
        3
    ) AS collisions_per_10k_movements,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, v.traffic_count_date)) <= 10 AS recency_reliable
FROM analytics.dim_intersection di
JOIN most_recent_volume v ON v.intersection_key = di.intersection_key
LEFT JOIN matched_recent m ON m.intersection_key = di.intersection_key
WHERE v.total_movements > 0
ORDER BY collisions_per_10k_movements DESC NULLS LAST;
