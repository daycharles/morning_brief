"""Daily Morning Brief — main orchestrator script.

Run via: python scripts/morning_brief.py
"""
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Ensure repo root is on sys.path so `scripts.*` imports work when the script
# is invoked directly (e.g. `python scripts/morning_brief.py` from repo root).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetchers import (
    jira_fetcher,
    mtg_fetcher,
    news_fetcher,
    sports_fetcher,
    weather_fetcher,
)
from scripts.formatters.report_builder import build_report
from scripts.notifiers.slack_notifier import post_summary
from scripts.utils.fetch_result import FetchResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_REQUIRED_SECRETS = ["JIRA_API_TOKEN", "JIRA_HOST", "NEWSAPI_KEY"]
_OUTPUT_DIR = ".agents-work/2026-05-01_morning-brief-system"


def validate_config() -> dict:
    """Read and validate environment config. Returns config dict.

    Logs missing required secret NAMES (never values).
    Raises SystemExit(1) if ALL required secrets are absent.
    """
    config = {
        "jira_api_token": os.environ.get("JIRA_API_TOKEN", ""),
        "jira_host": os.environ.get("JIRA_HOST", ""),
        "newsapi_key": os.environ.get("NEWSAPI_KEY", ""),
    }

    missing = [k for k in _REQUIRED_SECRETS if not os.environ.get(k)]
    if missing:
        logger.warning("Missing secrets: %s", ", ".join(missing))
        if len(missing) == len(_REQUIRED_SECRETS):
            logger.error("All required secrets missing — cannot proceed")
            raise SystemExit(1)

    return config


def _run_fetcher(name: str, fetcher_fn, config: dict) -> tuple[str, FetchResult]:
    """Run a single fetcher function and return (name, FetchResult)."""
    try:
        result = fetcher_fn(config)
    except Exception as exc:
        logger.warning("Fetcher %s raised unexpected exception: %s", name, exc)
        result = FetchResult(source=name, status="failed", error_message=str(exc))
    return name, result


def main() -> None:
    """Run the Daily Morning Brief pipeline."""
    config = validate_config()

    fetchers = {
        "jira": jira_fetcher.fetch,
        "weather": weather_fetcher.fetch,
        "news": news_fetcher.fetch,
        "sports": sports_fetcher.fetch,
        "mtg": mtg_fetcher.fetch,
    }

    results: dict[str, FetchResult] = {}

    logger.info("Starting parallel fetch of %d sources", len(fetchers))
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_run_fetcher, name, fn, config): name
            for name, fn in fetchers.items()
        }
        for future in as_completed(futures):
            name, result = future.result()
            results[name] = result
            logger.info("Fetcher '%s' completed with status: %s", name, result.status)

    # Generate report
    now_utc = datetime.now(tz=timezone.utc)
    generated_at = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = now_utc.strftime("%Y-%m-%d")
    filename = f"Morning-Brief-{date_str}.md"

    report_content = build_report(results, generated_at)

    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(_OUTPUT_DIR, filename)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(report_content)
    logger.info("Report written: %s", output_path)

    # Optional Slack notification
    if os.environ.get("SLACK_WEBHOOK_URL"):
        post_summary(results, filename, generated_at)

    # Exit code
    success_count = sum(1 for r in results.values() if r.status == "success")
    if success_count == 0:
        logger.error("All fetchers failed — exiting with code 1")
        sys.exit(1)

    logger.info("Morning Brief complete: %d/%d sources succeeded", success_count, len(fetchers))
    sys.exit(0)


if __name__ == "__main__":
    main()
