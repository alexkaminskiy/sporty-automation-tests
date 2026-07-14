"""Thin client around the betting API.

Kept deliberately simple (no retry/backoff abstraction) — this is a test client for a
take-home assignment, not a production SDK. Each method returns the raw `requests.Response`
so tests can assert on status code, headers, and body independently rather than the client
making assumptions about what a test cares about.
"""

from typing import Any

import requests

from config import API_BASE_URL, USER_ID

DEFAULT_TIMEOUT = 10  # seconds


class BettingAPIClient:
    def __init__(self, user_id: str = USER_ID, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"x-user-id": user_id})


    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        return self._session.request(method, f"{self.base_url}{path}", **kwargs)

    def get_matches(self) -> requests.Response:
        return self._request("GET", "/matches")

    def get_balance(self) -> requests.Response:
        return self._request("GET", "/balance")

    def place_bet(self, match_id: str, selection: str, stake: Any) -> requests.Response:
        """`stake` is intentionally typed as Any — tests need to send malformed types
        (e.g. strings, None) to exercise validation, so a strict type hint would fight
        the tests rather than help them."""
        payload = {"matchId": match_id, "selection": selection, "stake": stake}
        return self._request("POST", "/place-bet", json=payload)

    def place_bet_raw(self, json_body: Any) -> requests.Response:
        """For malformed-payload tests (non-object JSON, missing fields, wrong types)
        where callers need full control over the body shape."""
        return self._request("POST", "/place-bet", json=json_body)

    def reset_balance(self) -> requests.Response:
        return self._request("POST", "/reset-balance")

    def without_auth(self) -> "BettingAPIClient":
        """Returns a client with no x-user-id header, for 401 test cases."""
        client = BettingAPIClient(base_url=self.base_url)
        client._session.headers.pop("x-user-id", None)
        return client