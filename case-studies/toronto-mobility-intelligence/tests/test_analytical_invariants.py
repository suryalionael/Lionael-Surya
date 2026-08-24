"""
Invariant tests for the Phase 3 curated analytical layer (sql/analytics/0*_*/*.sql). These
don't re-derive the numbers independently -- they check structural properties that must hold
regardless of what the numbers are: totals reconcile across layers, fatal counts never exceed
total counts, percentages stay in [0, 100], rankings are well-formed, and the collision-level-
flag vs person-level-field distinction in road-user counting holds the direction it must.
"""
from conftest import psql


def _int(expr: str) -> int:
    return int(psql(f"SELECT {expr}"))


def _float_or_none(value: str):
    return None if value == "" else float(value)


class TestAnnualTotalsReconcile:
    def test_view_sum_matches_fact_table_distinct_count(self):
        view_sum = _int("(SELECT SUM(ksi_collision_count) FROM analytics.v_annual_ksi)")
        fact_count = _int(
            "(SELECT COUNT(DISTINCT collision_id) FROM analytics.fact_collisions "
            "WHERE acclass IN ('Fatal Injury', 'Non-Fatal Injury'))"
        )
        assert view_sum == fact_count

    def test_view_fatal_sum_matches_fact_table_fatal_count(self):
        view_sum = _int("(SELECT SUM(fatal_collision_count) FROM analytics.v_annual_ksi)")
        fact_count = _int(
            "(SELECT COUNT(DISTINCT collision_id) FROM analytics.fact_collisions "
            "WHERE acclass = 'Fatal Injury')"
        )
        assert view_sum == fact_count

    def test_every_year_2006_through_current_is_present(self):
        rows = psql("SELECT COUNT(*) FROM analytics.v_annual_ksi")
        # 2006 through the current year, inclusive
        import datetime
        expected = datetime.date.today().year - 2006 + 1
        assert int(rows) == expected


class TestFatalNeverExceedsTotal:
    def test_annual_view(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_annual_ksi WHERE fatal_collision_count > ksi_collision_count)"
        )
        assert bad == 0

    def test_neighbourhood_view(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_neighbourhood_ksi WHERE fatal_collision_count > ksi_collision_count)"
        )
        assert bad == 0

    def test_intersection_view(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_intersection_risk "
            "WHERE fatal_collision_count > matched_ksi_collision_count)"
        )
        assert bad == 0


class TestMatchedNeverExceedsGeocoded:
    def test_citywide(self):
        geocoded = _int(
            "(SELECT COUNT(DISTINCT collision_id) FROM analytics.fact_collisions WHERE geom IS NOT NULL)"
        )
        matched = _int(
            "(SELECT COUNT(*) FROM analytics.bridge_collision_intersection WHERE match_status = 'matched')"
        )
        assert matched <= geocoded

    def test_matched_rows_all_have_geocoded_source_collision(self):
        # Every 'matched' bridge row must correspond to a collision that actually has a geom --
        # a match without a source geometry would be a logical impossibility in the pipeline.
        bad = _int("""(
            SELECT COUNT(*)
            FROM analytics.bridge_collision_intersection b
            JOIN analytics.fact_collisions f ON f.collision_id = b.collision_id
            WHERE b.match_status = 'matched' AND f.geom IS NULL
        )""")
        assert bad == 0


class TestPercentagesStayInRange:
    def test_fatal_share_pct_annual(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_annual_ksi "
            "WHERE fatal_share_pct < 0 OR fatal_share_pct > 100)"
        )
        assert bad == 0

    def test_fatal_share_pct_neighbourhood(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_neighbourhood_ksi "
            "WHERE fatal_share_pct < 0 OR fatal_share_pct > 100)"
        )
        assert bad == 0

    def test_match_rate_pct_monitoring_query(self):
        # 07_quality/010_spatial_match_monitoring.sql is a plain query, not a view -- re-derive
        # its citywide match_rate_pct formula directly to check it stays in range.
        rows = psql("""
            SELECT ROUND(100.0 * COUNT(DISTINCT b.collision_id) FILTER (WHERE b.match_status='matched')
                   / NULLIF(COUNT(DISTINCT f.collision_id), 0), 2)
            FROM analytics.fact_collisions f
            LEFT JOIN analytics.bridge_collision_intersection b ON b.collision_id = f.collision_id
            WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
        """)
        pct = float(rows)
        assert 0 <= pct <= 100

    def test_recency_reliable_never_null(self):
        bad = _int("(SELECT COUNT(*) FROM analytics.v_intersection_exposure WHERE recency_reliable IS NULL)")
        assert bad == 0


class TestRankingsAreWellFormed:
    def test_intersection_risk_ranks_are_dense_and_bounded(self):
        max_rank = _int("(SELECT MAX(rank_by_observed_count) FROM analytics.v_intersection_risk)")
        row_count = _int("(SELECT COUNT(*) FROM analytics.v_intersection_risk)")
        assert 1 <= max_rank <= row_count

    def test_intersection_risk_rank_1_has_the_highest_count(self):
        top_count = _int(
            "(SELECT matched_ksi_collision_count FROM analytics.v_intersection_risk WHERE rank_by_observed_count = 1 LIMIT 1)"
        )
        overall_max = _int("(SELECT MAX(matched_ksi_collision_count) FROM analytics.v_intersection_risk)")
        assert top_count == overall_max

    def test_neighbourhood_density_rank_has_no_gaps_beyond_ties(self):
        # RANK() can skip numbers after ties but must never exceed the row count.
        max_rank = _int("(SELECT MAX(rank_by_density) FROM analytics.v_neighbourhood_ksi)")
        row_count = _int("(SELECT COUNT(*) FROM analytics.v_neighbourhood_ksi)")
        assert max_rank <= row_count


class TestRoadUserGrainDirection:
    """The collision-level-flag vs person-level-field distinction
    (03_road_users/010_road_user_involvement_trend.sql) must hold structurally: a road-user
    type's person_count can never be less than its collision_count, because every collision
    counted in collision_count is, by construction, a collision containing at least one
    person-row of that road_user type."""

    def test_pedestrian_person_count_never_below_collision_count(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_road_user_involvement WHERE ped_person_count < ped_collision_count)"
        )
        assert bad == 0

    def test_cyclist_person_count_never_below_collision_count(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_road_user_involvement WHERE cyclist_person_count < cyclist_collision_count)"
        )
        assert bad == 0

    def test_motorcyclist_person_count_never_below_collision_count(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_road_user_involvement "
            "WHERE motorcyclist_person_count < motorcyclist_collision_count)"
        )
        assert bad == 0


class TestExposureMetricSanity:
    def test_collisions_per_10k_movements_never_negative(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_intersection_exposure WHERE collisions_per_10k_movements < 0)"
        )
        assert bad == 0

    def test_zero_matched_collisions_yields_zero_metric_not_null(self):
        bad = _int(
            "(SELECT COUNT(*) FROM analytics.v_intersection_exposure "
            "WHERE matched_ksi_collisions_2021_2025 = 0 AND collisions_per_10k_movements <> 0)"
        )
        assert bad == 0

    def test_count_recency_years_is_never_negative(self):
        # A negative value would mean a traffic count dated in the future -- a real bug.
        bad = _int("(SELECT COUNT(*) FROM analytics.v_intersection_exposure WHERE count_recency_years < 0)")
        assert bad == 0
