-- Staging: near-1:1 mirror of the CKAN datastore dump CSVs. Every source column is TEXT
-- so that a load never fails (or silently drops rows) due to a type-coercion surprise;
-- typing and validation happen explicitly in the staging -> clean step.

DROP TABLE IF EXISTS staging.ingestion_log CASCADE;
CREATE TABLE staging.ingestion_log (
    id                   bigserial PRIMARY KEY,
    dataset_name         text NOT NULL,
    package_id           text NOT NULL,
    resource_id          text NOT NULL,
    resource_name        text NOT NULL,
    source_url           text NOT NULL,
    city_last_refreshed  timestamptz,
    downloaded_at        timestamptz NOT NULL,
    sha256               text NOT NULL,
    row_count_source     integer NOT NULL,
    row_count_loaded     integer NOT NULL,
    loaded_at            timestamptz NOT NULL DEFAULT now()
);

-- Motor Vehicle Collisions Involving Killed or Seriously Injured Persons (KSI)
-- Source columns, in CSV order, per CKAN resource 9c9a9b60-95c1-4541-ad44-15c4a643aff9.
DROP TABLE IF EXISTS staging.stg_ksi_collisions CASCADE;
CREATE TABLE staging.stg_ksi_collisions (
    src_id               text,
    collision_id         text,
    accdate              text,
    stname1              text,
    stname2               text,
    stname3               text,
    per_inv              text,
    acclass              text,
    accloc               text,
    traffictl            text,
    impactype            text,
    visible              text,
    light                text,
    rdsfcond             text,
    road_class           text,
    failtorem            text,
    longitude            text,
    latitude              text,
    veh_no               text,
    vehtype               text,
    initdir               text,
    per_no                text,
    invage                 text,
    injury                 text,
    safequip               text,
    drivact                text,
    drivcond               text,
    pedact                 text,
    pedcond                text,
    manoeuvre              text,
    pedtype                text,
    cyclistype             text,
    cycact                 text,
    cyccond                text,
    road_user              text,
    fatal_no               text,
    wardname               text,
    division               text,
    neighbourhood          text,
    aggressive             text,
    distracted             text,
    cyclist                text,
    motorcyclist            text,
    other_micromobility    text,
    older_adult             text,
    pedestrian              text,
    red_light               text,
    school_child            text,
    heavy_truck             text,
    geometry                text,
    _source_file            text,
    _loaded_at              timestamptz NOT NULL DEFAULT now()
);

-- Traffic Volumes - Multimodal Intersection Turning Movement Counts (full history summary)
-- Source columns per CKAN resource 1364bffa-29a3-4c39-af8a-925d8ca7bf1f.
DROP TABLE IF EXISTS staging.stg_tmc_counts CASCADE;
CREATE TABLE staging.stg_tmc_counts (
    src_id                text,
    count_id              text,
    count_date            text,
    location_name         text,
    longitude             text,
    latitude               text,
    centreline_type        text,
    centreline_id           text,
    px                      text,
    count_duration          text,
    total_vehicle           text,
    total_bike              text,
    total_heavy_pct         text,
    total_pedestrian        text,
    am_peak_start           text,
    am_peak_vehicle         text,
    am_peak_bike            text,
    am_peak_heavy_pct       text,
    pm_peak_start           text,
    pm_peak_vehicle         text,
    pm_peak_bike            text,
    pm_peak_heavy_pct       text,
    n_appr_vehicle          text,
    n_appr_bike             text,
    n_appr_heavy_pct        text,
    e_appr_vehicle          text,
    e_appr_bike             text,
    e_appr_heavy_pct        text,
    s_appr_vehicle          text,
    s_appr_bike             text,
    s_appr_heavy_pct        text,
    w_appr_vehicle          text,
    w_appr_bike             text,
    w_appr_heavy_pct        text,
    _source_file            text,
    _loaded_at              timestamptz NOT NULL DEFAULT now()
);

-- Traffic Signals Tabular ("Traffic Signal" layer)
-- Source columns (originally upper-case) per CKAN resource 139e5357-0caf-4c9a-a6be-ce94d38bcfeb.
DROP TABLE IF EXISTS staging.stg_traffic_signals CASCADE;
CREATE TABLE staging.stg_traffic_signals (
    src_id                              text,
    px                                  text,
    main_street                         text,
    midblock_route                      text,
    side1_street                        text,
    side2_street                        text,
    private_access                      text,
    additional_info                     text,
    activationdate                      text,
    signalsystem                        text,
    non_system                          text,
    control_mode                        text,
    pedwalkspeed                        text,
    aps_operation                       text,
    numberofapproaches                  text,
    objectid                            text,
    geo_id                              text,
    node_id                             text,
    audiblepedsignal                    text,
    transit_preempt                     text,
    fire_preempt                        text,
    rail_preempt                        text,
    mi_prinx                            text,
    bicycle_signal                      text,
    ups                                 text,
    led_blankout_sign                   text,
    lpi_north_implementation_date       text,
    lpi_south_implementation_date       text,
    lpi_east_implementation_date        text,
    lpi_west_implementation_date        text,
    lpi_comment                         text,
    geometry                            text,
    _source_file                        text,
    _loaded_at                          timestamptz NOT NULL DEFAULT now()
);

-- Neighbourhoods
-- Source columns (originally upper-case) per CKAN resource 5e6095fc-1bef-4776-887c-28d37f722c51.
DROP TABLE IF EXISTS staging.stg_neighbourhoods CASCADE;
CREATE TABLE staging.stg_neighbourhoods (
    src_id                text,
    area_id               text,
    area_attr_id          text,
    parent_area_id        text,
    area_short_code       text,
    area_long_code        text,
    area_name             text,
    area_desc             text,
    classification        text,
    classification_code   text,
    objectid              text,
    geometry              text,
    _source_file          text,
    _loaded_at            timestamptz NOT NULL DEFAULT now()
);
