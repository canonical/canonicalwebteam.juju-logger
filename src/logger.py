import logging
import os
from pathlib import Path
from typing import List


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if os.getenv("DEBUG_MODE", None):
    LOGS_DIRECTORY = "./logs"
else:
    LOGS_DIRECTORY = "/var/logs/juju-logger"


def save_logs_to_file(logs: str, file_path: str):
    """
    Save logs to a specified file. This file is non-rotating and will
    be truncated if it exceeds 5MB in size.

    :param logs: The log data to save.
    :param file_path: The path to the file where logs should be saved.
    """
    # Ensure the logs directory exists
    Path(LOGS_DIRECTORY).mkdir(parents=True, exist_ok=True)
    with Path(f"{LOGS_DIRECTORY}/{file_path}").open("a") as log_file:
        #  Check file size, truncate if larger than 5MB
        log_file.seek(0, 2)  # Move to end of file
        if log_file.tell() > 5 * 1024 * 1024:
            log_file.truncate(0)  # Truncate file to zero length

        log_file.write(logs + "\n")


def read_logs_from_file(file_path: str) -> List[str]:
    """
    Read logs from a specified file.

    :param file_path: The path to the file from which logs should be read.
    :return: The log data read from the file.
    """
    try:
        with Path(f"{LOGS_DIRECTORY}/{file_path}").open("r") as log_file:
            # Split by newlines into list
            return log_file.read().splitlines()
    except FileNotFoundError:
        return []


def save_juju_status_logs(status):
    """
    Save Juju status logs to a file.

    :param status: The Juju status data to save.
    """
    save_logs_to_file(str(status), "juju_status.log")


def save_juju_debug_logs(debug_info: dict):
    """
    Save Juju debug logs to a file.

    :param debug_info: The Juju debug data to save.
    """
    # Extract fields from json info
    applications = debug_info.get("applications", {})
    timestamp = debug_info.get("controller_timestamp", "")
    if applications:
        for app_name, app_data in applications.items():
            status = app_data.get("status", {}).get("status", "")
            scale = len(app_data.get("units", {}))
            channel = app_data.get("charm_channel", "")
            revision = app_data.get("charm_rev", "")
            public_address = app_data.get("public_address", "")
            exposed = app_data.get("exposed", False)
            message = app_data.get("status", {}).get("info", "")

            log_line = (
                f"{timestamp},{app_name},{status},{scale},"
                f"{channel},{revision},{public_address},{exposed},{message}"
            )
            logger.info(log_line)
            # save_logs_to_file(log_line, "juju_debug.log")


def read_juju_status_logs() -> List[str]:
    """
    Read Juju status logs from a file.

    :return: The Juju status log data.
    """
    return read_logs_from_file("juju_status.log")


def read_juju_debug_logs() -> List[str]:
    """
    Read Juju debug logs from a file.

    :return: The Juju debug log data.
    """
    return read_logs_from_file("juju_debug.log")
