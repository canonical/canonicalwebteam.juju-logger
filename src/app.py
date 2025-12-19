from src import create_app
from src.logger import read_juju_debug_logs, read_juju_status_logs


app = create_app()


@app.route("/environment/status")
def juju_environment_status():
    logs = read_juju_status_logs()
    return "\n".join(logs)


@app.route("/environment/debug")
def juju_environment_debug():
    logs = read_juju_debug_logs()
    return "\n".join(logs)


@app.route("/environment/status-log")
def juju_environment_status_log():
    return "Juju Environment status log for all units"


@app.route("/environment/unit-messages")
def juju_environment_unit_messages():
    return "Juju Environment unit messages"
