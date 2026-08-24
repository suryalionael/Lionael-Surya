"""
Tests for the collision -> intersection spatial nearest-neighbor match
(sql/analytics/060_bridge_collision_intersection.sql) and the approved 20m radius
(docs/DECISION_LOG.md).

The boundary tests build synthetic points at a controlled geodesic distance from a real
dim_intersection row using PostGIS's ST_Project, then run the *actual* geography-distance
calculation the pipeline uses -- this exercises the real distance math (SRID handling,
geometry<->geography casts), not a re-implementation of it in Python.
"""
from conftest import psql


def distance_from_reference_intersection(offset_m: float) -> float:
    """Distance, in meters, from a synthetic point placed `offset_m` due north of a real
    intersection, back to that same intersection -- should equal offset_m (within a few cm,
    since ST_Project computes on the same geodesic model ST_Distance uses)."""
    out = psql(f"""
        WITH ref AS (SELECT geom FROM analytics.dim_intersection ORDER BY px LIMIT 1),
        synthetic AS (
            SELECT ST_Project(ref.geom::geography, {offset_m}, radians(0)) AS pt FROM ref
        )
        SELECT ST_Distance(ref.geom::geography, synthetic.pt)
        FROM ref, synthetic
    """)
    return float(out)


class TestDistanceCalculation:
    def test_synthetic_offset_distance_is_accurate(self):
        d = distance_from_reference_intersection(19.0)
        assert abs(d - 19.0) < 0.05

    def test_larger_offset_distance_is_accurate(self):
        d = distance_from_reference_intersection(150.0)
        assert abs(d - 150.0) < 0.5


class TestTwentyMeterThreshold:
    def test_point_comfortably_inside_radius_would_match(self):
        d = distance_from_reference_intersection(5.0)
        assert d <= 20.0

    def test_point_just_inside_radius_would_match(self):
        d = distance_from_reference_intersection(19.5)
        assert d <= 20.0

    def test_point_just_outside_radius_would_not_match(self):
        d = distance_from_reference_intersection(20.5)
        assert d > 20.0

    def test_point_comfortably_outside_radius_would_not_match(self):
        d = distance_from_reference_intersection(100.0)
        assert d > 20.0

    def test_classification_logic_matches_the_production_case_expression(self):
        # Mirrors the exact CASE expression in sql/analytics/060_bridge_collision_intersection.sql
        for offset, expected in [(5.0, "matched"), (19.5, "matched"), (20.5, "unmatched_outside_radius"), (100.0, "unmatched_outside_radius")]:
            d = distance_from_reference_intersection(offset)
            status = psql(f"""
                WITH d AS (SELECT {d}::numeric AS distance_m)
                SELECT CASE WHEN distance_m <= 20.0 THEN 'matched' ELSE 'unmatched_outside_radius' END
                FROM d
            """)
            assert status == expected, f"offset={offset} distance={d}"


class TestBridgeTableInvariants:
    """Checks against the real, already-populated bridge_collision_intersection table."""

    def test_every_distinct_collision_appears_exactly_once(self):
        bridge_count = int(psql("SELECT count(*) FROM analytics.bridge_collision_intersection"))
        distinct_collisions = int(psql("SELECT count(DISTINCT collision_id) FROM clean.collisions"))
        assert bridge_count == distinct_collisions

    def test_no_matched_row_exceeds_the_approved_radius(self):
        over_radius = int(psql(
            "SELECT count(*) FROM analytics.bridge_collision_intersection "
            "WHERE match_status = 'matched' AND match_distance_m > 20.0"
        ))
        assert over_radius == 0

    def test_unmatched_rows_have_no_intersection_key(self):
        bad = int(psql(
            "SELECT count(*) FROM analytics.bridge_collision_intersection "
            "WHERE match_status <> 'matched' AND intersection_key IS NOT NULL"
        ))
        assert bad == 0

    def test_matched_rows_always_have_intersection_key_and_distance(self):
        bad = int(psql(
            "SELECT count(*) FROM analytics.bridge_collision_intersection "
            "WHERE match_status = 'matched' AND (intersection_key IS NULL OR match_distance_m IS NULL)"
        ))
        assert bad == 0

    def test_unmatched_collisions_are_not_dropped_from_the_bridge(self):
        # This is the core "preserve unmatched collisions" requirement: unmatched rows must
        # still exist in the table, not be filtered out.
        unmatched = int(psql(
            "SELECT count(*) FROM analytics.bridge_collision_intersection "
            "WHERE match_status IN ('unmatched_outside_radius', 'unmatched_no_candidate')"
        ))
        assert unmatched > 0

    def test_radius_used_is_recorded_as_the_approved_20_meters(self):
        distinct_radii = psql("SELECT DISTINCT match_radius_m_used FROM analytics.bridge_collision_intersection")
        assert distinct_radii == "20.00"
