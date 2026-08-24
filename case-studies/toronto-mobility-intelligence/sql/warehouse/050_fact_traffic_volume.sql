-- clean.traffic_volume -> analytics.fact_traffic_volume
-- Scope, per the approved docs/DATA_MODEL.md S3.4: only rows with a px (intersection
-- identity) are loaded. The ~22% of clean.traffic_volume rows with px IS NULL (midblock /
-- segment counts) are intentionally excluded here -- they remain visible in clean.traffic_volume
-- for anyone who wants to inspect them, and the exclusion is logged below.
--
-- The (px, count_date) grain has 9 known duplicate pairs in the source (found during Phase 1
-- research) -- the analytics table enforces UNIQUE(px, count_date), so one row per pair is
-- kept deterministically (lowest clean.traffic_volume.id) and the rest are logged, not
-- silently dropped.

TRUNCATE analytics.fact_traffic_volume;

WITH ranked AS (
    SELECT tv.*, ROW_NUMBER() OVER (PARTITION BY tv.px, tv.count_date ORDER BY tv.id) AS rn
    FROM clean.traffic_volume tv
    WHERE tv.px IS NOT NULL
)
INSERT INTO analytics.fact_traffic_volume
    (px, count_date, intersection_key, location_name, count_duration,
     total_vehicle, total_bike, total_pedestrian, total_heavy_pct,
     am_peak_start, am_peak_vehicle, am_peak_bike, am_peak_heavy_pct,
     pm_peak_start, pm_peak_vehicle, pm_peak_bike, pm_peak_heavy_pct,
     n_appr_vehicle, n_appr_bike, n_appr_heavy_pct,
     e_appr_vehicle, e_appr_bike, e_appr_heavy_pct,
     s_appr_vehicle, s_appr_bike, s_appr_heavy_pct,
     w_appr_vehicle, w_appr_bike, w_appr_heavy_pct, geom)
SELECT
    r.px, r.count_date, di.intersection_key, r.location_name, r.count_duration,
    r.total_vehicle, r.total_bike, r.total_pedestrian, r.total_heavy_pct,
    r.am_peak_start, r.am_peak_vehicle, r.am_peak_bike, r.am_peak_heavy_pct,
    r.pm_peak_start, r.pm_peak_vehicle, r.pm_peak_bike, r.pm_peak_heavy_pct,
    r.n_appr_vehicle, r.n_appr_bike, r.n_appr_heavy_pct,
    r.e_appr_vehicle, r.e_appr_bike, r.e_appr_heavy_pct,
    r.s_appr_vehicle, r.s_appr_bike, r.s_appr_heavy_pct,
    r.w_appr_vehicle, r.w_appr_bike, r.w_appr_heavy_pct, r.geom
FROM ranked r
LEFT JOIN analytics.dim_intersection di ON di.px = r.px
WHERE r.rn = 1;

INSERT INTO clean.dq_flags (target_table, target_id, flag_type, detail)
SELECT 'clean.traffic_volume', r.id, 'duplicate_px_count_date_excluded_from_fact',
       'px=' || r.px || ' count_date=' || r.count_date || ' (kept clean.traffic_volume.id with rn=1 instead)'
FROM (
    SELECT id, px, count_date, ROW_NUMBER() OVER (PARTITION BY px, count_date ORDER BY id) AS rn
    FROM clean.traffic_volume WHERE px IS NOT NULL
) r
WHERE r.rn > 1;

INSERT INTO clean.dq_flags (target_table, target_id, flag_type, detail)
SELECT 'clean.traffic_volume', id, 'midblock_px_null_excluded_from_fact_by_design',
       'out of scope for fact_traffic_volume per docs/DATA_MODEL.md S3.4 (no intersection identity)'
FROM clean.traffic_volume WHERE px IS NULL;
