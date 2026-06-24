"""Unit tests for src.ingestion.bps_client.BPSClient. No real network calls --
src.utils.http.fetch_url is monkeypatched with fixture responses.
"""

import pytest

from src.ingestion import bps_client as bps_client_module
from src.ingestion.bps_client import BPSAPIError, BPSClient


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_get_dynamic_table_raises_without_table_id(monkeypatch):
    client = BPSClient(api_key="dummy-key")
    with pytest.raises(BPSAPIError, match="No table_id configured"):
        client.get_dynamic_table(domain="0000", table_id=None)


def test_get_dynamic_table_raises_on_missing_key_error(monkeypatch):
    """Reproduces the real BPS behavior: a 200 OK whose JSON body signals failure."""
    monkeypatch.setattr(
        bps_client_module,
        "fetch_url",
        lambda url, params=None, headers=None, timeout=30: FakeResponse({"status": "Error", "message": "Parameter Key is Missing."}),
    )
    client = BPSClient(api_key="dummy-key")
    with pytest.raises(BPSAPIError, match="non-OK status"):
        client.get_dynamic_table(domain="0000", table_id="123")


def test_get_dynamic_table_returns_payload_on_success(monkeypatch):
    success_payload = {"status": "OK", "data": [{}, []], "datacontent": {}}
    monkeypatch.setattr(
        bps_client_module,
        "fetch_url",
        lambda url, params=None, headers=None, timeout=30: FakeResponse(success_payload),
    )
    client = BPSClient(api_key="dummy-key")
    result = client.get_dynamic_table(domain="0000", table_id="123")
    assert result == success_payload


def test_get_province_domains_raises_on_error_status(monkeypatch):
    monkeypatch.setattr(
        bps_client_module,
        "fetch_url",
        lambda url, params=None, headers=None, timeout=30: FakeResponse({"status": "Error", "message": "boom"}),
    )
    client = BPSClient(api_key="dummy-key")
    with pytest.raises(BPSAPIError, match="domain list returned non-OK"):
        client.get_province_domains()
