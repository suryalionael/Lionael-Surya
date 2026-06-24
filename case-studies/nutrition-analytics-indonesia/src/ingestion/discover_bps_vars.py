"""Lists BPS WebAPI variables for a domain so a human can find and confirm the real
var/table id for each dataset in config/datasets.yml. This is the "discovery" step --
it never guesses an id, it only prints what BPS itself reports, for a human to read
and transcribe.

Requires a real BPS_API_KEY (every BPS WebAPI endpoint, including this list endpoint,
rejects requests without one -- confirmed during Phase 0 research).

Root cause of the original "0 variable(s) printed" bug (fixed here): the var-list
endpoint paginates server-side at a fixed 10 results per page regardless of any
per_page param, and domain 0000 has 1699 variables across 170 pages. The first
version of this script only ever fetched page 1 (10 unrelated "Komunikasi" subject
variables), so any --search filter for poverty/IPM/population/etc. matched zero
results -- not an auth problem, not a filtering-logic bug, a missing pagination loop.

Usage:
    python -m src.ingestion.discover_bps_vars                  # list all vars, domain 0000
    python -m src.ingestion.discover_bps_vars --search miskin   # filter by label substring
"""

import argparse
import logging

from src.utils.config import get_bps_api_key
from src.utils.http import fetch_url

log = logging.getLogger(__name__)

VAR_LIST_URL = "https://webapi.bps.go.id/v1/api/list/model/var/domain/{domain}/"


def fetch_page(domain: str, key: str, page: int) -> dict:
    response = fetch_url(VAR_LIST_URL.format(domain=domain), params={"key": key, "page": page})
    log.debug("GET %s page=%d -> HTTP %d", response.url.replace(key, "<key>"), page, response.status_code)
    payload = response.json()
    if payload.get("status") != "OK":
        raise RuntimeError(f"BPS WebAPI var list returned non-OK status (page={page}): {payload}")
    return payload


def list_vars(domain: str = "0000") -> list[dict]:
    key = get_bps_api_key()

    first = fetch_page(domain, key, page=1)
    meta, variables = first["data"][0], list(first["data"][1])
    total_pages = meta["pages"]
    log.info(
        "BPS var list domain=%s: %d total variables across %d pages (per_page=%d, server-fixed)",
        domain, meta["total"], total_pages, meta["per_page"],
    )

    for page in range(2, total_pages + 1):
        payload = fetch_page(domain, key, page=page)
        variables.extend(payload["data"][1])
        if page % 20 == 0 or page == total_pages:
            log.info("Fetched page %d/%d (%d variables so far)", page, total_pages, len(variables))

    return variables


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="0000")
    parser.add_argument("--search", default=None, help="case-insensitive substring filter on the variable label")
    parser.add_argument("--verbose", action="store_true", help="log each page request (DEBUG)")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        variables = list_vars(args.domain)
    except Exception:
        log.exception("Failed to list BPS variables -- check BPS_API_KEY in .env")
        return 1

    log.info("Total variables fetched (before filtering): %d", len(variables))
    log.info("Example labels: %s", [v.get("title") for v in variables[:3]])

    if args.search:
        needle = args.search.lower()
        variables = [v for v in variables if needle in v.get("title", "").lower()]
        log.info("Variables matching --search %r (after filtering): %d", args.search, len(variables))

    for v in variables:
        print(f"var={v.get('var_id')}\tsubject={v.get('sub_id')} ({v.get('sub_name')})\tunit={v.get('unit')}\t{v.get('title')}")

    log.info("%d variable(s) printed. Transcribe the correct var_id into config/datasets.yml's table_id field.", len(variables))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
