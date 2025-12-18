from flask import Flask

from src.collector import start_collection


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    start_collection()

    @app.route("/_status/check")
    def status():
        return "OK"

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
