from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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


# ---------------------------------------------------------------------------
# Binary collector schemas (juju CLI / juju status --format=json output)
# ---------------------------------------------------------------------------


class BinaryStatus(BaseModel):
    current: str = ""
    message: str = ""
    since: str = ""


class BinaryBase(BaseModel):
    channel: str = ""
    name: str = ""


class BinaryUnit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    address: str | None = None
    juju_status: BinaryStatus | None = Field(None, alias="juju-status")
    leader: bool = False
    provider_id: str | None = Field(None, alias="provider-id")
    workload_status: BinaryStatus | None = Field(None, alias="workload-status")


class BinaryApplication(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    address: str | None = None
    application_status: BinaryStatus | None = Field(None, alias="application-status")
    base: BinaryBase | None = None
    charm: str = ""
    charm_channel: str = Field("", alias="charm-channel")
    charm_name: str = Field("", alias="charm-name")
    charm_origin: str = Field("", alias="charm-origin")
    charm_rev: int = Field(0, alias="charm-rev")
    exposed: bool = False
    scale: int = 0
    units: dict[str, BinaryUnit] = Field(default_factory=dict)


class BinaryModelInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cloud: str = ""
    controller: str = ""
    name: str = ""
    region: str = ""
    sla: str = ""
    type: str = ""
    version: str = ""
    model_status: BinaryStatus | None = Field(None, alias="model-status")


class BinaryModelStatus(BaseModel):
    model: BinaryModelInfo
    applications: dict[str, BinaryApplication] = Field(default_factory=dict)


class BinaryLogEntry(BaseModel):
    agent: str
    time: str
    level: str
    module: str
    message: str
