"""Integration test — full pipeline producing Morning-Brief-*.md with mocked HTTP."""
import importlib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SESSION_DIR = Path(".agents-work/2026-05-01_morning-brief-system")

# Minimal fixture responses for each fetcher
_JIRA_RESPONSE = {
    "issues": [{"key": "PROJ-1", "fields": {"summary": "Test task", "assignee": {"displayName": "Bob"}, "status": {"name": "In Progress"}}}]
}
_WEATHER_RESPONSE = {
    "daily": {"temperature_2m_max": [25.0], "temperature_2m_min": [15.0], "precipitation_probability_max": [20]}
}
_NEWS_RESPONSE = {
    "articles": [{"title": "Test headline", "source": {"name": "AP"}, "publishedAt": "2026-05-01T06:00:00Z", "url": "https://ap.com"}]
}
_SPORTS_RESPONSE = {
    "dates": [{"games": [{"status": {"abstractGameState": "Final"}, "teams": {"home": {"team": {"id": 119, "name": "Los Angeles Dodgers"}, "score": 5}, "away": {"team": {"id": 120, "name": "Giants"}, "score": 3}}, "linescore": {"note": "Series 1-1"}}]}]
}
_MTG_RESPONSE = {
    "data": [{"name": "Test Set", "released_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"), "card_count": 100, "set_type": "expansion"}]
}


def _mock_get(url: str, **kwargs) -> dict:
    """Route mock API calls to fixture responses."""
    if "atlassian.net" in url:
        return _JIRA_RESPONSE
    elif "open-meteo.com" in url:
        return _WEATHER_RESPONSE
    elif "newsapi.org" in url:
        return _NEWS_RESPONSE
    elif "statsapi.mlb.com" in url:
        return _SPORTS_RESPONSE
    elif "scryfall.com" in url:
        return _MTG_RESPONSE
    return {}


@pytest.mark.integration
def test_full_pipeline_produces_report(monkeypatch, tmp_path):
    """Full pipeline test: mock HTTP, run main(), assert report file."""
    # Set required environment variables
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
    monkeypatch.setenv("JIRA_HOST", "test.atlassian.net")
    monkeypatch.setenv("NEWSAPI_KEY", "test-newsapi-key")
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

    # Patch get() at every location it was imported into (from ... import get)
    with patch("scripts.utils.http_client.get", side_effect=_mock_get), \
         patch("scripts.fetchers.jira_fetcher.get", side_effect=_mock_get), \
         patch("scripts.fetchers.weather_fetcher.get", side_effect=_mock_get), \
         patch("scripts.fetchers.news_fetcher.get", side_effect=_mock_get), \
         patch("scripts.fetchers.sports_fetcher.get", side_effect=_mock_get), \
         patch("scripts.fetchers.mtg_fetcher.get", side_effect=_mock_get):
        # Prevent sys.exit from stopping the test
        with pytest.raises(SystemExit) as exc_info:
            from scripts import morning_brief
            # Reload to pick up fresh env vars
            importlib.reload(morning_brief)
            morning_brief.main()

    # Exit code 0 = at least one success
    assert exc_info.value.code == 0

    # Find the generated report file
    today_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    expected_filename = f"Morning-Brief-{today_str}.md"
    report_path = _SESSION_DIR / expected_filename

    # AC-007: filename matches Morning-Brief-YYYY-MM-DD.md
    assert report_path.exists(), f"Report not found at: {report_path}"

    # AC-008: file is in correct directory
    assert report_path.parent == _SESSION_DIR

    content = report_path.read_text(encoding="utf-8")

    # Assert all 5 section headers
    assert "## 🗂️ JIRA Sprint Status" in content, "Missing JIRA section"
    assert "## ☀️ Weather" in content, "Missing Weather section"
    assert "## 📰 Political Headlines" in content, "Missing News section"
    assert "## ⚾ LA Dodgers" in content, "Missing Sports section"
    assert "## 🃏 Magic: The Gathering" in content, "Missing MTG section"

    # AC-011: Metadata footer present
    assert "## 📋 Report Metadata" in content, "Missing Report Metadata footer"

    # AC-007: filename pattern validation
    assert re.match(r"Morning-Brief-\d{4}-\d{2}-\d{2}\.md", expected_filename)

    # File is non-empty
    assert len(content) > 500, "Report seems too short"
