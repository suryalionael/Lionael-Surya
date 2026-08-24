"""
Shared test fixtures. Tests talk to the running Postgres container via `docker compose exec
... psql`, the same mechanism the pipeline itself uses -- no psycopg2 dependency, and it
exercises the real SQL (helper functions, constraints, the spatial match query) rather than a
Python re-implementation of it.
"""
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_env() -> dict:
    env = {}
    for line in (PROJECT_ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    return env


ENV = _load_env()
DB_USER = ENV.get("POSTGRES_USER", "tmi")
DB_NAME = ENV.get("POSTGRES_DB", "toronto_mobility")


def psql(sql: str, field_sep: str = "|") -> str:
    """Run a SQL string as its own session/transaction and return stdout."""
    proc = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "psql", "-v", "ON_ERROR_STOP=1",
         "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-F", field_sep, "-c", sql],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"psql failed:\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout.strip()


def psql_rollback(statements: str, field_sep: str = "|") -> str:
    """Run a multi-statement script inside BEGIN ... ROLLBACK -- lets a test insert bad data
    and exercise the real transform logic against it without permanently mutating the DB.
    psql prints a command tag (e.g. "ROLLBACK", "TRUNCATE TABLE") after every statement, even
    in -t mode -- the trailing "ROLLBACK" tag this wrapper adds is stripped so callers can
    treat the return value as just their own statements' output."""
    script = "BEGIN;\n" + statements + "\nROLLBACK;\n"
    out = psql(script, field_sep=field_sep)
    lines = out.splitlines()
    assert lines and lines[-1] == "ROLLBACK", f"expected trailing ROLLBACK tag, got: {lines[-3:]}"
    return "\n".join(lines[:-1])


@pytest.fixture(scope="session", autouse=True)
def _require_database():
    try:
        psql("SELECT 1")
    except Exception as exc:
        pytest.exit(f"Database not reachable via `docker compose exec db psql` -- run `make up` first.\n{exc}")
