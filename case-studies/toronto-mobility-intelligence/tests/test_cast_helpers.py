"""
Unit tests for the sql/transformations/000_helpers.sql defensive-cast functions -- these are
what makes "a malformed value never aborts a batch load, and never gets silently coerced into
something wrong" true. Each test exercises the actual Postgres function, not a Python
re-implementation of its logic.
"""
from conftest import psql


def _is_null(expr: str) -> bool:
    return psql(f"SELECT ({expr}) IS NULL") == "t"


def _value(expr: str) -> str:
    return psql(f"SELECT {expr}")


class TestSafeInt:
    def test_valid_integer(self):
        assert _value("clean.safe_int('42')") == "42"

    def test_whitespace_trimmed(self):
        assert _value("clean.safe_int('  7  ')") == "7"

    def test_non_numeric_returns_null_not_error(self):
        assert _is_null("clean.safe_int('abc')")

    def test_decimal_string_returns_null(self):
        # '3.14' is not a valid integer literal -- must be caught, not raised.
        assert _is_null("clean.safe_int('3.14')")

    def test_empty_string_returns_null(self):
        assert _is_null("clean.safe_int('')")

    def test_null_input_returns_null(self):
        assert _is_null("clean.safe_int(NULL)")


class TestSafeTimestamp:
    def test_valid_iso_timestamp(self):
        assert _value("clean.safe_timestamp('2006-01-01T02:36:00')") == "2006-01-01 02:36:00"

    def test_garbage_returns_null_not_error(self):
        assert _is_null("clean.safe_timestamp('not-a-date')")

    def test_empty_string_returns_null(self):
        assert _is_null("clean.safe_timestamp('')")


class TestSafeDate:
    def test_valid_date(self):
        assert _value("clean.safe_date('2020-05-01')") == "2020-05-01"

    def test_full_timestamp_truncates_to_date(self):
        # Traffic Signals ACTIVATIONDATE ships as e.g. '1950-08-23T00:00:00'.
        assert _value("clean.safe_date('1950-08-23T00:00:00')") == "1950-08-23"

    def test_garbage_returns_null_not_error(self):
        assert _is_null("clean.safe_date('garbage')")


class TestSafeBool:
    def test_true_variants(self):
        for v in ["true", "TRUE", "yes", "1"]:
            assert _value(f"clean.safe_bool('{v}')") == "t", v

    def test_false_variants(self):
        for v in ["false", "FALSE", "no", "0"]:
            assert _value(f"clean.safe_bool('{v}')") == "f", v

    def test_unexpected_value_returns_null_not_error(self):
        assert _is_null("clean.safe_bool('maybe')")

    def test_empty_and_null_return_null(self):
        assert _is_null("clean.safe_bool('')")
        assert _is_null("clean.safe_bool(NULL)")


class TestSafeTorontoPoint:
    def test_valid_toronto_coordinates_build_a_point(self):
        # City Hall, roughly.
        assert not _is_null("clean.safe_toronto_point('-79.384', '43.653')")

    def test_coordinates_far_outside_toronto_return_null(self):
        assert _is_null("clean.safe_toronto_point('0', '0')")

    def test_swapped_lat_long_returns_null(self):
        # Latitude passed where longitude is expected -- lands far outside the bounding box.
        assert _is_null("clean.safe_toronto_point('43.653', '-79.384')")

    def test_malformed_text_returns_null_not_error(self):
        assert _is_null("clean.safe_toronto_point('not_a_number', '43.653')")

    def test_one_coordinate_missing_returns_null(self):
        assert _is_null("clean.safe_toronto_point('-79.384', '')")

    def test_point_at_edge_of_bounding_box_is_kept(self):
        assert not _is_null("clean.safe_toronto_point('-79.5', '43.75')")


class TestSafeGeomFromGeojson:
    def test_valid_point_geojson(self):
        geojson = '{"type": "Point", "coordinates": [-79.38, 43.65]}'
        assert not _is_null(f"clean.safe_geom_from_geojson('{geojson}')")

    def test_malformed_json_returns_null_not_error(self):
        assert _is_null("clean.safe_geom_from_geojson('{\"type\": not valid json')")

    def test_empty_string_returns_null(self):
        assert _is_null("clean.safe_geom_from_geojson('')")

    def test_null_input_returns_null(self):
        assert _is_null("clean.safe_geom_from_geojson(NULL)")
