"""Slack notifier — optional webhook POST for Morning Brief delivery status."""
import json
import logging
import os

import requests

from scripts.utils.fetch_result import FetchResult  # noqa: F401 — imported for type reference

logger = logging.getLogger(__name__)

_SOURCE_LABELS = {
    "jira": "JIRA",
    "weather": "Weather",
    "news": "News",
    "sports": "Sports (Dodgers)",
    "mtg": "MTG",
}


def _build_payload(results: dict, report_filename: str, generated_at: str) -> dict:
    """Construct the Slack message payload."""
    status_lines = []
    for source, label in _SOURCE_LABELS.items():
        result = results.get(source)
        if result is None:
            icon = "⚠️"
            note = "not run"
        elif result.status == "success":
            icon = "✅"
            note = "success"
        else:
            icon = "❌"
            note = result.error_message or "failed"
        status_lines.append(f"{icon} *{label}*: {note}")

    status_text = "\n".join(status_lines)
    return {
        "text": f"Morning Brief generated: `{report_filename}`",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "☀️ Daily Morning Brief"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Report:* `{report_filename}`\n*Generated:* {generated_at}",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": status_text},
            },
        ],
    }


def post_summary(results: dict, report_filename: str, generated_at: str) -> None:
    """Post a Morning Brief delivery summary to Slack via Incoming Webhook.

    Args:
        results: Dict mapping source name (str) to FetchResult.
        report_filename: The filename of the generated report.
        generated_at: ISO-8601 UTC timestamp string.

    Returns:
        None. This function is always a no-op if SLACK_WEBHOOK_URL is absent.
        Failures are logged at WARNING level and never propagate.
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")

    if not webhook_url:
        logger.info("Slack notification skipped: SLACK_WEBHOOK_URL not set")
        return

    if not webhook_url.startswith("https://"):
        logger.warning("Slack notification skipped: SLACK_WEBHOOK_URL must use HTTPS")
        return

    try:
        payload = _build_payload(results, report_filename, generated_at)
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if not response.ok:
            logger.warning("Slack notification failed: HTTP %d", response.status_code)
        else:
            logger.info("Slack notification sent successfully")
    except Exception as exc:
        logger.warning("Slack notification failed: %s", exc)
