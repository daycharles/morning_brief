"""Unit tests for scripts/formatters/report_builder.py."""
from scripts.formatters.report_builder import build_report
from scripts.utils.fetch_result import FetchResult

_GENERATED_AT = "2026-05-01T06:00:00Z"


def _make_results(statuses: dict) -> dict:
    results = {}
    for source, status in statuses.items():
        if status == "success":
            if source == "jira":
                data = {"issues": [{"key": "X-1", "summary": "Test", "assignee": "Bob", "status": "In Progress"}]}
            elif source == "weather":
                data = {"high_f": 75.0, "low_f": 60.0, "precipitation_probability": 10}
            elif source == "news":
                data = {"articles": [{"title": "News", "source": "AP", "published_date": "2026-05-01", "url": "https://ap.com"}]}
            elif source == "sports":
                data = {"opponent": "Giants", "dodgers_score": 3, "opponent_score": 1, "series_status": "Regular Season"}
            elif source == "mtg":
                data = {"sets": [{"set_name": "New Set", "release_date": "2026-05-01", "description": "100 cards"}]}
            else:
                data = {}
            results[source] = FetchResult(source=source, status="success", data=data)
        else:
            results[source] = FetchResult(source=source, status="failed", error_message="network error")
    return results


def test_report_contains_all_section_headers():
    results = _make_results({s: "success" for s in ["jira", "weather", "news", "sports", "mtg"]})
    report = build_report(results, _GENERATED_AT)
    assert "## 🗂️ JIRA Sprint Status" in report
    assert "## ☀️ Weather" in report
    assert "## 📰 Political Headlines" in report
    assert "## ⚾ LA Dodgers" in report
    assert "## 🃏 Magic: The Gathering" in report


def test_report_metadata_footer_ac011():
    """AC-011: Footer includes ISO-8601 timestamp and per-source status."""
    results = _make_results({s: "success" for s in ["jira", "weather", "news", "sports", "mtg"]})
    report = build_report(results, _GENERATED_AT)
    assert "## 📋 Report Metadata" in report
    assert "2026-05-01T06:00:00Z" in report
    assert "jira" in report
    assert "weather" in report


def test_jira_table_ac012():
    """AC-012: JIRA section renders as markdown table."""
    results = _make_results({"jira": "success", "weather": "failed", "news": "failed", "sports": "failed", "mtg": "failed"})
    report = build_report(results, _GENERATED_AT)
    assert "| Key | Summary | Assignee | Status |" in report
    assert "| X-1 |" in report


def test_news_table_ac012():
    """AC-012: News section renders as markdown table."""
    results = _make_results({"jira": "failed", "weather": "failed", "news": "success", "sports": "failed", "mtg": "failed"})
    report = build_report(results, _GENERATED_AT)
    assert "| Title | Source | Date | URL |" in report


def test_failed_source_renders_placeholder():
    results = _make_results({s: "failed" for s in ["jira", "weather", "news", "sports", "mtg"]})
    report = build_report(results, _GENERATED_AT)
    assert "⚠️" in report
    assert "unavailable" in report.lower()


def test_metadata_footer_shows_failed_status():
    results = _make_results({"jira": "failed", "weather": "success", "news": "success", "sports": "success", "mtg": "success"})
    report = build_report(results, _GENERATED_AT)
    assert "| jira | failed |" in report
    assert "| weather | success |" in report
