"""Unit tests for scripts/utils/http_client.py."""
from unittest.mock import MagicMock, call, patch

import pytest
import requests

from scripts.utils.http_client import get


def test_get_rejects_http_url():
    with pytest.raises(ValueError, match="https://"):
        get("http://example.com/api")


def test_get_returns_json_on_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status = MagicMock()
    with patch("scripts.utils.http_client.requests.Session") as MockSession:
        instance = MockSession.return_value
        instance.get.return_value = mock_response
        result = get("https://example.com/api")
    assert result == {"key": "value"}


def test_get_retries_on_connection_error():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status = MagicMock()
    with patch("scripts.utils.http_client.requests.Session") as MockSession, \
         patch("scripts.utils.http_client.time.sleep") as mock_sleep:
        instance = MockSession.return_value
        instance.get.side_effect = [
            requests.ConnectionError("connection refused"),
            mock_response,
        ]
        result = get("https://example.com/api")
    assert result == {"ok": True}
    mock_sleep.assert_called_once_with(1)


def test_get_retries_on_5xx_and_succeeds():
    error_response = MagicMock()
    error_response.status_code = 503
    ok_response = MagicMock()
    ok_response.status_code = 200
    ok_response.ok = True
    ok_response.json.return_value = {"data": "ok"}
    ok_response.raise_for_status = MagicMock()
    with patch("scripts.utils.http_client.requests.Session") as MockSession, \
         patch("scripts.utils.http_client.time.sleep") as mock_sleep:
        instance = MockSession.return_value
        instance.get.side_effect = [error_response, ok_response]
        result = get("https://example.com/api")
    assert result == {"data": "ok"}
    mock_sleep.assert_called_once_with(1)


def test_get_raises_on_429():
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
    with patch("scripts.utils.http_client.requests.Session") as MockSession:
        instance = MockSession.return_value
        instance.get.return_value = mock_response
        with pytest.raises(requests.HTTPError):
            get("https://example.com/api")


def test_get_exhausts_retries_and_raises():
    with patch("scripts.utils.http_client.requests.Session") as MockSession, \
         patch("scripts.utils.http_client.time.sleep"):
        instance = MockSession.return_value
        instance.get.side_effect = requests.ConnectionError("always failing")
        with pytest.raises(requests.ConnectionError):
            get("https://example.com/api")
    assert instance.get.call_count == 3  # initial + 2 retries
