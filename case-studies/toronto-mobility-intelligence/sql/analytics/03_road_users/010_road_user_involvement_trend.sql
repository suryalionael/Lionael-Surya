-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md A3): How has road-user involvement in KSI
-- collisions changed over time -- and, explicitly, how many *collisions* involved a
-- pedestrian/cyclist/motorcyclist versus how many *people* of each type were actually
-- involved?
--
-- Metric definition -- two genuinely different things, deliberately both shown per year:
--   {x}_collision_count = COUNT(DISTINCT collision_id) WHERE <x> flag is true
--       -- "how many KSI collision EVENTS involved at least one <x>"
--   {x}_person_count    = COUNT(*) WHERE road_user = '<x>'
--       -- "how many <x> PEOPLE were parties to a KSI collision"
-- These are not the same number and must not be used interchangeably: the `pedestrian` /
-- `cyclist` / `motorcyclist` boolean columns were confirmed during Phase 2/3 build to be
-- collision-level flags, duplicated identically across every person-row of a collision
-- (including the driver, passengers, etc. of that same event) -- COUNT(*) on those flags would
-- silently count non-pedestrians who merely happened to be in a pedestrian-involving collision.
-- road_user is the actual per-person field and is what a true person-count must use.
--
-- Grain: one row per year.
--
-- Limitation: a collision with 2 injured pedestrians contributes 1 to ped_collision_count but
-- 2 to ped_person_count -- the gap between the two columns is a real, expected feature of the
-- data, not an error.
--
-- [Phase 4 addition] {x}_fatal_collision_count added per road-user type -- lets Power BI Page 3
-- show "severity by road-user type, over time, filterable by year" from this one view instead
-- of re-deriving the collision-level-flag logic in DAX. Same COUNT(DISTINCT collision_id)
-- pattern as everywhere else this flag is used. Appended at the end of the column list (not
-- interleaved with each type's existing columns) because PostgreSQL's CREATE OR REPLACE VIEW
-- requires existing columns to keep their ordinal position -- new columns can only be added
-- at the end.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.v_road_user_involvement AS
SELECT
    d.year,
    COUNT(DISTINCT f.collision_id) FILTER (WHERE f.pedestrian) AS ped_collision_count,
    COUNT(*) FILTER (WHERE f.road_user = 'pedestrian') AS ped_person_count,
    COUNT(DISTINCT f.collision_id) FILTER (WHERE f.cyclist) AS cyclist_collision_count,
    COUNT(*) FILTER (WHERE f.road_user = 'cyclist') AS cyclist_person_count,
    COUNT(DISTINCT f.collision_id) FILTER (WHERE f.motorcyclist) AS motorcyclist_collision_count,
    COUNT(*) FILTER (WHERE f.road_user = 'motorcyclist') AS motorcyclist_person_count,
    COUNT(DISTINCT f.collision_id) AS ksi_collision_count,
    COUNT(DISTINCT f.collision_id) FILTER (WHERE f.pedestrian AND f.acclass = 'Fatal Injury') AS ped_fatal_collision_count,
    COUNT(DISTINCT f.collision_id) FILTER (WHERE f.cyclist AND f.acclass = 'Fatal Injury') AS cyclist_fatal_collision_count,
    COUNT(DISTINCT f.collision_id) FILTER (WHERE f.motorcyclist AND f.acclass = 'Fatal Injury') AS motorcyclist_fatal_collision_count
FROM analytics.fact_collisions f
JOIN analytics.dim_date d ON d.date_key = f.date_key
WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
GROUP BY d.year
ORDER BY d.year;
