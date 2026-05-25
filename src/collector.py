import asyncio
import base64
import io
import logging
import os
from pathlib import Path

from juju.client.connector import Connector
from juju.controller import Controller
from juju.model import Model

from src.logger import save_juju_debug_logs, save_juju_status_logs
from src.utils import get_flask_env

# juju library bug: Connector.connect() pops 'account' from kwargs on normal
# connections but forgets to do so on the debug_log_conn path, causing
# Connection.connect() to receive an unexpected keyword argument.
_original_connector_connect = Connector.connect


async def _patched_connector_connect(self, **kwargs):
    if "debug_log_conn" in kwargs:
        kwargs.pop("account", None)
    return await _original_connector_connect(self, **kwargs)


Connector.connect = _patched_connector_connect  # type: ignore


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


async def authenticate_juju_home():
    """Set up Juju credentials as files and point JUJU_DATA at them."""
    path = Path.home().joinpath(".go-cookies")
    if not path.exists():
        with open(path, "w") as f:
            f.write("{}")

    Path(AUTHENTICATION_DIR).expanduser().mkdir(parents=True, exist_ok=True)

    controllers_file = base64.b64decode(get_flask_env("JUJU_CONTROLLERS_BASE64", ""))
    with open(f"{AUTHENTICATION_DIR}/controllers.yaml", "wb") as cf:
        cf.write(controllers_file)

    accounts_file = base64.b64decode(get_flask_env("JUJU_ACCOUNTS_BASE64", ""))
    with open(f"{AUTHENTICATION_DIR}/accounts.yaml", "wb") as af:
        af.write(accounts_file)

    models_file = base64.b64decode(get_flask_env("JUJU_MODELS_BASE64", ""))
    with open(f"{AUTHENTICATION_DIR}/models.yaml", "wb") as mf:
        mf.write(models_file)

    os.environ["JUJU_DATA"] = AUTHENTICATION_DIR


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


async def raw_collect():
    """
    Collect raw Juju data using service account credentials from environment
    variables, connecting directly rather than via shared credential files.

    Gathers model info, application and unit status, general debug logs,
    and per-unit debug logs (equivalent to `juju debug-log --include <unit>`).

    Required env vars: JUJU_ENDPOINT, JUJU_USERNAME, JUJU_PASSWORD,
    JUJU_MODEL_NAME. Optional: JUJU_CACERT.

    :return: Dict with keys 'model', 'applications', 'debug_logs',
             and 'unit_debug_logs'.
    """
    await authenticate_juju_home()
    model_name = get_flask_env("JUJU_MODEL_NAME", error=True)

    controller = Controller()
    await controller.connect()
    try:
        uuids = await controller.model_uuids()
        # Capture connection params while still connected, then strip 'account'.
        # controller.get_model() copies params including 'account', which
        # Connection.connect() rejects when debug_log opens its second connection.
        raw_params = controller.connection().connect_params()
    finally:
        await controller.disconnect()

    if model_name not in uuids:
        raise ValueError(f"Model '{model_name}' not found. Available: {list(uuids)}")

    _ALLOWED_CONNECT_PARAMS = {
        "endpoint",
        "uuid",
        "username",
        "password",
        "cacert",
        "bakery_client",
        "macaroons",
        "max_frame_size",
    }
    connect_params = {
        k: v for k, v in raw_params.items() if k in _ALLOWED_CONNECT_PARAMS
    }
    connect_params["uuid"] = uuids[model_name]

    model = Model()
    await model._connect_direct(**connect_params)
    try:
        status = await model.get_status()

        model_info = status.model

        applications = dict(status.applications or {})
        unit_names = [
            unit_name
            for app_data in applications.values()
            for unit_name in (app_data.units if app_data else {})
        ]

        debug_log_buf = io.StringIO()
        await model.debug_log(target=debug_log_buf, no_tail=True, limit=1000)
        debug_logs = debug_log_buf.getvalue()

        unit_debug_logs = {}
        for unit_name in unit_names:
            unit_buf = io.StringIO()
            await model.debug_log(
                target=unit_buf, no_tail=True, limit=1000, include=[unit_name]
            )
            unit_debug_logs[unit_name] = unit_buf.getvalue()

        return {
            "model": model_info,
            "applications": applications,
            "debug_logs": debug_logs,
            "unit_debug_logs": unit_debug_logs,
        }
    finally:
        await model.disconnect()


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
