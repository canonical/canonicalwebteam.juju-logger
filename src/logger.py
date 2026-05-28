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


async def save_logs_to_file(logs: str, file_path: str):
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


async def save_juju_debug_logs(model_name, debug_log):
    """
    Save Juju debug logs to a file.

    :param model_name: The name of the Juju model.
    :param debug_log: The Juju debug log data to save.
    """

    logging.info(f"Saving Juju debug logs for model: {debug_log}")

    for entry in debug_log:
        timestamp = entry.get("time", "N/A")
        level = entry.get("level", "N/A")
        message = entry.get("message", "N/A")

        log_line = f"{timestamp}; juju_environment:{model_name}; level:{level}; message:{message}"
        await save_logs_to_file(log_line, "juju_debug.log")
    await save_logs_to_file(str(debug_log), "juju_debug.log")


async def save_juju_status_logs(model_name, application_status):
    """
    Save Juju status logs to a file.

    :param model_name: The name of the Juju model.
    :param application_status: The Juju application status data to save.
    """
    # Extract fields from json info
    applications = application_status.get("applications", {})
    if applications:
        for app_name, app_data in applications.items():
            timestamp = app_data.status.since
            status = app_data.status.status
            scale = len(app_data.units)
            channel = app_data.charm_channel
            revision = app_data.charm_rev
            public_address = app_data.public_address
            exposed = app_data.get("exposed", False)
            message = app_data.status.info or "N/A"

            log_line = (
                f"{timestamp}; juju_environment:{model_name} app:{app_name}; status:{status}; scale:{scale}; "
                f"channel:{channel}; revision:{revision}; public_address:{public_address}; exposed:{exposed}; message:{message}"
            )
            await save_logs_to_file(log_line, "juju_status.log")


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
