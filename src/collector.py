import asyncio
import base64
import logging
import os
from pathlib import Path
from juju.model import Model
from juju.controller import Controller
from src.logger import save_juju_debug_logs, save_juju_status_logs
from src.utils import get_flask_env


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


AUTHENTICATION_DIR = ".auth"


async def authenticate_juju():
    """Decode and set up Juju credentials from environment variables."""
    # juju needs this file to exist, with at least an empty JSON object
    path = Path.home().joinpath(".go-cookies")
    if not path.exists():
        with open(path, "w") as f:
            f.write("{}")

    Path(AUTHENTICATION_DIR).mkdir(parents=True, exist_ok=True)
    controllers_file = base64.b64decode(get_flask_env("JUJU_CONTROLLERS_BASE64", ""))
    accounts_file = base64.b64decode(get_flask_env("JUJU_ACCOUNTS_BASE64", ""))
    models_file = base64.b64decode(get_flask_env("JUJU_MODELS_BASE64", ""))

    with open(f"{AUTHENTICATION_DIR}/controllers.yaml", "wb") as cf:
        cf.write(controllers_file)
    with open(f"{AUTHENTICATION_DIR}/accounts.yaml", "wb") as af:
        af.write(accounts_file)
    with open(f"{AUTHENTICATION_DIR}/models.yaml", "wb") as mf:
        mf.write(models_file)

    os.environ["JUJU_DATA"] = AUTHENTICATION_DIR

    # Connect to the controller to verify authentication
    controller = Controller()
    await controller.connect()

    logging.info(f"Connected to controller: {controller.controller_name}")


async def collect_data():
    """
    Collect data from the Juju model.
    """
    # Set up credentials
    await authenticate_juju()

    logging.info("Collecting data from the model...")

    # Create a Model instance. We need to get the currently active model name.
    model = Model()
    await model.connect()

    status = await model.get_status()
    debug_log = await model.debug_log()

    #  Log to file
    await save_juju_status_logs(model.name, status)  # type: ignore
    await save_juju_debug_logs(model.name, debug_log)  # type: ignore
