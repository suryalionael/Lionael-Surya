-- Analytics: the star schema described in docs/DATA_MODEL.md. Populated exclusively from
-- the `clean` schema by sql/analytics/*.sql -- never loaded directly from staging.

DROP TABLE IF EXISTS analytics.dim_date CASCADE;
CREATE TABLE analytics.dim_date (
    date_key       date PRIMARY KEY,
    year           smallint NOT NULL,
    month          smallint NOT NULL,
    month_name     text NOT NULL,
    quarter        smallint NOT NULL,
    week           smallint NOT NULL,
    day_of_month   smallint NOT NULL,
    day_of_week    smallint NOT NULL,
    day_name       text NOT NULL,
    is_weekend     boolean NOT NULL,
    season         text NOT NULL
);

DROP TABLE IF EXISTS analytics.dim_neighbourhood CASCADE;
CREATE TABLE analytics.dim_neighbourhood (
    neighbourhood_key   serial PRIMARY KEY,
    area_id             integer NOT NULL UNIQUE,
    area_short_code     text,
    area_name           text NOT NULL,
    classification      text,
    geom                geometry(MultiPolygon, 4326) NOT NULL
);

DROP TABLE IF EXISTS analytics.dim_intersection CASCADE;
CREATE TABLE analytics.dim_intersection (
    intersection_key     serial PRIMARY KEY,
    px                   integer NOT NULL UNIQUE,
    main_street          text,
    side1_street         text,
    side2_street         text,
    signal_system        text,
    control_mode         text,
    audible_ped_signal   boolean,
    led_blankout_sign    boolean,
    transit_preempt      boolean,
    fire_preempt         boolean,
    rail_preempt         boolean,
    activation_date      date,
    geom                 geometry(Point, 4326) NOT NULL
);

-- Grain: one row per person involved in a collision, matching the KSI source exactly.
-- (collision_id, veh_no, per_no) is the natural key; collision-level rollups are done with
-- COUNT(DISTINCT collision_id) at query time (see docs/ANALYTICAL_QUESTIONS.md), not by a
-- separate physical table, to avoid maintaining two sources of truth for the same facts.
DROP TABLE IF EXISTS analytics.fact_collisions CASCADE;
CREATE TABLE analytics.fact_collisions (
    collision_person_key   bigserial PRIMARY KEY,
    collision_id           text NOT NULL,
    veh_no                 integer,
    per_no                 integer,
    accdate                timestamp NOT NULL,
    date_key               date NOT NULL REFERENCES analytics.dim_date(date_key),
    stname1                text,
    stname2                text,
    stname3                text,
    acclass                text,
    accloc                 text,
    traffictl              text,
    impactype              text,
    visible                text,
    light                  text,
    rdsfcond               text,
    road_class             text,
    vehtype                text,
    invage                 integer,
    injury                 text,
    drivact                text,
    drivcond               text,
    pedact                 text,
    pedcond                text,
    manoeuvre               text,
    cyclistype               text,
    road_user                 text,
    fatal_no                   integer,
    aggressive                  boolean,
    distracted                   boolean,
    cyclist                       boolean,
    motorcyclist                   boolean,
    other_micromobility             boolean,
    older_adult                      boolean,
    pedestrian                        boolean,
    red_light                          boolean,
    school_child                        boolean,
    heavy_truck                          boolean,
    wardname                              text,
    division                              text,
    neighbourhood_key                     integer REFERENCES analytics.dim_neighbourhood(neighbourhood_key),
    latitude                              double precision,
    longitude                             double precision,
    geom                                  geometry(Point, 4326)
);

-- Grain: one row per (px, count_date) count event, restricted to rows where the source TMC
-- record carries a px (signal/intersection identity). The ~22% of TMC rows with px IS NULL
-- (midblock/segment counts with no intersection identity) are intentionally excluded here --
-- see docs/DATA_MODEL.md S3.4 and docs/DECISION_LOG.md. They remain visible in
-- clean.traffic_volume for anyone who wants to inspect them; they are simply out of scope
-- for the approved intersection-based fact table.
DROP TABLE IF EXISTS analytics.fact_traffic_volume CASCADE;
CREATE TABLE analytics.fact_traffic_volume (
    traffic_volume_key   bigserial PRIMARY KEY,
    px                   integer NOT NULL,
    count_date           date NOT NULL,
    intersection_key     integer REFERENCES analytics.dim_intersection(intersection_key),
    location_name        text,
    count_duration       text,
    total_vehicle        integer,
    total_bike            integer,
    total_pedestrian      integer,
    total_heavy_pct        numeric(6,4),
    am_peak_start           timestamp,
    am_peak_vehicle          integer,
    am_peak_bike               integer,
    am_peak_heavy_pct           numeric(6,4),
    pm_peak_start                 timestamp,
    pm_peak_vehicle                integer,
    pm_peak_bike                     integer,
    pm_peak_heavy_pct                  numeric(6,4),
    n_appr_vehicle                      integer,
    n_appr_bike                          integer,
    n_appr_heavy_pct                      numeric(6,4),
    e_appr_vehicle                         integer,
    e_appr_bike                            integer,
    e_appr_heavy_pct                        numeric(6,4),
    s_appr_vehicle                          integer,
    s_appr_bike                            integer,
    s_appr_heavy_pct                       numeric(6,4),
    w_appr_vehicle                        integer,
    w_appr_bike                          integer,
    w_appr_heavy_pct                    numeric(6,4),
    geom                                geometry(Point, 4326),
    UNIQUE (px, count_date)
);

-- Spatial match result, kept separate from fact_collisions because the match is
-- collision-grain (one location per event) while fact_collisions is person-grain.
-- One row per distinct collision_id -- see docs/DATA_MODEL.md S3.7 and S2 for the empirical
-- justification of the 20m radius.
DROP TABLE IF EXISTS analytics.bridge_collision_intersection CASCADE;
CREATE TABLE analytics.bridge_collision_intersection (
    collision_id          text PRIMARY KEY,
    collision_lat         double precision,
    collision_lon         double precision,
    intersection_key      integer REFERENCES analytics.dim_intersection(intersection_key),
    matched_px             integer,
    match_distance_m        numeric(8,2),
    match_status              text NOT NULL,
    match_radius_m_used        numeric(6,2) NOT NULL,
    matched_at                   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT bridge_match_status_chk
        CHECK (match_status IN ('matched', 'unmatched_no_candidate', 'unmatched_outside_radius')),
    CONSTRAINT bridge_matched_needs_intersection_chk
        CHECK (
            (match_status = 'matched' AND intersection_key IS NOT NULL AND match_distance_m IS NOT NULL)
            OR (match_status <> 'matched' AND intersection_key IS NULL)
        )
);

-- Indexing rationale (deliberately not over-indexed -- these tables are read in bulk for
-- analysis, not looked up row-by-row under write load, so only the joins/filters the
-- approved analytical questions actually use get an index):
--   * fact_collisions.collision_id      -- rollup to collision grain (COUNT DISTINCT), and
--                                           the join target from the bridge table.
--   * fact_collisions.date_key          -- every temporal question (dim_date join/filter).
--   * fact_collisions.neighbourhood_key -- neighbourhood rollups (section F).
--   * fact_collisions.geom              -- GiST, for map/bounding-box queries (C2, G4).
--   * fact_traffic_volume.count_date    -- recency filtering (E1's MAX(count_date) pattern).
--   * fact_traffic_volume.intersection_key -- join to dim_intersection.
--   * fact_traffic_volume.geom          -- GiST, for map queries.
--   * bridge_collision_intersection.match_status     -- the matched/unmatched split is
--                                                        filtered in nearly every D/E question.
--   * bridge_collision_intersection.intersection_key -- join to dim_intersection.
--   * dim_intersection.geom, dim_neighbourhood.geom   -- GiST, needed by the nearest-neighbor
--                                                        spatial match itself (sql/analytics).
-- (px and area_id already carry a unique index via their UNIQUE constraints above.)

CREATE INDEX idx_fact_collisions_collision_id ON analytics.fact_collisions (collision_id);
CREATE INDEX idx_fact_collisions_date_key ON analytics.fact_collisions (date_key);
CREATE INDEX idx_fact_collisions_neighbourhood_key ON analytics.fact_collisions (neighbourhood_key);
CREATE INDEX idx_fact_collisions_geom ON analytics.fact_collisions USING GIST (geom);

CREATE INDEX idx_fact_traffic_volume_count_date ON analytics.fact_traffic_volume (count_date);
CREATE INDEX idx_fact_traffic_volume_intersection_key ON analytics.fact_traffic_volume (intersection_key);
CREATE INDEX idx_fact_traffic_volume_geom ON analytics.fact_traffic_volume USING GIST (geom);

CREATE INDEX idx_bridge_match_status ON analytics.bridge_collision_intersection (match_status);
CREATE INDEX idx_bridge_intersection_key ON analytics.bridge_collision_intersection (intersection_key);

CREATE INDEX idx_dim_intersection_geom ON analytics.dim_intersection USING GIST (geom);
CREATE INDEX idx_dim_neighbourhood_geom ON analytics.dim_neighbourhood USING GIST (geom);
