"""
Tests for the Phase 4 SQL view extensions built to support the Power BI specification
(docs/POWER_BI_SPEC.md) -- three new views (v_collision_hour_weekday,
v_collision_seasonal_pattern, v_collision_monthly_pattern) and three additive extensions to
existing views (v_neighbourhood_ksi, v_intersection_risk, v_road_user_involvement).
"""
from conftest import psql


def _int(expr: str) -> int:
    return int(psql(f"SELECT {expr}"))


class TestNewTemporalViews:
    def test_hour_weekday_view_has_full_168_row_grid(self):
        assert _int("(SELECT COUNT(*) FROM analytics.v_collision_hour_weekday)") == 168

    def test_hour_weekday_view_sum_matches_citywide_ksi_total(self):
        view_sum = _int("(SELECT SUM(ksi_collision_count) FROM analytics.v_collision_hour_weekday)")
        fact_count = _int(
            "(SELECT COUNT(DISTINCT collision_id) FROM analytics.fact_collisions "
            "WHERE acclass IN ('Fatal Injury', 'Non-Fatal Injury'))"
        )
        assert view_sum == fact_count

    def test_hour_weekday_hours_cover_full_0_to_23_range(self):
        distinct_hours = _int("(SELECT COUNT(DISTINCT hour_of_day) FROM analytics.v_collision_hour_weekday)")
        assert distinct_hours == 24

    def test_seasonal_view_has_exactly_four_seasons(self):
        assert _int("(SELECT COUNT(*) FROM analytics.v_collision_seasonal_pattern)") == 4

    def test_seasonal_view_sum_matches_citywide_ksi_total(self):
        view_sum = _int("(SELECT SUM(ksi_collision_count) FROM analytics.v_collision_seasonal_pattern)")
        fact_count = _int(
            "(SELECT COUNT(DISTINCT collision_id) FROM analytics.fact_collisions "
            "WHERE acclass IN ('Fatal Injury', 'Non-Fatal Injury'))"
        )
        assert view_sum == fact_count

    def test_monthly_view_has_exactly_twelve_months(self):
        assert _int("(SELECT COUNT(*) FROM analytics.v_collision_monthly_pattern)") == 12

    def test_monthly_view_sum_matches_citywide_ksi_total(self):
        view_sum = _int("(SELECT SUM(ksi_collision_count) FROM analytics.v_collision_monthly_pattern)")
        fact_count = _int(
            "(SELECT COUNT(DISTINCT collision_id) FROM analytics.fact_collisions "
            "WHERE acclass IN ('Fatal Injury', 'Non-Fatal Injury'))"
        )
        assert view_sum == fact_count

    def test_monthly_view_coverage_reflects_partial_current_year(self):
        # Months that have occurred in the partial current year (Jan-Aug, since data runs
        # through early August) should show 21 years of coverage; later months only 20.
        early_month_coverage = _int(
            "(SELECT month_year_coverage FROM analytics.v_collision_monthly_pattern WHERE month = 1)"
        )
        late_month_coverage = _int(
            "(SELECT month_year_coverage FROM analytics.v_collision_monthly_pattern WHERE month = 12)"
        )
        assert early_month_coverage == late_month_coverage + 1


class TestExtendedNeighbourhoodView:
    def test_pedestrian_and_cyclist_counts_never_exceed_total(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_neighbourhood_ksi "
            "WHERE pedestrian_collision_count > ksi_collision_count "
            "OR cyclist_collision_count > ksi_collision_count)"
        )
        assert bad == 0

    def test_still_covers_all_158_neighbourhoods(self):
        # Confirmed in Phase 4 design: every neighbourhood has >=1 KSI collision, so the
        # inner join was never silently dropping empty-count neighbourhoods.
        assert _int("(SELECT COUNT(*) FROM analytics.v_neighbourhood_ksi)") == 158


class TestExtendedIntersectionView:
    def test_latitude_longitude_always_populated(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_intersection_risk "
            "WHERE latitude IS NULL OR longitude IS NULL)"
        )
        assert bad == 0

    def test_coordinates_fall_within_toronto_bounds(self):
        bad = _int("""(
            SELECT COUNT(*) FROM analytics.v_intersection_risk
            WHERE longitude NOT BETWEEN -80.0 AND -78.9 OR latitude NOT BETWEEN 43.4 AND 44.0
        )""")
        assert bad == 0


class TestExtendedRoadUserView:
    def test_fatal_counts_never_exceed_involvement_counts(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_road_user_involvement "
            "WHERE ped_fatal_collision_count > ped_collision_count "
            "OR cyclist_fatal_collision_count > cyclist_collision_count "
            "OR motorcyclist_fatal_collision_count > motorcyclist_collision_count)"
        )
        assert bad == 0

    def test_fatal_counts_never_negative(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_road_user_involvement "
            "WHERE ped_fatal_collision_count < 0 OR cyclist_fatal_collision_count < 0 "
            "OR motorcyclist_fatal_collision_count < 0)"
        )
        assert bad == 0
