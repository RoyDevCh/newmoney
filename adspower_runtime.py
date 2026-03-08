#!/usr/bin/env python3
"""Runtime helpers for AdsPower Local API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import requests


DEFAULT_BASE_URLS = (
    "http://local.adspower.net:50361",
    "http://127.0.0.1:50361",
    "http://127.0.0.1:50325",
    "http://127.0.0.1:50326",
    "http://127.0.0.1:50631",
)


def _build_candidates() -> Iterable[str]:
    env_url = os.getenv("ADSPOWER_BASE_URL", "").strip()
    if env_url:
        yield env_url.rstrip("/")
    for url in DEFAULT_BASE_URLS:
        yield url.rstrip("/")


def detect_base_url(timeout: float = 2.0) -> str:
    """Find the first reachable AdsPower local API base url."""
    seen = set()
    for url in _build_candidates():
        if url in seen:
            continue
        seen.add(url)
        try:
            resp = requests.get(f"{url}/status", timeout=timeout)
            if resp.status_code == 200:
                return url
        except requests.RequestException:
            continue
    ports = ", ".join(DEFAULT_BASE_URLS)
    raise RuntimeError(
        f"AdsPower API not reachable. Tried ADSPOWER_BASE_URL and candidates: {ports}."
    )


@dataclass
class AdsPowerClient:
    api_key: str
    base_url: Optional[str] = None
    timeout: float = 15.0

    def __post_init__(self) -> None:
        self.base_url = (self.base_url or detect_base_url()).rstrip("/")
        self._headers = {"Authorization": f"Bearer {self.api_key}"}

    def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> Dict:
        url = f"{self.base_url}{path}"
        resp = requests.get(url, headers=self._headers, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("code") not in (None, 0):
            raise RuntimeError(f"AdsPower error ({path}): {data.get('msg')}")
        return data

    def get_ws(self, user_id: str, allow_start: bool = True) -> str:
        data = self._get("/api/v1/browser/active", params={"user_id": user_id})
        ws = (
            data.get("data", {}).get("ws", {}).get("puppeteer")
            or data.get("data", {}).get("ws", {}).get("selenium")
        )
        if ws:
            return ws
        if not allow_start:
            raise RuntimeError(f"No active websocket for user_id={user_id}")
        data = self._get("/api/v1/browser/start", params={"user_id": user_id})
        ws = (
            data.get("data", {}).get("ws", {}).get("puppeteer")
            or data.get("data", {}).get("ws", {}).get("selenium")
        )
        if not ws:
            raise RuntimeError(f"Could not get websocket for user_id={user_id}")
        return ws

    def get_active_ws(self, user_id: str) -> str:
        data = self._get("/api/v1/browser/active", params={"user_id": user_id})
        ws = (
            data.get("data", {}).get("ws", {}).get("puppeteer")
            or data.get("data", {}).get("ws", {}).get("selenium")
        )
        if not ws:
            raise RuntimeError(f"No active websocket for user_id={user_id}")
        return ws

    def stop(self, user_id: str) -> None:
        try:
            self._get("/api/v1/browser/stop", params={"user_id": user_id})
        except Exception:
            pass

    def stop_many(self, user_ids: Iterable[str]) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for user_id in user_ids:
            try:
                self._get("/api/v1/browser/stop", params={"user_id": user_id})
                results[str(user_id)] = True
            except Exception:
                results[str(user_id)] = False
        return results
