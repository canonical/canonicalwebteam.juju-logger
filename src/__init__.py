from flask import Flask

from src.collector import collect_data


async def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    await collect_data()

    @app.route("/_status/check")
    def status():
        return "OK"

    return app
