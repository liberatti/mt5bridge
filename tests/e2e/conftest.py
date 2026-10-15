import requests
import pytest


class MT5ApiClient:
    """Helper client for communicating with the running MetaTrader 5 REST API."""

    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if api_key:
            headers["x-api-key"] = api_key
        self.session.headers.update(headers)

    def request(self, method: str, endpoint: str, data: dict = None, params: dict = None, timeout: float = 15.0):
        url = f"{self.base_url}{endpoint}"
        resp = self.session.request(method=method, url=url, json=data, params=params, timeout=timeout)
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text}

        if not resp.ok:
            raise requests.HTTPError(f"{method} {endpoint} -> HTTP {resp.status_code}: {body}", response=resp)

        return body

    def get(self, endpoint: str, params: dict = None):
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: dict = None, params: dict = None):
        return self.request("POST", endpoint, data=data, params=params)

    def delete(self, endpoint: str, params: dict = None):
        return self.request("DELETE", endpoint, params=params)

    @staticmethod
    def get_data(res, key: str = None):
        """Safely extracts inner data payload from dict responses or returns lists as-is."""
        if isinstance(res, dict):
            val = res.get("data", res)
            if key and isinstance(val, dict):
                return val.get(key, val)
            return val
        return res


@pytest.fixture(scope="session")
def live_server_check(api_url):
    """Skips E2E tests gracefully when the MT5 REST API container is not running."""
    try:
        resp = requests.get(f"{api_url}/", timeout=3)
        if resp.status_code >= 500:
            pytest.skip(f"Live server at {api_url} returned HTTP {resp.status_code}")
    except (requests.ConnectionError, requests.Timeout):
        pytest.skip(
            f"Live MT5 REST API server at {api_url} is unreachable. "
            "Start the container using 'docker compose up' before running E2E tests."
        )


@pytest.fixture(scope="session")
def api_client(api_url, api_key, live_server_check) -> MT5ApiClient:
    return MT5ApiClient(base_url=api_url, api_key=api_key)
