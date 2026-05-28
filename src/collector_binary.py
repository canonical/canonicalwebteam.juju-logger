import asyncio
import json
import logging
import subprocess

from src.logger import save_juju_debug_logs, save_juju_status_logs


def scheduled_task(interval: int):
    """
    Run a scheduled async task at a given interval.

    :param interval: Interval in seconds between task executions.
    """

    def scheduler(func):
        async def wrapper(*args, **kwargs):
            while True:
                asyncio.ensure_future(func(*args, **kwargs))
                await asyncio.sleep(interval)

        return wrapper

    return scheduler


class AttrDict(dict):
    """Dict subclass that also supports attribute-style access."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)


def _run_juju(*args) -> str:
    """Run a juju CLI command and return stdout."""
    result = subprocess.run(
        ["juju", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def get_model_name() -> str:
    """Return the currently active juju model name."""
    # `juju switch` outputs "controller:model-name" or just "model-name"
    return _run_juju("switch").strip().split(":")[-1]


def get_juju_status() -> AttrDict:
    """
    Return juju status as an AttrDict matching the structure expected by
    save_juju_status_logs, normalising from CLI JSON field names to the
    attribute names used by python-libjuju.
    """
    raw = json.loads(_run_juju("status", "--format=json"))
    normalised_apps = {}
    for app_name, app_data in raw.get("applications", {}).items():
        status = app_data.get("status", {})
        normalised_apps[app_name] = AttrDict(
            {
                "status": AttrDict(
                    {
                        "since": status.get("since", "N/A"),
                        # CLI uses "current"; libjuju exposes it as "status"
                        "status": status.get("current", "N/A"),
                        # CLI uses "message"; libjuju exposes it as "info"
                        "info": status.get("message", ""),
                    }
                ),
                "units": app_data.get("units", {}),
                # CLI uses hyphenated keys; libjuju uses underscored attributes
                "charm_channel": app_data.get("charm-channel", "N/A"),
                "charm_rev": app_data.get("charm-rev", "N/A"),
                "public_address": app_data.get("public-address", "N/A"),
                "exposed": app_data.get("exposed", False),
            }
        )
    return AttrDict({"applications": normalised_apps})


def get_juju_debug_log(limit: int = 100) -> list:
    """
    Return recent juju debug log entries as a list of dicts, normalising the
    "timestamp" key to "time" to match what save_juju_debug_logs expects.

    :param limit: Maximum number of log lines to retrieve.
    """
    output = _run_juju(
        "debug-log", "--format=json", f"--limit={limit}", "--no-tail"
    )
    entries = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            # Normalise timestamp key used by the CLI to what logger.py expects
            if "timestamp" in entry and "time" not in entry:
                entry["time"] = entry["timestamp"]
            entries.append(entry)
        except json.JSONDecodeError:
            logging.warning(f"Failed to parse debug-log line: {line!r}")
    return entries


async def collect_data():
    """
    Collect data from the Juju model using the local juju CLI binary.
    No credential setup is required; the binary uses the already-configured
    juju client on the host OS.
    """
    logging.info("Collecting data from the model...")

    model_name = get_model_name()
    status = get_juju_status()
    debug_log = get_juju_debug_log()

    await save_juju_status_logs(model_name, status)
    await save_juju_debug_logs(model_name, debug_log)
