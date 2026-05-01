"""Unit tests for scripts/fetchers/weather_fetcher.py."""
from unittest.mock import patch

import pytest
import requests

from scripts.fetchers.weather_fetcher import fetch
from scripts.utils.fetch_result import FetchResult

_WEATHER_RESPONSE = {
    "daily": {
        "temperature_2m_max": [30.0],
        "temperature_2m_min": [20.0],
        "precipitation_probability_max": [25],
    }
}


def test_fetch_success_fahrenheit_conversion():
    with patch("scripts.fetchers.weather_fetcher.get", return_value=_WEATHER_RESPONSE):
        result = fetch({})
    assert result.status == "success"
    assert result.data["high_f"] == 86.0  # 30C = 86F
    assert result.data["low_f"] == 68.0   # 20C = 68F
    assert result.data["precipitation_probability"] == 25


def test_fetch_empty_daily_ec010():
    """EC-010: empty daily arrays return success with message."""
    with patch("scripts.fetchers.weather_fetcher.get", return_value={"daily": {"temperature_2m_max": [], "temperature_2m_min": [], "precipitation_probability_max": []}}):
        result = fetch({})
    assert result.status == "success"
    assert "message" in result.data


def test_fetch_missing_daily_key():
    with patch("scripts.fetchers.weather_fetcher.get", return_value={}):
        result = fetch({})
    assert result.status == "success"
    assert "message" in result.data


def test_fetch_http_error():
    with patch("scripts.fetchers.weather_fetcher.get", side_effect=requests.HTTPError("503")):
        result = fetch({})
    assert result.status == "failed"
    assert result.error_message is not None
