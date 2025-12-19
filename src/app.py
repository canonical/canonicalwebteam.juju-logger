import logging
from contextlib import asynccontextmanager

from fastapi.responses import HTMLResponse
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.collector import collect_data
from src.logger import read_juju_debug_logs, read_juju_status_logs

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Set up the scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(collect_data, "interval", seconds=5)
scheduler.start()


# Ensure the scheduler shuts down properly on application exit.
@asynccontextmanager
async def lifespan(app: FastAPI):
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
