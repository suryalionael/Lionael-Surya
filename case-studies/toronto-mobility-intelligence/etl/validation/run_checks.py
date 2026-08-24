#!/usr/bin/env python3
"""
Run the sql/quality/*.sql data-quality checks against the running database and print a
PASS/WARN/FAIL report. Exits non-zero if any check FAILs (WARN does not fail the build --
it flags something worth a human look, e.g. a match rate drifting from its documented
Phase 1 prediction).

Each check file must return rows shaped (check_name, status, detail) -- see the files in
sql/quality/ for the pattern. sql/quality/000_row_counts.sql is a plain row-count report
(different shape) and is printed separately, not scored.
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUALITY_DIR = PROJECT_ROOT / "sql" / "quality"

ENV = {}
for line in (PROJECT_ROOT / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k] = v

DB_USER = ENV.get("POSTGRES_USER", "tmi")
DB_NAME = ENV.get("POSTGRES_DB", "toronto_mobility")

RESET = "\033[0m"
COLORS = {"PASS": "\033[32m", "WARN": "\033[33m", "FAIL": "\033[31m"}


def run_sql_file(container_path: str, field_sep: str = "|") -> str:
    proc = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "psql", "-v", "ON_ERROR_STOP=1",
         "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-F", field_sep, "-f", container_path],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"query failed: {container_path}")
    return proc.stdout


def main() -> int:
    print("=== Row counts (staging / clean / analytics) ===")
    counts_out = run_sql_file("/sql/quality/000_row_counts.sql")
    for line in counts_out.strip().splitlines():
        if not line:
            continue
        table, count = line.split("|")
        print(f"  {table:<42} {count:>8}")

    check_files = sorted(f for f in QUALITY_DIR.glob("*.sql") if f.name != "000_row_counts.sql")

    print("\n=== Data quality checks ===")
    tally = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for f in check_files:
        out = run_sql_file(f"/sql/quality/{f.name}")
        for line in out.strip().splitlines():
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) != 3:
                continue
            check_name, status, detail = parts
            status = status.strip()
            tally[status] = tally.get(status, 0) + 1
            color = COLORS.get(status, "")
            print(f"  {color}[{status:<4}]{RESET} {check_name:<48} {detail}")

    print(f"\n{tally['PASS']} PASS, {tally['WARN']} WARN, {tally['FAIL']} FAIL")
    if tally["FAIL"] > 0:
        print("\nVALIDATION FAILED.")
        return 1
    if tally["WARN"] > 0:
        print("\nValidation passed with warnings.")
        return 0
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
