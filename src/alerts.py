import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from src.schemas import Snapshot, UnitSnapshot
from src.snapshots import get_snapshots_since

MATTERMOST_HOST = os.environ.get("MATTERMOST_HOST", "chat.canonical.com")
MATTERMOST_ACCESS_TOKEN = os.environ["MATTERMOST_ACCESS_TOKEN"]

_BASE_URL = f"https://{MATTERMOST_HOST}/api/v4"
_HEADERS = {
    "Authorization": f"Bearer {MATTERMOST_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

logger = logging.getLogger(__name__)

# Workload statuses that indicate a unit is not healthy.
_UNHEALTHY_STATUSES: frozenset[str] = frozenset({"error", "unknown"})

_ALERT_THRESHOLD = 0.70  # >70% non-active snapshots → alert
_WARNING_THRESHOLD = 0.50  # >50% non-active snapshots → warning

# Minimum time between alerts for the same unit to prevent scheduler spam.
_ALERT_COOLDOWN = timedelta(minutes=5)

# Module-level cooldown state: unit_name → last alert datetime (UTC).
_last_alert_sent: dict[str, datetime] = {}


def mattermost(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Make a request to the Mattermost REST API.

    Args:
        method:  HTTP verb — "GET", "POST", "PUT", "DELETE", etc.
        path:    API path, e.g. "/posts" or "/channels/{id}/posts"
        payload: Optional JSON body (for POST/PUT requests)

    Returns:
        Parsed JSON dict.

    Raises:
        requests.HTTPError: on 4xx/5xx responses.
    """
    url = f"{_BASE_URL}/{path.lstrip('/')}"
    response = requests.request(
        method.upper(),
        url,
        headers=_HEADERS,
        json=payload,
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def send_message(channel_id: str, message: str) -> dict[str, Any]:
    """
    Send a message to a Mattermost channel.

    Args:
        channel_id: The ID of the channel to post in.
        message:    The message text to send.

    Returns:
        The created post as a dict.
    """
    return mattermost(
        "POST",
        "/posts",
        payload={
            "channel_id": channel_id,
            "message": message,
        },
    )


def reply_to_post(channel_id: str, post_id: str, message: str) -> dict[str, Any]:
    """

    Send a reply to an existing Mattermost post.

    Args:
        channel_id: The ID of the channel containing the post.
        post_id:    The ID of the post to reply to.
        message:    The message text to send.
    Returns:
        The created reply post as a dict.
    """
    return mattermost(
        "POST",
        "/posts",
        payload={
            "channel_id": channel_id,
            "message": message,
            "root_id": post_id,
        },
    )


def _unit_status_table(unit: UnitSnapshot) -> str:
    """Format a unit's status fields as a markdown table."""
    rows = [
        ("Workload status", f"`{unit.workload_status or 'N/A'}`"),
        ("Workload message", unit.workload_message or "N/A"),
        ("Agent status", f"`{unit.agent_status or 'N/A'}`"),
        ("Agent message", unit.agent_message or "N/A"),
        ("Machine", f"`{unit.machine or 'N/A'}`"),
        ("Address", f"`{unit.public_address or 'N/A'}`"),
    ]
    header = "| Field | Value |"
    divider = "|---|---|"
    body = "\n".join(f"| {field} | {value} |" for field, value in rows)
    return "\n".join([header, divider, body])


def _find_unit(snapshots: list[Snapshot], unit_name: str) -> UnitSnapshot | None:
    """Return the most recent UnitSnapshot for the given unit name."""
    for snapshot in reversed(snapshots):
        for app in snapshot.applications.values():
            if unit_name in app.units:
                return app.units[unit_name]
    return None


def send_environment_alert(channel_id: str) -> None:
    """
    Check unit workload statuses over the last 2 minutes and post a Mattermost
    message if any unit's non-active rate crosses a threshold.

    Levels (based on the fraction of snapshots in the window where
    ``workload_status`` was not ``"active"``):

    * :rotating_light: **alert**   — unit non-active in >70% of snapshots
    * :warning:        **warning** — unit non-active in >50% of snapshots

    A threaded reply is posted for each triggered unit containing its current
    workload/agent status and the most recent debug log excerpt.

    Alerts for a given unit are suppressed for ``_ALERT_COOLDOWN`` after
    firing to prevent the scheduler from spamming the channel.

    :param channel_id: Mattermost channel ID to post into.
    """
    snapshots = get_snapshots_since(minutes=2)
    if not snapshots:
        logger.debug("No snapshots in the last 2 minutes; skipping alert check")
        return

    # Tally how often each unit appeared and how often it was non-active.
    unit_total: dict[str, int] = {}
    unit_unhealthy: dict[str, int] = {}

    for snapshot in snapshots:
        for app in snapshot.applications.values():
            for unit_name, unit in app.units.items():
                unit_total[unit_name] = unit_total.get(unit_name, 0) + 1
                if unit.workload_status in _UNHEALTHY_STATUSES:
                    unit_unhealthy[unit_name] = unit_unhealthy.get(unit_name, 0) + 1

    now = datetime.now(timezone.utc)

    # Determine which units cross a threshold and are outside the cooldown.
    # Structure: unit_name → (level, non-active rate)
    triggered: dict[str, tuple[str, float]] = {}
    for unit_name, total in unit_total.items():
        rate = unit_unhealthy.get(unit_name, 0) / total
        if rate > _ALERT_THRESHOLD:
            level = "alert"
        elif rate > _WARNING_THRESHOLD:
            level = "warning"
        else:
            continue

        last_sent = _last_alert_sent.get(unit_name)
        if last_sent and (now - last_sent) < _ALERT_COOLDOWN:
            continue

        triggered[unit_name] = (level, rate)

    if not triggered:
        return

    # Build the top-level summary message.
    alert_units = [(u, r) for u, (lv, r) in triggered.items() if lv == "alert"]
    warning_units = [(u, r) for u, (lv, r) in triggered.items() if lv == "warning"]

    lines: list[str] = []
    if alert_units:
        lines.append(
            f":rotating_light: **Environment alert** — "
            f"{len(alert_units)} unit(s) non-active in >70% of snapshots over the last 2 minutes:"
        )
        for unit_name, rate in alert_units:
            lines.append(f"- `{unit_name}`: {rate:.0%}")
    if warning_units:
        lines.append(
            f":warning: **Environment warning** — "
            f"{len(warning_units)} unit(s) non-active in >50% of snapshots over the last 2 minutes:"
        )
        for unit_name, rate in warning_units:
            lines.append(f"- `{unit_name}`: {rate:.0%}")

    try:
        post = send_message(channel_id, "\n".join(lines))
        post_id = post["id"]
    except requests.HTTPError:
        logger.exception("Failed to post environment alert to Mattermost")
        return

    # Record cooldown timestamps before sending replies so a reply failure
    # does not leave units in an un-throttled state.
    for unit_name in triggered:
        _last_alert_sent[unit_name] = now

    # Post a threaded reply for each triggered unit with status details
    # and its debug log excerpt.
    for unit_name, (level, rate) in triggered.items():
        unit = _find_unit(snapshots, unit_name)
        if unit is None:
            continue

        debug_log = (
            snapshots[-1].unit_debug_logs.get(unit_name) or "(no debug log available)"
        )
        # Mattermost's message size limit is ~16 000 chars; take the tail of
        # the log so the most recent lines are always included.
        debug_excerpt = debug_log[-4000:] if len(debug_log) > 4000 else debug_log

        emoji = ":rotating_light:" if level == "alert" else ":warning:"
        reply_lines = [
            f"{emoji} **{unit_name}** — {rate:.0%} non-active over the last 2 minutes",
            "",
            "**Status**",
            _unit_status_table(unit),
            "",
            "**Debug log (most recent excerpt)**",
            f"```\n{debug_excerpt}\n```",
        ]

        try:
            reply_to_post(channel_id, post_id, "\n".join(reply_lines))
        except requests.HTTPError:
            logger.exception("Failed to post unit detail reply for %s", unit_name)

    logger.info(
        "Environment alert posted to channel %s for %d unit(s): %s",
        channel_id,
        len(triggered),
        list(triggered),
    )
