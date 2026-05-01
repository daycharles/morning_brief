"""Unit tests for scripts/fetchers/news_fetcher.py."""
from unittest.mock import patch

import pytest
import requests

from scripts.fetchers.news_fetcher import fetch
from scripts.utils.fetch_result import FetchResult

_CONFIG = {"newsapi_key": "test-key-123"}

_ARTICLE_FIXTURE = {
    "title": "Senate passes bill",
    "source": {"name": "Reuters"},
    "publishedAt": "2026-05-01T06:00:00Z",
    "url": "https://reuters.com/article/1",
}


def test_fetch_success():
    response = {"articles": [_ARTICLE_FIXTURE] * 5}
    with patch("scripts.fetchers.news_fetcher.get", return_value=response):
        result = fetch(_CONFIG)
    assert result.status == "success"
    assert len(result.data["articles"]) == 5
    article = result.data["articles"][0]
    assert article["title"] == "Senate passes bill"
    assert article["source"] == "Reuters"
    assert article["published_date"] == "2026-05-01"
    assert article["url"] == "https://reuters.com/article/1"


def test_fetch_empty_articles_ec006():
    """EC-006: empty results return success with message."""
    with patch("scripts.fetchers.news_fetcher.get", return_value={"articles": []}):
        result = fetch(_CONFIG)
    assert result.status == "success"
    assert "message" in result.data


def test_fetch_missing_api_key():
    result = fetch({})
    assert result.status == "failed"


def test_fetch_http_error():
    with patch("scripts.fetchers.news_fetcher.get", side_effect=requests.HTTPError("401")):
        result = fetch(_CONFIG)
    assert result.status == "failed"
