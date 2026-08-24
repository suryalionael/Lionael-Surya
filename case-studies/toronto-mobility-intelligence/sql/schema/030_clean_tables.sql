-- Clean: typed columns, standardized categories, PostGIS geometry built, deduplicated.
-- Grain matches the source (person-per-collision for collisions, px x count_date for
-- volumes) -- grain changes happen only in the analytics layer, never here.
--
-- Rows that fail a hard requirement needed to make the row usable at all (missing natural
-- key, unparseable required date) are excluded from the clean table and logged in
-- clean.dq_rejected_rows, with the reason and the full raw source row preserved for audit.
-- Rows with a soft quality issue (e.g. a coordinate outside Toronto) are KEPT with the
-- offending field nulled, and logged in clean.dq_flags -- never silently dropped.

DROP TABLE IF EXISTS clean.dq_rejected_rows CASCADE;
CREATE TABLE clean.dq_rejected_rows (
    id                  bigserial PRIMARY KEY,
    source_table        text NOT NULL,
    source_staging_id   text,
    natural_key         text,
    reject_reason       text NOT NULL,
    raw_row             jsonb NOT NULL,
    rejected_at         timestamptz NOT NULL DEFAULT now()
);

DROP TABLE IF EXISTS clean.dq_flags CASCADE;
CREATE TABLE clean.dq_flags (
    id            bigserial PRIMARY KEY,
    target_table  text NOT NULL,
    target_id     bigint NOT NULL,
    flag_type     text NOT NULL,
    detail        text,
    flagged_at    timestamptz NOT NULL DEFAULT now()
);

DROP TABLE IF EXISTS clean.collisions CASCADE;
CREATE TABLE clean.collisions (
    id                    bigserial PRIMARY KEY,
    collision_id          text NOT NULL,
    veh_no                integer,
    per_no                integer,
    accdate               timestamp NOT NULL,
    stname1               text,
    stname2               text,
    stname3               text,
    acclass               text,
    accloc                text,
    traffictl             text,
    impactype             text,
    visible               text,
    light                 text,
    rdsfcond              text,
    road_class            text,
    vehtype               text,
    invage                integer,
    injury                text,
    drivact               text,
    drivcond              text,
    pedact                text,
    pedcond                text,
    manoeuvre               text,
    cyclistype              text,
    road_user               text,
    fatal_no                 integer,
    aggressive               boolean,
    distracted               boolean,
    cyclist                  boolean,
    motorcyclist              boolean,
    other_micromobility       boolean,
    older_adult                boolean,
    pedestrian                  boolean,
    red_light                    boolean,
    school_child                  boolean,
    heavy_truck                    boolean,
    wardname                        text,
    division                        text,
    neighbourhood_name              text,
    latitude                        double precision,
    longitude                       double precision,
    geom                            geometry(Point, 4326),
    _staging_id                     text
);

DROP TABLE IF EXISTS clean.traffic_volume CASCADE;
CREATE TABLE clean.traffic_volume (
    id                  bigserial PRIMARY KEY,
    px                  integer,
    count_date          date NOT NULL,
    location_name       text,
    centreline_type     text,
    centreline_id       bigint,
    count_duration      text,
    total_vehicle       integer,
    total_bike          integer,
    total_pedestrian    integer,
    total_heavy_pct     numeric(6,4),
    am_peak_start       timestamp,
    am_peak_vehicle     integer,
    am_peak_bike        integer,
    am_peak_heavy_pct   numeric(6,4),
    pm_peak_start       timestamp,
    pm_peak_vehicle     integer,
    pm_peak_bike        integer,
    pm_peak_heavy_pct   numeric(6,4),
    n_appr_vehicle      integer,
    n_appr_bike         integer,
    n_appr_heavy_pct    numeric(6,4),
    e_appr_vehicle      integer,
    e_appr_bike         integer,
    e_appr_heavy_pct    numeric(6,4),
    s_appr_vehicle      integer,
    s_appr_bike         integer,
    s_appr_heavy_pct    numeric(6,4),
    w_appr_vehicle      integer,
    w_appr_bike         integer,
    w_appr_heavy_pct    numeric(6,4),
    latitude            double precision,
    longitude           double precision,
    geom                geometry(Point, 4326),
    _staging_id         text
);

DROP TABLE IF EXISTS clean.intersections CASCADE;
CREATE TABLE clean.intersections (
    id                   bigserial PRIMARY KEY,
    px                   integer NOT NULL,
    main_street          text,
    side1_street         text,
    side2_street         text,
    midblock_route       text,
    signal_system        text,
    control_mode         text,
    audible_ped_signal   boolean,
    transit_preempt      boolean,
    fire_preempt         boolean,
    rail_preempt         boolean,
    led_blankout_sign    boolean,
    activation_date      date,
    latitude             double precision,
    longitude            double precision,
    geom                 geometry(Point, 4326) NOT NULL,
    _staging_id          text,
    UNIQUE (px)
);

DROP TABLE IF EXISTS clean.neighbourhoods CASCADE;
CREATE TABLE clean.neighbourhoods (
    id               bigserial PRIMARY KEY,
    area_id          integer NOT NULL,
    area_short_code  text,
    area_name        text NOT NULL,
    classification   text,
    geom             geometry(MultiPolygon, 4326) NOT NULL,
    _staging_id      text,
    UNIQUE (area_id)
);

-- Minimal indexing to support the clean -> analytics transform joins (dedup checks,
-- neighbourhood-name resolution, px joins). The heavier GiST indexes used by the spatial
-- match live on the analytics tables (sql/schema/040_analytics_tables.sql), since that is
-- where the match query actually runs.
CREATE INDEX idx_clean_collisions_collision_id ON clean.collisions (collision_id);
CREATE INDEX idx_clean_collisions_neighbourhood_name ON clean.collisions (neighbourhood_name);
CREATE INDEX idx_clean_traffic_volume_px_date ON clean.traffic_volume (px, count_date);
