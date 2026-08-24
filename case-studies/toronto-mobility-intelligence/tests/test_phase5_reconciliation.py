"""
Phase 5 reconciliation tests: confirm the new v_severity_by_road_user_type view (added to
close a real gap found while building the Power BI DAX measures -- see docs/DECISION_LOG.md)
behaves correctly, and re-check the headline dashboard numbers this phase's KPI cards and
charts were built against, so a future data refresh can't silently drift without a test
catching it.
"""
from conftest import psql


def _int(expr: str) -> int:
    return int(psql(f"SELECT {expr}"))


class TestSeverityByRoadUserView:
    def test_five_categories(self):
        assert _int("(SELECT COUNT(*) FROM analytics.v_severity_by_road_user_type)") == 5

    def test_categories_not_mutually_exclusive_so_no_sum_constraint(self):
        # Sanity check only: the "All KSI collisions (citywide)" row exists and is the largest.
        citywide = _int(
            "(SELECT ksi_collision_count FROM analytics.v_severity_by_road_user_type "
            "WHERE category = 'All KSI collisions (citywide)')"
        )
        maxcat = _int(
            "(SELECT MAX(ksi_collision_count) FROM analytics.v_severity_by_road_user_type "
            "WHERE category <> 'All KSI collisions (citywide)')"
        )
        assert citywide >= maxcat

    def test_fatal_share_bounded_0_100(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_severity_by_road_user_type "
            "WHERE fatal_share_pct < 0 OR fatal_share_pct > 100)"
        )
        assert bad == 0

    def test_pedestrian_fatal_share_matches_known_value(self):
        # Locks in the exact figure docs/ANALYTICAL_FINDINGS.md and the dashboard cite (17.54%).
        pct = psql(
            "SELECT fatal_share_pct FROM analytics.v_severity_by_road_user_type WHERE category = 'Pedestrian'"
        )
        assert pct == "17.54"


class TestDashboardHeadlineReconciliation:
    """Re-derives every number the Power BI KPI cards / prototype headline visuals show,
    independent of the TMDL/HTML build -- if a future data refresh changes these, this test
    (not a visual inspection) is what catches it."""

    def test_total_ksi_and_fatal(self):
        assert _int("(SELECT SUM(ksi_collision_count) FROM analytics.v_annual_ksi)") == 7578
        assert _int("(SELECT SUM(fatal_collision_count) FROM analytics.v_annual_ksi)") == 1061

    def test_spatial_match_counts(self):
        assert _int("(SELECT COUNT(*) FROM analytics.bridge_collision_intersection WHERE match_status='matched')") == 3392
        assert _int("(SELECT COUNT(*) FROM analytics.bridge_collision_intersection)") == 7587

    def test_peak_hour_is_friday_18(self):
        row = psql(
            "SELECT day_name || '|' || hour_of_day FROM analytics.v_collision_hour_weekday "
            "ORDER BY ksi_collision_count DESC LIMIT 1"
        )
        assert row == "Friday|18"

    def test_highest_fatal_share_season_is_winter(self):
        season = psql(
            "SELECT season FROM analytics.v_collision_seasonal_pattern ORDER BY fatal_share_pct DESC LIMIT 1"
        )
        assert season == "Winter"

    def test_west_humber_clairville_rank_contrast(self):
        row = psql(
            "SELECT rank_by_raw_count || '|' || rank_by_density FROM analytics.v_neighbourhood_ksi "
            "WHERE area_name = 'West Humber-Clairville'"
        )
        assert row == "1|120"
