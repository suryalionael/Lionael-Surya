-- Defensive-cast helpers used by every staging -> clean transform. A malformed value in one
-- row must never abort the whole batch load (Postgres's normal ::type cast raises and stops
-- the statement) -- these return NULL instead, so the calling transform can decide whether a
-- NULL there means "reject the row" (required field) or "keep the row, flag the field"
-- (optional field). This is what makes "avoid silently dropping rows" and "do not arbitrarily
-- delete suspicious records" both achievable at the same time.

CREATE OR REPLACE FUNCTION clean.safe_int(t text) RETURNS integer AS $$
BEGIN
    RETURN NULLIF(TRIM(t), '')::integer;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION clean.safe_bigint(t text) RETURNS bigint AS $$
BEGIN
    RETURN NULLIF(TRIM(t), '')::bigint;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION clean.safe_numeric(t text) RETURNS numeric AS $$
BEGIN
    RETURN NULLIF(TRIM(t), '')::numeric;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION clean.safe_double(t text) RETURNS double precision AS $$
BEGIN
    RETURN NULLIF(TRIM(t), '')::double precision;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION clean.safe_timestamp(t text) RETURNS timestamp AS $$
BEGIN
    RETURN NULLIF(TRIM(t), '')::timestamp;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION clean.safe_date(t text) RETURNS date AS $$
BEGIN
    RETURN NULLIF(TRIM(t), '')::date;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Source boolean-style flags appear as 'true'/'false' text (KSI) or '1'/NULL (Traffic
-- Signals) depending on the dataset -- both encodings observed directly in the raw data
-- during Phase 1/2 research, not assumed.
CREATE OR REPLACE FUNCTION clean.safe_bool(t text) RETURNS boolean AS $$
BEGIN
    RETURN CASE lower(TRIM(COALESCE(t, '')))
        WHEN 'true' THEN true
        WHEN 'false' THEN false
        WHEN 'yes' THEN true
        WHEN 'no' THEN false
        WHEN '1' THEN true
        WHEN '0' THEN false
        ELSE NULL
    END;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Builds a SRID 4326 point from text lon/lat, returning NULL (not an error) when either
-- coordinate is unparseable OR falls outside a generous Toronto bounding box (a wide margin
-- around the city -- true edge-of-city collisions stay inside it; this only catches obvious
-- geocoding errors, e.g. a swapped lat/long or a stray 0,0).
CREATE OR REPLACE FUNCTION clean.safe_toronto_point(lon text, lat text) RETURNS geometry AS $$
DECLARE
    lon_d double precision := clean.safe_double(lon);
    lat_d double precision := clean.safe_double(lat);
BEGIN
    IF lon_d IS NULL OR lat_d IS NULL THEN
        RETURN NULL;
    END IF;
    IF lon_d < -80.0 OR lon_d > -78.9 OR lat_d < 43.4 OR lat_d > 44.0 THEN
        RETURN NULL;
    END IF;
    RETURN ST_SetSRID(ST_MakePoint(lon_d, lat_d), 4326);
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Safe GeoJSON parse -- PostGIS's ST_GeomFromGeoJSON raises a hard error on malformed
-- input, which would otherwise abort an entire batch INSERT over one bad row.
CREATE OR REPLACE FUNCTION clean.safe_geom_from_geojson(t text) RETURNS geometry AS $$
BEGIN
    IF t IS NULL OR TRIM(t) = '' THEN
        RETURN NULL;
    END IF;
    RETURN ST_GeomFromGeoJSON(t);
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Same Toronto bounding-box check as safe_toronto_point, applied to an already-built point
-- geometry (used for the geometry-column sources like Traffic Signals, rather than separate
-- lon/lat text columns).
CREATE OR REPLACE FUNCTION clean.point_in_toronto_bounds(g geometry) RETURNS boolean AS $$
BEGIN
    IF g IS NULL THEN
        RETURN false;
    END IF;
    RETURN ST_X(g) BETWEEN -80.0 AND -78.9 AND ST_Y(g) BETWEEN 43.4 AND 44.0;
EXCEPTION WHEN OTHERS THEN
    RETURN false;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
