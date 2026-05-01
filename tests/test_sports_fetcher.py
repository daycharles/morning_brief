"""Unit tests for scripts/fetchers/sports_fetcher.py."""
from unittest.mock import patch

import pytest
import requests

from scripts.fetchers.sports_fetcher import fetch
from scripts.utils.fetch_result import FetchResult

_GAME_FIXTURE = {
    "status": {"abstractGameState": "Final"},
    "teams": {
        "home": {"team": {"id": 119, "name": "Los Angeles Dodgers"}, "score": 5},
        "away": {"team": {"id": 120, "name": "Washington Nationals"}, "score": 3},
    },
    "linescore": {"note": "Series tied 1-1"},
}

_SCHEDULE_RESPONSE = {
    "dates": [{"games": [_GAME_FIXTURE]}]
}


def test_fetch_success():
    with patch("scripts.fetchers.sports_fetcher.get", return_value=_SCHEDULE_RESPONSE):
        result = fetch({})
    assert result.status == "success"
    assert result.data["opponent"] == "Washington Nationals"
    assert result.data["dodgers_score"] == 5
    assert result.data["opponent_score"] == 3
    assert result.data["series_status"] == "Series tied 1-1"


def test_fetch_dodgers_as_away():
    game = {
        "status": {"abstractGameState": "Final"},
        "teams": {
            "home": {"team": {"id": 120, "name": "Washington Nationals"}, "score": 2},
            "away": {"team": {"id": 119, "name": "Los Angeles Dodgers"}, "score": 4},
        },
        "linescore": {"note": ""},
    }
    with patch("scripts.fetchers.sports_fetcher.get", return_value={"dates": [{"games": [game]}]}):
        result = fetch({})
    assert result.data["dodgers_score"] == 4
    assert result.data["opponent_score"] == 2


def test_fetch_no_games_ec005():
    """EC-005: no completed game returns success with message."""
    with patch("scripts.fetchers.sports_fetcher.get", return_value={"dates": []}):
        result = fetch({})
    assert result.status == "success"
    assert "message" in result.data


def test_fetch_http_error():
    with patch("scripts.fetchers.sports_fetcher.get", side_effect=requests.HTTPError("503")):
        result = fetch({})
    assert result.status == "failed"
