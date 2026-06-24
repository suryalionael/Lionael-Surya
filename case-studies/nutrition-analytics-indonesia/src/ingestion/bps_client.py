"""Thin client for the BPS WebAPI (https://webapi.bps.go.id/).

BPS wraps errors in an HTTP 200 response body (e.g. {"status":"Error","message":
"Parameter Key is Missing."}) rather than using HTTP error codes, so a 200 status
alone does not mean success -- the JSON "status" field must be checked.
"""

import logging

from src.utils.config import get_bps_api_key
from src.utils.http import fetch_url

log = logging.getLogger(__name__)

BASE_URL = "https://webapi.bps.go.id/v1/api"


class BPSAPIError(Exception):
    pass


class BPSClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_bps_api_key()

    def get_dynamic_table(self, *, domain: str, table_id: str, **extra_params) -> dict:
        if not table_id:
            raise BPSAPIError(
                "No table_id configured for this dataset in config/datasets.yml. "
                "Confirm the real var id via the BPS WebAPI (list/model/var) before fetching -- "
                "never guess a table id."
            )
        params = {"key": self.api_key, "var": table_id, **extra_params}
        url = f"{BASE_URL}/list/model/data/lang/ind/domain/{domain}/"
        response = fetch_url(url, params=params)
        payload = response.json()
        if payload.get("status") != "OK":
            raise BPSAPIError(f"BPS WebAPI returned non-OK status for table_id={table_id}: {payload}")
        return payload

    def get_province_domains(self) -> list[dict]:
        url = f"{BASE_URL}/domain/type/prov/"
        response = fetch_url(url, params={"key": self.api_key})
        payload = response.json()
        if payload.get("status") != "OK":
            raise BPSAPIError(f"BPS WebAPI domain list returned non-OK status: {payload}")
        return payload["data"][1]

    def get_th_list(self, *, domain: str, table_id: str) -> list[dict]:
        """The set of valid 'th' (period) ids for a given var -- required because the
        data endpoint rejects requests with no 'th' param ("'th' parameter is required"),
        and th ids are an opaque internal id (e.g. th_id=124 means year 2024), not the
        literal year, so they must be looked up rather than assumed."""
        url = f"{BASE_URL}/list/model/th/domain/{domain}/var/{table_id}/"
        response = fetch_url(url, params={"key": self.api_key})
        payload = response.json()
        if payload.get("status") != "OK":
            raise BPSAPIError(f"BPS WebAPI th list returned non-OK status for table_id={table_id}: {payload}")
        return payload["data"][1]

    def get_latest_th_range(self, *, domain: str, table_id: str, n_periods: int = 3) -> str:
        """th list is returned newest-first; build a BPS-style colon range covering the
        n most recent periods, e.g. '123:125'."""
        periods = self.get_th_list(domain=domain, table_id=table_id)
        if not periods:
            raise BPSAPIError(f"No th (period) values available for table_id={table_id}")
        ids = sorted(p["th_id"] for p in periods)[-n_periods:]
        return f"{ids[0]}:{ids[-1]}" if len(ids) > 1 else str(ids[0])
