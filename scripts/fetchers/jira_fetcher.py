"""JIRA fetcher — retrieves active sprint In-Progress and new (last 24h) issues."""
import logging
from typing import Any

from scripts.utils.fetch_result import FetchResult
from scripts.utils.http_client import get

logger = logging.getLogger(__name__)

_JQL_IN_PROGRESS = "status = 'In Progress' AND sprint in openSprints()"
_JQL_NEW_24H = "created >= -24h"
_FIELDS = "key,summary,assignee,status"


def _parse_issue(issue: dict) -> dict:
    """Extract key, summary, assignee, status from a raw JIRA issue dict."""
    fields = issue.get("fields", {})
    assignee = fields.get("assignee")
    assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
    return {
        "key": issue.get("key", ""),
        "summary": fields.get("summary", ""),
        "assignee": assignee_name,
        "status": fields.get("status", {}).get("name", ""),
    }


def _run_jql(base_url: str, jql: str, headers: dict) -> list[dict]:
    """Run a single JQL query and return the list of raw issue dicts."""
    response = get(
        base_url,
        headers=headers,
        params={"jql": jql, "fields": _FIELDS, "maxResults": 50},
    )
    return response.get("issues", [])


def fetch(config: dict) -> FetchResult:
    """Fetch JIRA active sprint issues and issues created in the last 24 hours.

    Args:
        config: Dict with keys:
            - jira_host: JIRA instance hostname (e.g. 'company.atlassian.net')
            - jira_api_token: Bearer token for JIRA API v3 authentication

    Returns:
        FetchResult with status='success' and data={'issues': [...]} on success.
        FetchResult with status='failed' on any error.
    """
    try:
        jira_host = config.get("jira_host", "")
        jira_api_token = config.get("jira_api_token", "")

        if not jira_host or not jira_api_token:
            missing = []
            if not jira_host:
                missing.append("jira_host")
            if not jira_api_token:
                missing.append("jira_api_token")
            raise ValueError(f"Missing required config keys: {missing}")

        base_url = f"https://{jira_host}/rest/api/3/search/jql"
        headers = {
            "Authorization": f"Bearer {jira_api_token}",
            "Accept": "application/json",
        }

        # Run both JQL queries
        in_progress_raw = _run_jql(base_url, _JQL_IN_PROGRESS, headers)
        new_24h_raw = _run_jql(base_url, _JQL_NEW_24H, headers)

        # Merge and deduplicate by issue key (EC-008)
        seen_keys: set[str] = set()
        issues: list[dict] = []
        for raw_issue in in_progress_raw + new_24h_raw:
            key = raw_issue.get("key", "")
            if key and key not in seen_keys:
                seen_keys.add(key)
                issues.append(_parse_issue(raw_issue))

        logger.info("JIRA: fetched %d unique issues", len(issues))

        data: dict[str, Any] = {"issues": issues}
        if not issues:
            # EC-004: no active sprint issues
            data["message"] = "No active sprint issues found."

        return FetchResult(source="jira", status="success", data=data)

    except Exception as exc:
        logger.warning("JIRA fetch failed: %s", exc)
        return FetchResult(source="jira", status="failed", error_message=str(exc))
