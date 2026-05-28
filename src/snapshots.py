import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator

from src.collector import raw_collect
from src.schemas import ApplicationSnapshot, Snapshot

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
    """Create the snapshots table and index if they do not already exist."""
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at TEXT    NOT NULL,
                model_name   TEXT    NOT NULL,
                data         TEXT    NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_snapshots_collected_at
            ON snapshots (collected_at)
            """
        )


def _serialize_raw(data: dict) -> dict:
    """
    Convert a raw_collect() result into a plain, JSON-serialisable dict.

    :param data: Dict as returned by raw_collect().
    :return: JSON-serialisable representation of the snapshot.
    """
    model = data["model"]
    return {
        "model": {
            "name": model.name,
            "cloud": model.cloud_tag,
            "region": model.region,
            "version": model.version,
            "type": model.type_,
            "sla": model.sla,
            "status": model.model_status.status if model.model_status else None,
        },
        "applications": {
            app_name: {
                "status": app.status.status if app.status else None,
                "message": app.status.info if app.status else None,
                "since": str(app.status.since)
                if app.status and app.status.since
                else None,
                "charm": app.charm,
                "charm_channel": app.charm_channel,
                "charm_rev": app.charm_rev,
                "workload_version": app.workload_version,
                "exposed": app.exposed,
                "life": app.life,
                "units": {
                    unit_name: {
                        "machine": unit.machine,
                        "public_address": unit.address or unit.public_address,
                        "agent_status": unit.agent_status.status
                        if unit.agent_status
                        else None,
                        "agent_message": unit.agent_status.info
                        if unit.agent_status
                        else None,
                        "workload_status": unit.workload_status.status
                        if unit.workload_status
                        else None,
                        "workload_message": unit.workload_status.info
                        if unit.workload_status
                        else None,
                        "workload_version": unit.workload_version,
                        "leader": unit.leader,
                        "ports": list(unit.opened_ports or []),
                    }
                    for unit_name, unit in (app.units or {}).items()
                },
            }
            for app_name, app in data["applications"].items()
        },
        "debug_logs": data["debug_logs"],
        "unit_debug_logs": data["unit_debug_logs"],
    }


async def store_snapshot() -> None:
    """
    Save a snapshot of the environment status to SQLite. Snapshots are
    retained for RETENTION_DAYS.
    """
    try:
        data = await raw_collect()
    except Exception:
        logger.exception("Failed to collect Juju data; snapshot skipped")
        return

    serialized = _serialize_raw(data)
    collected_at = datetime.now(timezone.utc).isoformat()
    model_name = serialized["model"].get("name") or ""

    with _conn() as conn:
        conn.execute(
            "INSERT INTO snapshots (collected_at, model_name, data) VALUES (?, ?, ?)",
            (collected_at, model_name, json.dumps(serialized, default=str)),
        )
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        ).isoformat()
        # Delete old snapshots and get the count of deleted rows.
        deleted = conn.execute(
            "DELETE FROM snapshots WHERE collected_at < ?", (cutoff,)
        ).rowcount

    logger.info(
        "Snapshot stored at %s for model '%s' (%d old row(s) pruned)",
        collected_at,
        model_name,
        deleted,
    )


def get_latest_snapshot() -> Snapshot | None:
    """
    Return the most recently stored snapshot, or None if the database is empty.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT data FROM snapshots ORDER BY collected_at DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    return Snapshot.model_validate(json.loads(row["data"]))


def get_latest_debug_logs() -> list[str]:
    """
    Return the debug log lines from the most recent snapshot.

    :return: List of log lines, or an empty list if no snapshot exists yet.
    """
    snapshot = get_latest_snapshot()
    if not snapshot:
        return []
    return snapshot.debug_logs.splitlines()


def get_latest_status() -> dict[str, ApplicationSnapshot]:
    """
    Return the applications status dict from the most recent snapshot.

    :return: Dict keyed by application name, or an empty dict if no snapshot
             exists yet.
    """
    snapshot = get_latest_snapshot()
    if not snapshot:
        return {}
    return snapshot.applications


def get_snapshots_since(minutes: int = 2) -> list[Snapshot]:
    """
    Return all snapshots collected within the last `minutes` minutes, in
    ascending chronological order.

    :param minutes: How far back to look.
    :return: List of Snapshot objects, oldest first.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT data FROM snapshots
            WHERE collected_at >= ?
            ORDER BY collected_at ASC
            """,
            (cutoff,),
        ).fetchall()
    return [Snapshot.model_validate(json.loads(row["data"])) for row in rows]
