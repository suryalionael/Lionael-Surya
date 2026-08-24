# Entity-Relationship Diagram

Toronto Mobility Intelligence — `analytics` schema. See [`DATA_MODEL.md`](DATA_MODEL.md) for
full column-level detail and the empirical reasoning behind this shape.

```mermaid
erDiagram
    DIM_DATE ||--o{ FACT_COLLISIONS : "date_key"
    DIM_NEIGHBOURHOOD ||--o{ FACT_COLLISIONS : "neighbourhood_key (nullable)"
    FACT_COLLISIONS ||--|| BRIDGE_COLLISION_INTERSECTION : "collision_id (1 collision : many person-rows, 1 bridge row)"
    DIM_INTERSECTION ||--o{ BRIDGE_COLLISION_INTERSECTION : "intersection_key (nullable, ~45% matched)"
    DIM_INTERSECTION ||--o{ FACT_TRAFFIC_VOLUME : "intersection_key (nullable, ~92% matched)"

    DIM_DATE {
        date date_key PK
        smallint year
        smallint month
        text month_name
        smallint quarter
        smallint day_of_week
        text day_name
        boolean is_weekend
        text season
    }

    DIM_NEIGHBOURHOOD {
        serial neighbourhood_key PK
        integer area_id UK
        text area_name
        geometry geom "MultiPolygon,4326"
    }

    DIM_INTERSECTION {
        serial intersection_key PK
        integer px UK
        text main_street
        text side1_street
        text side2_street
        text signal_system
        boolean audible_ped_signal
        boolean transit_preempt
        date activation_date
        geometry geom "Point,4326"
    }

    FACT_COLLISIONS {
        serial collision_person_key PK
        text collision_id "natural key, repeats per person"
        integer veh_no
        integer per_no
        timestamp accdate
        date date_key FK
        text acclass "severity"
        text road_user
        boolean pedestrian
        boolean cyclist
        boolean motorcyclist
        integer neighbourhood_key FK "nullable"
        double latitude
        double longitude
        geometry geom "Point,4326, nullable"
    }

    BRIDGE_COLLISION_INTERSECTION {
        text collision_id PK
        integer intersection_key FK "nullable"
        integer matched_px
        numeric match_distance_m "nullable"
        text match_status "matched / unmatched_outside_radius / unmatched_no_candidate"
        numeric match_radius_m_used "20.00 for Phase 1"
        timestamp matched_at
    }

    FACT_TRAFFIC_VOLUME {
        serial traffic_volume_key PK
        integer px "natural key part"
        date count_date "natural key part"
        integer intersection_key FK "nullable"
        integer total_vehicle
        integer total_bike
        integer total_pedestrian
        geometry geom "Point,4326"
    }
```

## Plain-text fallback

```
 dim_date                dim_neighbourhood
    |  1                        |  1
    |                           |  (nullable)
    * many                      * many
 fact_collisions  ------------------------------+
 (person grain, PK collision_person_key)        |
    | collision_id (many person-rows : 1 event)  |
    * 1                                          |
 bridge_collision_intersection                   |
 (PK collision_id, nullable intersection_key)    |
    | intersection_key (nullable, ~45% matched)   |
    * many                                        |
 dim_intersection  <---------------- many ---- fact_traffic_volume
 (PK intersection_key, UK px)         intersection_key (nullable, ~92% matched)
                                       PK traffic_volume_key, UK (px, count_date)
```

## Reading the "nullable" relationships

Two joins in this model are intentionally nullable, and both nullability rates are empirically
derived, not assumed:

- **`bridge_collision_intersection.intersection_key`** — null for ~55.3% of collisions. This is
  expected: most KSI collisions happen at unsignalized intersections, stop-sign intersections,
  or midblock, none of which exist in the Traffic Signals dataset. See `DATA_MODEL.md` §2.
- **`fact_traffic_volume.intersection_key`** — null for ~7.8% of TMC intersection-keyed rows,
  where the TMC `px` value doesn't resolve to a signal in the Traffic Signals dataset (likely
  beacons, pedestrian crossovers, or unsignalized intersections that still get a TMC count).
  See `DATA_MODEL.md` §2.5.

Both are modeled as `LEFT JOIN`-safe nullable foreign keys rather than forced/lossy matches.
