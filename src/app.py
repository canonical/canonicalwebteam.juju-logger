import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from src.monitor import (
    _init_db as _init_monitor_db,
    collect_and_store_request_log,
    get_request_logs_since,
)
from src.schemas import ApplicationSnapshot, Snapshot
from src.snapshots import (
    _init_db,
    get_latest_debug_logs,
    get_latest_snapshot,
    get_latest_status,
    store_snapshot,
)
from src.utils import get_flask_env

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Set up the scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(store_snapshot, "interval", seconds=5)
scheduler.add_job(collect_and_store_request_log, "interval", seconds=5)
scheduler.start()


_REQUIRED_ENV_VARS = [
    "JUJU_ACCOUNTS_BASE64",
    "JUJU_CONTROLLERS_BASE64",
    "JUJU_MODEL_NAME",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    missing = [v for v in _REQUIRED_ENV_VARS if not get_flask_env(v)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )
    _init_db()
    _init_monitor_db()
    yield
    # Ensure the scheduler shuts down properly on application exit.
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/_status/check", response_class=HTMLResponse)
async def status():
    return "OK"


@app.get("/environment/debug", response_model=list[str])
async def juju_environment_debug():
    return get_latest_debug_logs()


@app.get("/environment/status", response_model=dict[str, ApplicationSnapshot])
async def juju_environment_status():
    return get_latest_status()


@app.route("/environment/status-log")
async def juju_environment_status_log():
    return "Juju Environment status log for all units"


@app.route("/environment/unit-messages")
async def juju_environment_unit_messages():
    return "Juju Environment unit messages"


@app.get("/environment/raw", response_model=Snapshot | None)
async def juju_environment_raw():
    return get_latest_snapshot()


@app.get("/environment/request-logs")
async def request_logs(seconds: int = 3600):
    return get_request_logs_since(seconds)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return FileResponse(Path(__file__).parent / "templates" / "dashboard.html")


@app.get("/stats", response_class=HTMLResponse)
async def stats():
    monitor_url = get_flask_env("MONITOR_URL") or ""
    html = (Path(__file__).parent / "templates" / "stats.html").read_text()
    html = html.replace("__MONITOR_URL__", monitor_url)
    return HTMLResponse(html)
