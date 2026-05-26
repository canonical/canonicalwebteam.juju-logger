from __future__ import annotations

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str | None = None
    cloud: str | None = None
    region: str | None = None
    version: str | None = None
    type: str | None = None
    sla: str | None = None
    status: str | None = None


class UnitSnapshot(BaseModel):
    machine: str | None = None
    public_address: str | None = None
    agent_status: str | None = None
    agent_message: str | None = None
    workload_status: str | None = None
    workload_message: str | None = None
    workload_version: str | None = None
    leader: bool | None = None
    ports: list[str] = Field(default_factory=list)


class ApplicationSnapshot(BaseModel):
    status: str | None = None
    message: str | None = None
    since: str | None = None
    charm: str | None = None
    charm_channel: str | None = None
    charm_rev: int | None = None
    workload_version: str | None = None
    exposed: bool | None = None
    life: str | None = None
    units: dict[str, UnitSnapshot] = Field(default_factory=dict)


class Snapshot(BaseModel):
    model: ModelInfo
    applications: dict[str, ApplicationSnapshot] = Field(default_factory=dict)
    # Raw string output from `juju debug-log`, one entry per line.
    debug_logs: str = ""
    # Per-unit debug log output keyed by unit name (e.g. "ubuntu/0").
    unit_debug_logs: dict[str, str] = Field(default_factory=dict)
