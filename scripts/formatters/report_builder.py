"""Report builder — renders the Daily Morning Brief as a markdown string."""
import logging

from scripts.utils.fetch_result import FetchResult

logger = logging.getLogger(__name__)


def _render_jira_section(result: FetchResult) -> str:
    """Render the JIRA Sprint Status section."""
    lines = ["## 🗂️ JIRA Sprint Status", ""]
    if result is None or result.status != "success":
        error = result.error_message if result else "No data"
        lines.append(f"> ⚠️ JIRA data unavailable: {error}")
        return "\n".join(lines)

    data = result.data or {}
    message = data.get("message")
    issues = data.get("issues", [])

    if message and not issues:
        lines.append(f"> ℹ️ {message}")
        return "\n".join(lines)

    if not issues:
        lines.append("> ℹ️ No active sprint issues found.")
        return "\n".join(lines)

    lines.append("| Key | Summary | Assignee | Status |")
    lines.append("|---|---|---|---|")
    for issue in issues:
        key = issue.get("key", "")
        summary = issue.get("summary", "").replace("|", "\\|")
        assignee = issue.get("assignee", "Unassigned")
        status = issue.get("status", "")
        lines.append(f"| {key} | {summary} | {assignee} | {status} |")

    return "\n".join(lines)


def _render_weather_section(result: FetchResult) -> str:
    """Render the Weather section."""
    lines = ["## ☀️ Weather — Los Angeles", ""]
    if result is None or result.status != "success":
        error = result.error_message if result else "No data"
        lines.append(f"> ⚠️ Weather data unavailable: {error}")
        return "\n".join(lines)

    data = result.data or {}
    message = data.get("message")
    if message:
        lines.append(f"> ℹ️ {message}")
        return "\n".join(lines)

    high_f = data.get("high_f", "N/A")
    low_f = data.get("low_f", "N/A")
    precip = data.get("precipitation_probability", "N/A")
    lines.append(f"- **High:** {high_f}°F")
    lines.append(f"- **Low:** {low_f}°F")
    lines.append(f"- **Precipitation Probability:** {precip}%")
    return "\n".join(lines)


def _render_news_section(result: FetchResult) -> str:
    """Render the Political Headlines section."""
    lines = ["## 📰 Political Headlines", ""]
    if result is None or result.status != "success":
        error = result.error_message if result else "No data"
        lines.append(f"> ⚠️ News data unavailable: {error}")
        return "\n".join(lines)

    data = result.data or {}
    message = data.get("message")
    articles = data.get("articles", [])

    if message and not articles:
        lines.append(f"> ℹ️ {message}")
        return "\n".join(lines)

    if not articles:
        lines.append("> ℹ️ No headlines available.")
        return "\n".join(lines)

    lines.append("| Title | Source | Date | URL |")
    lines.append("|---|---|---|---|")
    for article in articles:
        title = article.get("title", "").replace("|", "\\|")
        source = article.get("source", "").replace("|", "\\|")
        date = article.get("published_date", "")
        url = article.get("url", "")
        lines.append(f"| {title} | {source} | {date} | {url} |")

    return "\n".join(lines)


def _render_sports_section(result: FetchResult) -> str:
    """Render the LA Dodgers Sports section."""
    lines = ["## ⚾ LA Dodgers", ""]
    if result is None or result.status != "success":
        error = result.error_message if result else "No data"
        lines.append(f"> ⚠️ Sports data unavailable: {error}")
        return "\n".join(lines)

    data = result.data or {}
    message = data.get("message")
    if message:
        lines.append(f"> ℹ️ {message}")
        return "\n".join(lines)

    opponent = data.get("opponent", "Unknown")
    dodgers_score = data.get("dodgers_score", "?")
    opponent_score = data.get("opponent_score", "?")
    series_status = data.get("series_status", "")

    lines.append(f"**Most Recent Game:** Dodgers vs {opponent}")
    lines.append(f"**Score:** {dodgers_score} – {opponent_score}")
    if series_status:
        lines.append(f"**Series:** {series_status}")
    return "\n".join(lines)


def _render_mtg_section(result: FetchResult) -> str:
    """Render the Magic: The Gathering section."""
    lines = ["## 🃏 Magic: The Gathering", ""]
    if result is None or result.status != "success":
        error = result.error_message if result else "No data"
        lines.append(f"> ⚠️ MTG data unavailable: {error}")
        return "\n".join(lines)

    data = result.data or {}
    message = data.get("message")
    sets = data.get("sets", [])

    if message and not sets:
        lines.append(f"> ℹ️ {message}")
        return "\n".join(lines)

    if not sets:
        lines.append("> ℹ️ No new MTG releases in the last 7 days.")
        return "\n".join(lines)

    lines.append("**Recent Releases (last 7 days):**")
    lines.append("")
    for mtg_set in sets:
        name = mtg_set.get("set_name", "Unknown Set")
        release_date = mtg_set.get("release_date", "")
        description = mtg_set.get("description", "")
        lines.append(f"- **{name}** ({release_date}) — {description}")

    return "\n".join(lines)


def _render_metadata_footer(results: dict, generated_at: str) -> str:
    """Render the Report Metadata footer."""
    lines = ["## 📋 Report Metadata", ""]
    lines.append(f"**Generated:** {generated_at} UTC")
    lines.append("")
    lines.append("| Source | Status |")
    lines.append("|---|---|")
    for source in ["jira", "weather", "news", "sports", "mtg"]:
        result = results.get(source)
        status = result.status if result is not None else "not run"
        lines.append(f"| {source} | {status} |")
    return "\n".join(lines)


def build_report(results: dict, generated_at: str) -> str:
    """Render the complete Daily Morning Brief as a markdown string.

    Args:
        results: Dict mapping source name (str) to FetchResult.
        generated_at: ISO-8601 UTC timestamp string.

    Returns:
        Complete markdown string ready to write to disk.
    """
    sections = [
        f"# ☀️ Daily Morning Brief — {generated_at[:10]}",
        "",
        _render_jira_section(results.get("jira")),
        "",
        _render_weather_section(results.get("weather")),
        "",
        _render_news_section(results.get("news")),
        "",
        _render_sports_section(results.get("sports")),
        "",
        _render_mtg_section(results.get("mtg")),
        "",
        _render_metadata_footer(results, generated_at),
        "",
    ]
    report = "\n".join(sections)
    logger.info("Report built: %d characters", len(report))
    return report
