-- clean.collisions -> analytics.fact_collisions
-- neighbourhood_key is resolved by matching KSI's free-text neighbourhood field against the
-- Neighbourhoods dimension's area_name, case/whitespace-insensitively -- this was flagged in
-- docs/DATA_MODEL.md S3.5 as needing validation, not assumed to be a clean match. The match
-- rate is checked explicitly in sql/quality/ rather than assumed here.

TRUNCATE analytics.fact_collisions;

INSERT INTO analytics.fact_collisions
    (collision_id, veh_no, per_no, accdate, date_key, stname1, stname2, stname3, acclass,
     accloc, traffictl, impactype, visible, light, rdsfcond, road_class, vehtype, invage,
     injury, drivact, drivcond, pedact, pedcond, manoeuvre, cyclistype, road_user, fatal_no,
     aggressive, distracted, cyclist, motorcyclist, other_micromobility, older_adult,
     pedestrian, red_light, school_child, heavy_truck, wardname, division,
     neighbourhood_key, latitude, longitude, geom)
SELECT
    c.collision_id, c.veh_no, c.per_no, c.accdate, c.accdate::date, c.stname1, c.stname2,
    c.stname3, c.acclass, c.accloc, c.traffictl, c.impactype, c.visible, c.light,
    c.rdsfcond, c.road_class, c.vehtype, c.invage, c.injury, c.drivact, c.drivcond,
    c.pedact, c.pedcond, c.manoeuvre, c.cyclistype, c.road_user, c.fatal_no, c.aggressive,
    c.distracted, c.cyclist, c.motorcyclist, c.other_micromobility, c.older_adult,
    c.pedestrian, c.red_light, c.school_child, c.heavy_truck, c.wardname, c.division,
    n.neighbourhood_key, c.latitude, c.longitude, c.geom
FROM clean.collisions c
LEFT JOIN analytics.dim_neighbourhood n
    ON lower(TRIM(n.area_name)) = lower(TRIM(c.neighbourhood_name));
