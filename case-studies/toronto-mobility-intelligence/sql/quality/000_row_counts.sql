SELECT 'staging.stg_ksi_collisions' AS table_name, count(*) FROM staging.stg_ksi_collisions
UNION ALL SELECT 'staging.stg_tmc_counts', count(*) FROM staging.stg_tmc_counts
UNION ALL SELECT 'staging.stg_traffic_signals', count(*) FROM staging.stg_traffic_signals
UNION ALL SELECT 'staging.stg_neighbourhoods', count(*) FROM staging.stg_neighbourhoods
UNION ALL SELECT 'clean.collisions', count(*) FROM clean.collisions
UNION ALL SELECT 'clean.traffic_volume', count(*) FROM clean.traffic_volume
UNION ALL SELECT 'clean.intersections', count(*) FROM clean.intersections
UNION ALL SELECT 'clean.neighbourhoods', count(*) FROM clean.neighbourhoods
UNION ALL SELECT 'clean.dq_rejected_rows', count(*) FROM clean.dq_rejected_rows
UNION ALL SELECT 'clean.dq_flags', count(*) FROM clean.dq_flags
UNION ALL SELECT 'analytics.dim_date', count(*) FROM analytics.dim_date
UNION ALL SELECT 'analytics.dim_neighbourhood', count(*) FROM analytics.dim_neighbourhood
UNION ALL SELECT 'analytics.dim_intersection', count(*) FROM analytics.dim_intersection
UNION ALL SELECT 'analytics.fact_collisions', count(*) FROM analytics.fact_collisions
UNION ALL SELECT 'analytics.fact_traffic_volume', count(*) FROM analytics.fact_traffic_volume
UNION ALL SELECT 'analytics.bridge_collision_intersection', count(*) FROM analytics.bridge_collision_intersection
ORDER BY 1;
