from fluid_rower_monitor.api.dependencies import noop_auth_dependency


def test_noop_auth_dependency_returns_true():
    assert noop_auth_dependency() is True
