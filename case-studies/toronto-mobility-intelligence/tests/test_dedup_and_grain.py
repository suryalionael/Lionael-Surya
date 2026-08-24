"""
Tests for deduplication (staging -> clean) and grain guarantees (clean -> analytics).

The duplicate-handling test inserts a synthetic duplicate row directly into staging, re-runs
the real staging.stg_ksi_collisions -> clean.collisions transform SQL against it, and checks
that exactly one copy survives and the extra is logged in clean.dq_rejected_rows -- all
inside a single BEGIN...ROLLBACK session, so the running database is left untouched.
"""
from pathlib import Path

from conftest import psql, psql_rollback

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COLLISIONS_TRANSFORM_SQL = (PROJECT_ROOT / "sql" / "transformations" / "040_collisions.sql").read_text()

# One real row's worth of columns, duplicated with a different src_id (as if the source file
# had shipped the same person-in-collision twice under two different underlying row ids --
# the scenario the (collision_id, veh_no, per_no) dedup key is designed to catch).
_DUPLICATE_ROW_TEMPLATE = """
INSERT INTO staging.stg_ksi_collisions
    (src_id, collision_id, accdate, veh_no, per_no, acclass, longitude, latitude,
     aggressive, distracted, cyclist, motorcyclist, other_micromobility, older_adult,
     pedestrian, red_light, school_child, heavy_truck)
VALUES
    ('999901', 'TEST:DUPLICATE', '2020-06-15T10:00:00', '1', '1', 'Non-Fatal Injury',
     '-79.38', '43.65', 'false','false','false','false','false','false','false','false','false','false'),
    ('999902', 'TEST:DUPLICATE', '2020-06-15T10:00:00', '1', '1', 'Non-Fatal Injury',
     '-79.38', '43.65', 'false','false','false','false','false','false','false','false','false','false');
"""


class TestDuplicateHandling:
    def test_duplicate_natural_key_keeps_one_and_rejects_the_rest(self):
        script = _DUPLICATE_ROW_TEMPLATE + "\n" + COLLISIONS_TRANSFORM_SQL + """
            SELECT
                (SELECT count(*) FROM clean.collisions WHERE collision_id = 'TEST:DUPLICATE'),
                (SELECT count(*) FROM clean.dq_rejected_rows
                    WHERE reject_reason = 'duplicate_natural_key'
                    AND raw_row->>'collision_id' = 'TEST:DUPLICATE');
        """
        out = psql_rollback(script)
        survivors, rejected = out.strip().splitlines()[-1].split("|")
        assert survivors == "1"
        assert rejected == "1"

    def test_kept_row_is_the_lowest_source_row_id(self):
        script = _DUPLICATE_ROW_TEMPLATE + "\n" + COLLISIONS_TRANSFORM_SQL + """
            SELECT _staging_id FROM clean.collisions WHERE collision_id = 'TEST:DUPLICATE';
        """
        out = psql_rollback(script)
        assert out.strip().splitlines()[-1] == "999901"


class TestGrainInvariants:
    def test_fact_collisions_grain_is_person_per_collision(self):
        dupes = int(psql(
            "SELECT count(*) FROM ("
            "  SELECT collision_id, veh_no, per_no FROM analytics.fact_collisions"
            "  GROUP BY 1,2,3 HAVING count(*) > 1"
            ") d"
        ))
        assert dupes == 0

    def test_fact_traffic_volume_grain_is_px_by_count_date(self):
        dupes = int(psql(
            "SELECT count(*) FROM ("
            "  SELECT px, count_date FROM analytics.fact_traffic_volume"
            "  GROUP BY 1,2 HAVING count(*) > 1"
            ") d"
        ))
        assert dupes == 0

    def test_fact_traffic_volume_excludes_midblock_px_null_rows(self):
        # Approved scope decision (docs/DATA_MODEL.md S3.4): px IS NULL rows never reach
        # the fact table, even though they exist in clean.traffic_volume.
        null_px_in_fact = int(psql("SELECT count(*) FROM analytics.fact_traffic_volume WHERE px IS NULL"))
        null_px_in_clean = int(psql("SELECT count(*) FROM clean.traffic_volume WHERE px IS NULL"))
        assert null_px_in_fact == 0
        assert null_px_in_clean > 0  # sanity: the exclusion is a real scoping choice, not a no-op

    def test_bridge_grain_is_one_row_per_collision(self):
        dupes = int(psql(
            "SELECT count(*) FROM ("
            "  SELECT collision_id FROM analytics.bridge_collision_intersection"
            "  GROUP BY 1 HAVING count(*) > 1"
            ") d"
        ))
        assert dupes == 0

    def test_dim_date_has_no_gaps_across_its_range(self):
        gap_days = psql(
            "SELECT (max(date_key) - min(date_key) + 1) - count(*) FROM analytics.dim_date"
        )
        assert gap_days == "0"

    def test_dim_intersection_px_is_unique(self):
        dupes = int(psql(
            "SELECT count(*) FROM (SELECT px FROM analytics.dim_intersection GROUP BY 1 HAVING count(*) > 1) d"
        ))
        assert dupes == 0
