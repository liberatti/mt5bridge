import os
import pytest


def pytest_addoption(parser):
    """Register custom CLI options for end-to-end API tests."""
    parser.addoption(
        "--api-url",
        action="store",
        default=os.environ.get("API_URL", "http://localhost:5000"),
        help="Base API URL for e2e tests (default: http://localhost:5000)",
    )
    parser.addoption(
        "--symbol",
        action="store",
        default=os.environ.get("TEST_SYMBOL", os.environ.get("MT5_STARTUP_SYMBOL", "EURUSD")),
        help="Trading symbol for tests (default: EURUSD)",
    )
    parser.addoption(
        "--volume",
        action="store",
        type=float,
        default=0.01,
        help="Lot volume for test trades (default: 0.01)",
    )
    parser.addoption(
        "--api-key",
        action="store",
        default=os.environ.get("API_KEY", ""),
        help="API key for x-api-key authentication",
    )
    parser.addoption(
        "--no-close",
        action="store_true",
        default=False,
        help="Do not close opened test positions",
    )


@pytest.fixture(scope="session")
def api_url(request) -> str:
    return str(request.config.getoption("--api-url")).rstrip("/")


@pytest.fixture(scope="session")
def test_symbol(request) -> str:
    return str(request.config.getoption("--symbol"))


@pytest.fixture(scope="session")
def test_volume(request) -> float:
    return float(request.config.getoption("--volume"))


@pytest.fixture(scope="session")
def api_key(request) -> str:
    return str(request.config.getoption("--api-key"))


@pytest.fixture(scope="session")
def close_order(request) -> bool:
    return not bool(request.config.getoption("--no-close"))
