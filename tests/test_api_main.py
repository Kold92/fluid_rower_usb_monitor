import os

from fastapi import FastAPI

from fluid_rower_monitor.api.main import create_app, run


def test_create_app_has_routes():
    app = create_app(mode="dev")
    assert isinstance(app, FastAPI)
    paths = {route.path for route in app.router.routes}
    assert "/sessions/" in paths
    assert "/config/" in paths
    assert "/ws/live" in paths


def test_run_sets_mode_and_calls_uvicorn(monkeypatch):
    called = {}

    def fake_run(app, host, port, reload):
        called["app"] = app
        called["host"] = host
        called["port"] = port
        called["reload"] = reload

    monkeypatch.setattr("uvicorn.run", fake_run)

    run(host="0.0.0.0", port=1234, dev=True)

    assert os.environ["FRM_API_MODE"] == "dev"
    assert called["host"] == "0.0.0.0"
    assert called["port"] == 1234
    assert called["reload"] is False
