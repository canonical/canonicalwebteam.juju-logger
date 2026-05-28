import json
import logging
import os
import sqlite3
import subprocess
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator
from urllib.parse import urlparse

from src.utils import get_flask_env

logger = logging.getLogger(__name__)

RETENTION_DAYS = 7

if os.getenv("DEBUG_MODE"):
    _DB_PATH = Path("./juju-logger.db")
else:
    _DB_PATH = Path("/var/logs/juju-logger/juju-logger.db")


def _db_path() -> Path:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return _DB_PATH


@contextmanager
def _conn() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _init_db() -> None:
    """Create the request_logs table and index if they do not already exist."""
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS request_logs (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at       TEXT    NOT NULL,
                url                TEXT    NOT NULL,
                resolver_ip        TEXT    NOT NULL,
                http_status        INTEGER,
                time_connect       REAL,
                time_starttransfer REAL,
                time_total         REAL,
                size_download      INTEGER,
                size_upload        INTEGER,
                exit_code          INTEGER NOT NULL,
                error              TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_request_logs_collected_at
            ON request_logs (collected_at)
            """
        )


# curl -w format that produces valid JSON so stdout can be parsed directly.
# Values are unquoted numbers; curl substitutes them in place of %{varname}.
_CURL_WRITE_FORMAT = (
    "{"
    '"http_status": %{http_code}, '
    '"time_connect": %{time_connect}, '
    '"time_starttransfer": %{time_starttransfer}, '
    '"time_total": %{time_total}, '
    '"size_download": %{size_download}, '
    '"size_upload": %{size_upload}'
    "}"
)


def _collect_request_metrics(url: str, resolver_ip: str) -> dict:
    """
    Run curl against ``url`` using ``resolver_ip`` for DNS resolution and
    return the timing and size metrics reported by curl.

    The ``--resolve`` flag tells curl to connect to ``resolver_ip`` instead of
    performing a real DNS lookup, while still sending the correct ``Host``
    header and validating TLS against the original hostname.

    :param url:         The URL to probe (e.g. ``https://example.com/path``).
    :param resolver_ip: The IP address curl should connect to.
    :return: Dict with keys ``http_status``, ``time_connect``,
             ``time_starttransfer``, ``time_total``, ``size_download``,
             ``size_upload``, ``exit_code``, ``error``.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    resolve_value = f"{hostname}:{port}:{resolver_ip}"

    result = subprocess.run(
        [
            "curl",
            "-L",
            "--insecure",
            "--silent",
            "--show-error",
            "--resolve",
            resolve_value,
            "-w",
            _CURL_WRITE_FORMAT,
            "-o",
            "/dev/null",
            url,
        ],
        capture_output=True,
        text=True,
    )

    metrics: dict = {
        "exit_code": result.returncode,
        "error": result.stderr.strip() or None,
        "http_status": None,
        "time_connect": None,
        "time_starttransfer": None,
        "time_total": None,
        "size_download": None,
        "size_upload": None,
    }

    if result.stdout:
        try:
            data = json.loads(result.stdout)
            metrics["http_status"] = int(data["http_status"]) or None
            metrics["time_connect"] = float(data["time_connect"])
            metrics["time_starttransfer"] = float(data["time_starttransfer"])
            metrics["time_total"] = float(data["time_total"])
            metrics["size_download"] = int(data["size_download"])
            metrics["size_upload"] = int(data["size_upload"])
        except (json.JSONDecodeError, KeyError, ValueError):
            logger.warning("Could not parse curl -w output: %r", result.stdout)

    return metrics


def collect_and_store_request_log() -> None:
    """
    Read the target URL and resolver IP from environment variables, probe the
    URL via curl using the given resolver, and persist the timing metrics to
    SQLite.  Rows older than RETENTION_DAYS are pruned after each insert.

    Required env vars:
        MONITOR_URL          — URL to probe (e.g. ``https://example.com``)
        MONITOR_RESOLVER_IP  — IP address to use in place of DNS resolution
    """
    url = get_flask_env("MONITOR_URL", error=True)
    resolver_ip = get_flask_env("MONITOR_RESOLVER_IP", error=True)

    try:
        metrics = _collect_request_metrics(url, resolver_ip)
    except Exception:
        logger.exception("curl invocation failed for %s via %s", url, resolver_ip)
        return

    collected_at = datetime.now(timezone.utc).isoformat()

    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO request_logs (
                collected_at, url, resolver_ip,
                http_status, time_connect, time_starttransfer, time_total,
                size_download, size_upload, exit_code, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                collected_at,
                url,
                resolver_ip,
                metrics["http_status"],
                metrics["time_connect"],
                metrics["time_starttransfer"],
                metrics["time_total"],
                metrics["size_download"],
                metrics["size_upload"],
                metrics["exit_code"],
                metrics["error"],
            ),
        )
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        ).isoformat()
        deleted = conn.execute(
            "DELETE FROM request_logs WHERE collected_at < ?", (cutoff,)
        ).rowcount

    logger.info(
        "Request log stored at %s for %s via %s — "
        "exit=%d status=%s total=%.3fs (%d old row(s) pruned)",
        collected_at,
        url,
        resolver_ip,
        metrics["exit_code"],
        metrics["http_status"],
        metrics["time_total"] or 0.0,
        deleted,
    )


def get_request_logs_since(seconds: int = 3600) -> list[dict]:
    """
    Return all request log rows collected within the last ``seconds`` seconds,
    in ascending chronological order.

    :param seconds: How far back to look (default: 3600).
    :return: List of row dicts, oldest first.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT collected_at, url, resolver_ip,
                   http_status, time_connect, time_starttransfer, time_total,
                   size_download, size_upload, exit_code, error
            FROM request_logs
            WHERE collected_at >= ?
            ORDER BY collected_at ASC
            """,
            (cutoff,),
        ).fetchall()
    return [dict(row) for row in rows]
