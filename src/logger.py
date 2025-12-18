from pathlib import Path

LOGS_DIRECTORY = "./logs"


def save_logs_to_file(logs: str, file_path: str):
    """
    Save logs to a specified file.

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


def save_juju_status_logs(status: str):
    """
    Save Juju status logs to a file.

    :param status: The Juju status data to save.
    """
    save_logs_to_file(status, "juju_status.log")
