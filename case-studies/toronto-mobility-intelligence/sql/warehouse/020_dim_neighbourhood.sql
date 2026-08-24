TRUNCATE analytics.dim_neighbourhood CASCADE;

INSERT INTO analytics.dim_neighbourhood (area_id, area_short_code, area_name, classification, geom)
SELECT area_id, area_short_code, area_name, classification, geom
FROM clean.neighbourhoods;
