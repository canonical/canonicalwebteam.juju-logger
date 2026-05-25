import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from src.collector import collect_data, raw_collect
from src.logger import read_juju_debug_logs, read_juju_status_logs
from src.utils import get_flask_env

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Set up the scheduler
scheduler = AsyncIOScheduler()
# scheduler.add_job(collect_data, "interval", seconds=5)
scheduler.start()


_REQUIRED_ENV_VARS = [
    "JUJU_ACCOUNTS_BASE64",
    "JUJU_CONTROLLERS_BASE64",
    "JUJU_MODEL_NAME",
]


# Ensure the scheduler shuts down properly on application exit.
@asynccontextmanager
async def lifespan(app: FastAPI):
    missing = [v for v in _REQUIRED_ENV_VARS if not get_flask_env(v)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/_status/check", response_class=HTMLResponse)
async def status():
    return "OK"


@app.get("/environment/debug")
async def juju_environment_debug():
    return read_juju_debug_logs()


@app.get("/environment/status")
async def juju_environment_status():
    return read_juju_status_logs()


@app.route("/environment/status-log")
async def juju_environment_status_log():
    return "Juju Environment status log for all units"


@app.route("/environment/unit-messages")
async def juju_environment_unit_messages():
    return "Juju Environment unit messages"


@app.get("/environment/raw")
async def juju_environment_raw():
    data = await raw_collect()
    return _serialize_raw(data)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return FileResponse(Path(__file__).parent / "templates" / "dashboard.html")


def _serialize_raw(data: dict) -> dict:
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
                "since": app.status.since if app.status else None,
                "charm": app.charm,
                "charm_channel": app.charm_channel,
                "charm_rev": app.charm_rev,
                "workload_version": app.workload_version,
                "exposed": app.exposed,
                "life": app.life,
                "units": {
                    unit_name: {
                        "machine": unit.machine,
                        "public_address": unit.public_address,
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
