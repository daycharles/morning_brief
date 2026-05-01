"""Unit tests for scripts/fetchers/jira_fetcher.py."""
from unittest.mock import patch

import pytest
import requests

from scripts.fetchers.jira_fetcher import fetch
from scripts.utils.fetch_result import FetchResult

_BASE_CONFIG = {"jira_host": "test.atlassian.net", "jira_api_token": "test-token"}

_ISSUE_FIXTURE = {
    "key": "PROJ-1",
    "fields": {
        "summary": "Fix the bug",
        "assignee": {"displayName": "Alice"},
        "status": {"name": "In Progress"},
    },
}


def test_fetch_success():
    mock_response = {"issues": [_ISSUE_FIXTURE]}
    with patch("scripts.fetchers.jira_fetcher.get", return_value=mock_response):
        result = fetch(_BASE_CONFIG)
    assert result.status == "success"
    assert result.source == "jira"
    assert len(result.data["issues"]) == 1
    issue = result.data["issues"][0]
    assert issue["key"] == "PROJ-1"
    assert issue["summary"] == "Fix the bug"
    assert issue["assignee"] == "Alice"
    assert issue["status"] == "In Progress"


def test_fetch_deduplication():
    """EC-008: same key in both query results appears only once."""
    mock_response = {"issues": [_ISSUE_FIXTURE, _ISSUE_FIXTURE]}
    with patch("scripts.fetchers.jira_fetcher.get", return_value=mock_response):
        result = fetch(_BASE_CONFIG)
    assert result.status == "success"
    assert len(result.data["issues"]) == 1


def test_fetch_no_sprint_ec004():
    """EC-004: empty results return success with message."""
    with patch("scripts.fetchers.jira_fetcher.get", return_value={"issues": []}):
        result = fetch(_BASE_CONFIG)
    assert result.status == "success"
    assert "message" in result.data


def test_fetch_http_error():
    with patch("scripts.fetchers.jira_fetcher.get", side_effect=requests.HTTPError("401")):
        result = fetch(_BASE_CONFIG)
    assert result.status == "failed"
    assert result.error_message is not None


def test_fetch_missing_config():
    result = fetch({})
    assert result.status == "failed"


def test_fetch_unassigned_issue():
    issue = {
        "key": "PROJ-2",
        "fields": {"summary": "Task", "assignee": None, "status": {"name": "New"}},
    }
    with patch("scripts.fetchers.jira_fetcher.get", return_value={"issues": [issue]}):
        result = fetch(_BASE_CONFIG)
    assert result.data["issues"][0]["assignee"] == "Unassigned"
