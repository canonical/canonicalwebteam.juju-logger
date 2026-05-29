import json
import logging
import re
import subprocess

from src.schemas import BinaryLogEntry, BinaryModelStatus

_LOG_RE = re.compile(
    r"^(\S+):\s+(\d{2}:\d{2}:\d{2})\s+(DEBUG|TRACE|INFO|WARNING|ERROR|CRITICAL)\s+(\S+)\s+(.*)"
)


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


def get_juju_status() -> BinaryModelStatus:
    """Return juju status as a BinaryModelStatus parsed from CLI JSON."""
    raw = json.loads(_run_juju("status", "--relations", "--format=json"))
    return BinaryModelStatus.model_validate(raw)


def get_juju_debug_log(limit: int = 100) -> list[BinaryLogEntry]:
    """
    Return recent juju debug log entries parsed from the plain-text log format.

    Lines that don't match the entry pattern (e.g. traceback continuations)
    are appended to the previous entry's message.

    :param limit: Maximum number of log lines to retrieve.
    """
    output = _run_juju("debug-log", f"--limit={limit}", "--no-tail")
    entries: list[BinaryLogEntry] = []
    for line in output.splitlines():
        m = _LOG_RE.match(line)
        if m:
            agent, time, level, module, message = m.groups()
            entries.append(
                BinaryLogEntry(
                    agent=agent, time=time, level=level, module=module, message=message
                )
            )
        elif entries:
            last = entries[-1]
            entries[-1] = last.model_copy(
                update={"message": last.message + "\n" + line}
            )
        else:
            logging.warning("Skipping unparseable log line before first entry: %r", line)
    return entries
