"""
See:
https://pytest.org/en/7.1.x/example/simple.html#control-skipping-of-tests-according-to-command-line-option
"""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        # --run-integration given in cli: do not skip integration tests
        skip_unit = pytest.mark.skip(reason="not an integration test")
        for item in items:
            if "integration" not in item.keywords:
                item.add_marker(skip_unit)
    else:
        skip_integration = pytest.mark.skip(
            reason="need --run-integration option to run"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
