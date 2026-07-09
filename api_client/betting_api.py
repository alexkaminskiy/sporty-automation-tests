"""Thin client around the betting API.

Kept deliberately simple (no retry/backoff abstraction) — this is a test client for a
take-home assignment, not a production SDK. Each method returns the raw `requests.Response`
so tests can assert on status code, headers, and body independently rather than the client
making assumptions about what a test cares about.
"""
from __future__ import annotations

import requests

from config import API_BASE_URL, USER_ID

DEFAULT_TIMEOUT = 10  # seconds


class BettingAPIClient:
    def __init__(self, user_id: str = USER_ID, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self._session = requests.Session()
        self._session.headers.update({"x-user-id": user_id})

    def get_matches(self) -> requests.Response:
        return self._session.get(f"{self.base_url}/matches", timeout=DEFAULT_TIMEOUT)

    def get_balance(self) -> requests.Response:
        return self._session.get(f"{self.base_url}/balance", timeout=DEFAULT_TIMEOUT)

    def place_bet(self, match_id: str, selection: str, stake) -> requests.Response:
        """`stake` is intentionally untyped (Any) — tests need to send malformed types
        (e.g. strings, None) to exercise validation, so a strict type hint would fight
        the tests rather than help them."""
        payload = {"matchId": match_id, "selection": selection, "stake": stake}
        return self._session.post(f"{self.base_url}/place-bet", json=payload, timeout=DEFAULT_TIMEOUT)

    def place_bet_raw(self, json_body) -> requests.Response:
        """For malformed-payload tests (non-object JSON, missing fields, wrong types)
        where callers need full control over the body shape."""
        return self._session.post(f"{self.base_url}/place-bet", json=json_body, timeout=DEFAULT_TIMEOUT)

    def reset_balance(self) -> requests.Response:
        return self._session.post(f"{self.base_url}/reset-balance", timeout=DEFAULT_TIMEOUT)

    def without_auth(self) -> "BettingAPIClient":
        """Returns a client with no x-user-id header, for 401 test cases."""
        client = BettingAPIClient.__new__(BettingAPIClient)
        client.base_url = self.base_url
        client._session = requests.Session()
        return client
