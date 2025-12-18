import asyncio
import base64
import logging
import os
from pathlib import Path
from juju.model import Model
from juju.controller import Controller
from src.logger import save_juju_status_logs

logging.basicConfig(level=logging.INFO)


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
    controllers_file = base64.b64decode(os.getenv("JUJU_CONTROLLERS_BASE64", ""))
    accounts_file = base64.b64decode(os.getenv("JUJU_ACCOUNTS_BASE64", ""))
    models_file = base64.b64decode(os.getenv("JUJU_MODELS_BASE64", ""))

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


@scheduled_task(300)  # run every 5 minutes
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

    #  Log to file
    save_juju_status_logs(str(status))
    # logging.info(f"Model status: {status}")

    # apps = await model.applications()
    # for app in apps:
    #     units = await app.units()
    #     for unit in units:
    #         status = await unit.status()
    #         logging.info(f"Unit {unit.name} status: {status}")


def start_collection():
    # Run the deploy coroutine in an asyncio event loop
    asyncio.run(collect_data())


xx = {
    "applications": {
        "canonical-com": (
            {
                "base": (
                    {"channel": "22.04/stable", "name": "ubuntu", "unknown_fields": {}}
                ),
                "can_upgrade_to": "",
                "charm": "ch:amd64/canonical-com-11",
                "charm_channel": "latest/beta",
                "charm_profile": "",
                "charm_rev": 11,
                "charm_version": "",
                "endpoint_bindings": {
                    "": "alpha",
                    "grafana-dashboard": "alpha",
                    "ingress": "alpha",
                    "logging": "alpha",
                    "metrics-endpoint": "alpha",
                    "secret-storage": "alpha",
                },
                "err": None,
                "exposed": False,
                "exposed_endpoints": {},
                "int_": 1,
                "life": "",
                "meter_statuses": {},
                "provider_id": "a07abcf4-d6d1-4750-a6c6-e213e410b1ae",
                "public_address": "10.96.131.252",
                "relations": {
                    "ingress": ["nginx-ingress-integrator"],
                    "secret-storage": ["canonical-com"],
                },
                "status": (
                    {
                        "data": {},
                        "err": None,
                        "info": "",
                        "kind": "",
                        "life": "",
                        "since": "2025-12-10T05:36:28.86714856Z",
                        "status": "active",
                        "version": "",
                        "unknown_fields": {},
                    }
                ),
                "subordinate_to": [],
                "units": {
                    "canonical-com/0": (
                        {
                            "address": "10.244.0.9",
                            "agent_status": (
                                {
                                    "data": {},
                                    "err": None,
                                    "info": "",
                                    "kind": "",
                                    "life": "",
                                    "since": "2025-12-10T05:36:29.317020716Z",
                                    "status": "idle",
                                    "version": "3.6.12",
                                    "unknown_fields": {},
                                }
                            ),
                            "charm": "",
                            "leader": True,
                            "machine": "",
                            "opened_ports": [],
                            "provider_id": "canonical-com-0",
                            "public_address": "",
                            "subordinates": {},
                            "workload_status": (
                                {
                                    "data": {},
                                    "err": None,
                                    "info": "",
                                    "kind": "",
                                    "life": "",
                                    "since": "2025-12-10T05:36:28.846694837Z",
                                    "status": "active",
                                    "version": "",
                                    "unknown_fields": {},
                                }
                            ),
                            "workload_version": "",
                            "unknown_fields": {},
                        }
                    )
                },
                "workload_version": "",
                "unknown_fields": {},
            }
        ),
        "nginx-ingress-integrator": (
            {
                "base": (
                    {"channel": "22.04/stable", "name": "ubuntu", "unknown_fields": {}}
                ),
                "can_upgrade_to": "",
                "charm": "ch:amd64/nginx-ingress-integrator-203",
                "charm_channel": "latest/stable",
                "charm_profile": "",
                "charm_rev": 203,
                "charm_version": "",
                "endpoint_bindings": {
                    "": "alpha",
                    "certificates": "alpha",
                    "ingress": "alpha",
                    "nginx-peers": "alpha",
                    "nginx-route": "alpha",
                },
                "err": None,
                "exposed": False,
                "exposed_endpoints": {},
                "int_": 1,
                "life": "",
                "meter_statuses": {},
                "provider_id": "9159160f-8a1b-47de-a1ea-f24ef2d86653",
                "public_address": "10.96.84.181",
                "relations": {
                    "ingress": ["canonical-com"],
                    "nginx-peers": ["nginx-ingress-integrator"],
                },
                "status": (
                    {
                        "data": {},
                        "err": None,
                        "info": "",
                        "kind": "",
                        "life": "",
                        "since": "2025-12-10T05:38:05.836994035Z",
                        "status": "active",
                        "version": "",
                        "unknown_fields": {},
                    }
                ),
                "subordinate_to": [],
                "units": {
                    "nginx-ingress-integrator/0": (
                        {
                            "address": "10.244.0.8",
                            "agent_status": (
                                {
                                    "data": {},
                                    "err": None,
                                    "info": "",
                                    "kind": "",
                                    "life": "",
                                    "since": "2025-12-10T05:38:17.767499898Z",
                                    "status": "idle",
                                    "version": "3.6.12",
                                    "unknown_fields": {},
                                }
                            ),
                            "charm": "",
                            "leader": True,
                            "machine": "",
                            "opened_ports": [],
                            "provider_id": "nginx-ingress-integrator-0",
                            "public_address": "",
                            "subordinates": {},
                            "workload_status": (
                                {
                                    "data": {},
                                    "err": None,
                                    "info": "",
                                    "kind": "",
                                    "life": "",
                                    "since": "2025-12-10T05:38:05.836994035Z",
                                    "status": "active",
                                    "version": "",
                                    "unknown_fields": {},
                                }
                            ),
                            "workload_version": "24.2.0",
                            "unknown_fields": {},
                        }
                    )
                },
                "workload_version": "24.2.0",
                "unknown_fields": {},
            }
        ),
    },
    "branches": {},
    "controller_timestamp": "2025-12-10T07:02:50.57064576Z",
    "filesystems": [],
    "machines": {},
    "model": (
        {
            "available_version": "",
            "cloud_tag": "cloud-kind-kind",
            "meter_status": ({"color": "", "message": "", "unknown_fields": {}}),
            "model_status": (
                {
                    "data": {},
                    "err": None,
                    "info": "",
                    "kind": "",
                    "life": "",
                    "since": "2025-12-08T07:22:07.829755394Z",
                    "status": "available",
                    "version": "",
                    "unknown_fields": {},
                }
            ),
            "name": "local-model",
            "region": None,
            "sla": "unsupported",
            "type_": "caas",
            "version": "3.6.12",
            "unknown_fields": {},
        }
    ),
    "offers": {},
    "relations": [
        (
            {
                "endpoints": [
                    (
                        {
                            "application": "canonical-com",
                            "name": "secret-storage",
                            "role": "peer",
                            "subordinate": False,
                            "unknown_fields": {},
                        }
                    )
                ],
                "id_": 0,
                "interface": "secret-storage",
                "key": "canonical-com:secret-storage",
                "scope": "global",
                "status": (
                    {
                        "data": {},
                        "err": None,
                        "info": "",
                        "kind": "",
                        "life": "",
                        "since": "2025-12-08T07:24:01.601345398Z",
                        "status": "joined",
                        "version": "",
                        "unknown_fields": {},
                    }
                ),
                "unknown_fields": {},
            }
        ),
        (
            {
                "endpoints": [
                    (
                        {
                            "application": "canonical-com",
                            "name": "ingress",
                            "role": "requirer",
                            "subordinate": False,
                            "unknown_fields": {},
                        }
                    ),
                    (
                        {
                            "application": "nginx-ingress-integrator",
                            "name": "ingress",
                            "role": "provider",
                            "subordinate": False,
                            "unknown_fields": {},
                        }
                    ),
                ],
                "id_": 2,
                "interface": "ingress",
                "key": "canonical-com:ingress nginx-ingress-integrator:ingress",
                "scope": "global",
                "status": (
                    {
                        "data": {},
                        "err": None,
                        "info": "",
                        "kind": "",
                        "life": "",
                        "since": "2025-12-08T07:25:09.156982201Z",
                        "status": "joined",
                        "version": "",
                        "unknown_fields": {},
                    }
                ),
                "unknown_fields": {},
            }
        ),
        (
            {
                "endpoints": [
                    (
                        {
                            "application": "nginx-ingress-integrator",
                            "name": "nginx-peers",
                            "role": "peer",
                            "subordinate": False,
                            "unknown_fields": {},
                        }
                    )
                ],
                "id_": 1,
                "interface": "nginx-instance",
                "key": "nginx-ingress-integrator:nginx-peers",
                "scope": "global",
                "status": (
                    {
                        "data": {},
                        "err": None,
                        "info": "",
                        "kind": "",
                        "life": "",
                        "since": "2025-12-08T07:24:12.772112015Z",
                        "status": "joined",
                        "version": "",
                        "unknown_fields": {},
                    }
                ),
                "unknown_fields": {},
            }
        ),
    ],
    "remote_applications": {},
    "storage": [],
    "volumes": [],
    "unknown_fields": {},
}
