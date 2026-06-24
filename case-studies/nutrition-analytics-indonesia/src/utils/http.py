"""Shared HTTP fetch helpers. Every ingestion script goes through these so retry,
backoff, and failure semantics are implemented exactly once.

On final failure these always raise -- they never return a fabricated or empty
response. A source that cannot be reached is a failed ingestion run, not an
excuse to substitute synthetic data.
"""

import logging

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tqdm import tqdm

log = logging.getLogger(__name__)

_RETRYABLE = (requests.ConnectionError, requests.Timeout, requests.HTTPError)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, max=30),
    retry=retry_if_exception_type(_RETRYABLE),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def fetch_url(url: str, *, params: dict | None = None, headers: dict | None = None, timeout: int = 30) -> requests.Response:
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, max=30),
    retry=retry_if_exception_type(_RETRYABLE),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def download_file(url: str, dest_path, *, min_size_bytes: int = 1024, timeout: int = 60) -> int:
    """Stream a (possibly large) file to disk. Returns the number of bytes written.

    Raises if the final file is smaller than ``min_size_bytes`` -- a 200 OK with a
    near-empty or error-page body is not a successful download.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        written = 0
        with open(dest_path, "wb") as f, tqdm(total=total or None, unit="B", unit_scale=True, desc=dest_path.name) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    written += len(chunk)
                    bar.update(len(chunk))

    if written < min_size_bytes:
        dest_path.unlink(missing_ok=True)
        raise ValueError(f"Downloaded file from {url} is only {written} bytes (< {min_size_bytes}) -- treating as a failed download, not a real file.")

    return written
