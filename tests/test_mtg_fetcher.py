"""Unit tests for scripts/fetchers/mtg_fetcher.py."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
import requests

from scripts.fetchers.mtg_fetcher import fetch
from scripts.utils.fetch_result import FetchResult


def _today() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")


def _days_ago(n: int) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=n)
    return dt.strftime("%Y-%m-%d")


def test_fetch_recent_set():
    response = {
        "data": [{"name": "Thunder Junction", "released_at": _today(), "card_count": 250, "set_type": "expansion"}]
    }
    with patch("scripts.fetchers.mtg_fetcher.get", return_value=response):
        result = fetch({})
    assert result.status == "success"
    assert len(result.data["sets"]) == 1
    s = result.data["sets"][0]
    assert s["set_name"] == "Thunder Junction"
    assert s["description"] == "250 cards"


def test_fetch_filters_old_sets():
    response = {
        "data": [
            {"name": "Old Set", "released_at": _days_ago(30), "card_count": 100, "set_type": "expansion"},
        ]
    }
    with patch("scripts.fetchers.mtg_fetcher.get", return_value=response):
        result = fetch({})
    assert result.status == "success"
    assert result.data["sets"] == []


def test_fetch_no_recent_sets_ec006():
    """EC-006: no sets in last 7 days returns success with message."""
    with patch("scripts.fetchers.mtg_fetcher.get", return_value={"data": []}):
        result = fetch({})
    assert result.status == "success"
    assert "message" in result.data


def test_fetch_http_error():
    with patch("scripts.fetchers.mtg_fetcher.get", side_effect=requests.HTTPError("500")):
        result = fetch({})
    assert result.status == "failed"
