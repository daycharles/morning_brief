# Daily Morning Briefing System — Automated Aggregation and Markdown Report Generation

## Problem Statement
Teams lack a consolidated daily view of sprint progress, local weather, political news, sports results, and hobby-relevant updates. Engineers and team leads must visit multiple tools each morning to get context for their day — a process that is manual, inconsistent, and time-consuming. This system automates that aggregation into a single, structured daily markdown report generated at 6:00 AM UTC via a GitHub Actions workflow.

---

## Goals
- Automate daily report generation at 6:00 AM UTC with zero manual intervention.
- Aggregate data from 5 distinct sources: JIRA, Weather, Political News, MLB Dodgers, Magic: The Gathering.
- Store each report as a clean, dated markdown file: `Morning-Brief-YYYY-MM-DD.md`.
- Manage all credentials exclusively through GitHub Secrets — no hardcoded keys.
- Implement graceful degradation: partial report generated if any individual source fails.
- Keep implementation modular so new data sources can be added without refactoring.
- Provide a metadata footer on each report showing source success/failure status.

---

## Non-Goals
- Real-time or on-demand report generation (scheduled only).
- Web dashboard or UI for report viewing.
- Email or Slack notifications (report stored as file only).
- Support for multiple Jira projects or locations (single project, LA fixed).
- Historical trend analysis or data retention beyond file storage.
- Custom user-configurable report templates.

---

## User Stories
- **US-001** — As a developer, I want to open one file each morning to see sprint status, news, and hobby updates so I can plan my day without switching between tools.
- **US-002** — As a Scrum Master, I want the JIRA sprint summary to include In Progress and New issues with assignees so I can quickly triage the board.
- **US-003** — As a team member in Los Angeles, I want today's weather forecast in the report so I can plan commuting and activities.
- **US-004** — As a citizen, I want the top 5 national political headlines so I stay informed without browsing news sites.
- **US-005** — As a Dodgers fan, I want the most recent game score, opponent, and series status so I can follow the team without checking the MLB app.
- **US-006** — As an MTG player, I want the latest set announcements and card spoilers so I can keep up with the game.

---

## Functional Requirements

### FR-001 — Scheduled GitHub Action
The system MUST include a GitHub Actions workflow file (`.github/workflows/morning-brief.yml`) with a `schedule` trigger: `cron: '0 6 * * *'` (daily 6:00 AM UTC). The workflow MUST support manual `workflow_dispatch` trigger for testing.

### FR-002 — Python Script Execution
The workflow MUST invoke a Python 3.10+ script (`scripts/morning_brief.py`) that orchestrates all data collection and report generation. The script MUST complete within 5 minutes; each API call MUST timeout at 10 seconds.

### FR-003 — JIRA Integration
The script MUST query the JIRA REST API v3 to retrieve: (a) all issues in the active sprint with status `In Progress`; (b) all issues created in the last 24 hours. Each issue record MUST include: key, summary, assignee display name, and status. Authentication: Bearer token via `JIRA_API_TOKEN` secret. Endpoint: `https://{JIRA_HOST}/rest/api/3/search` with JQL filter.

### FR-004 — Weather (Los Angeles, CA)
The script MUST fetch the current weather forecast for Los Angeles, CA (latitude 34.0522°N, longitude 118.2437°W) using the Open-Meteo API (free, no auth required). The report MUST include: current condition description, High temperature (°F), Low temperature (°F), precipitation probability.

### FR-005 — Political Headlines
The script MUST retrieve the top 5 trending national US political headlines using the NewsAPI (`newsapi.org`). Each headline MUST include: title, source name, published date (YYYY-MM-DD), and URL. Authentication: API key via `NEWSAPI_KEY` secret.

### FR-006 — LA Dodgers Score
The script MUST query the MLB Stats API (`statsapi.mlb.com`) to retrieve the LA Dodgers' most recent completed game (team ID: 119). The report MUST include: opponent team name, final score (Dodgers vs Opponent), series win/loss/tie status. No authentication required.

### FR-007 — Magic: The Gathering News
The script MUST query the Scryfall API (`api.scryfall.com`) to retrieve the latest set announcements and card spoilers released within the last 7 days. No authentication required. The report MUST include: set name, release date, and a brief description for each result.

### FR-008 — Markdown Report Generation
The script MUST generate a markdown file named `Morning-Brief-YYYY-MM-DD.md` (where the date is the UTC date at time of execution) and store it in `.agents-work/2026-05-01_morning-brief-system/`. The report MUST use a consistent template with labelled sections for each data source.

### FR-009 — GitHub Secrets Management
All API credentials MUST be read from environment variables backed by GitHub Secrets: `JIRA_API_TOKEN`, `JIRA_HOST`, `NEWSAPI_KEY`. `OPENWEATHER_API_KEY` is optional (if OpenWeatherMap replaces Open-Meteo). No credentials MUST appear in source code, logs, or the generated report.

### FR-010 — Error Resilience
If any individual data source fails (timeout, HTTP error, parse error), the script MUST log a warning and continue generating the report with the remaining available sections. The metadata footer MUST record which sources succeeded and which failed. The workflow exit code MUST be `0` if at least one section is generated, `1` only if all sources fail.

---

## Non-Functional Requirements

- **NFR-001 — Performance:** Total script execution MUST complete in under 5 minutes. Each HTTP request MUST have a 10-second timeout. API calls MAY run in parallel threads to reduce total time.
- **NFR-002 — Reliability:** Workflow MUST achieve 95% successful execution on scheduled runs. Retry logic (2 retries with exponential backoff) MUST be applied to transient failures.
- **NFR-003 — Usability:** The generated markdown report MUST render cleanly in GitHub's markdown viewer and standard markdown editors. Sections MUST be clearly labelled and scannable.
- **NFR-004 — Security:** No API keys, tokens, or sensitive data in source code. HTTPS for all API calls. Error messages MUST NOT expose credential values. GitHub Actions automatically masks secrets in logs.
- **NFR-005 — Maintainability:** Python code MUST follow PEP 8. Each data fetcher MUST be a separate module/function. Unit tests MUST cover parsing logic for each fetcher.
- **NFR-006 — Extensibility:** The data source architecture MUST allow adding new sources by adding a new fetcher module without changing core orchestration or formatting logic.

---

## Edge Cases

- **EC-001 — API Rate Limiting:** If any API returns HTTP 429, log a warning, record source as `failed/rate-limited` in metadata footer, and continue with remaining sources.
- **EC-002 — Network Timeouts:** If an API call times out after 10 seconds, retry up to 2 times with exponential backoff (1s, 2s). On final failure, log error and continue.
- **EC-003 — Malformed API Response:** If JSON parsing fails on any response, log a warning with the source name and continue. Do not crash the entire script.
- **EC-004 — No Active JIRA Sprint:** If JIRA returns no active sprint, render the JIRA section with message: `No active sprint found.`
- **EC-005 — MLB Off-Season:** If MLB Stats API returns no recent game (off-season), render the Sports section with message: `No recent Dodgers game available.`
- **EC-006 — No Recent MTG Releases:** If Scryfall returns no sets released in the last 7 days, render the MTG section with message: `No new MTG releases in the last 7 days.`
- **EC-007 — Workflow Cancellation:** If the workflow is manually cancelled mid-run, the partially written report file MAY be incomplete. The next scheduled run will overwrite it with a complete report.
- **EC-008 — Duplicate Data:** JIRA issues appearing in both In Progress and New-24h filters MUST be deduplicated by issue key before rendering.

---

## Assumptions

1. The JIRA instance (cloud or on-premise) has a REST API v3-compatible endpoint accessible from GitHub Actions runners.
2. GitHub Secrets (`JIRA_API_TOKEN`, `JIRA_HOST`, `NEWSAPI_KEY`) are pre-configured by the repository administrator before the workflow first runs.
3. Open-Meteo (free, no auth) is the primary weather source; OpenWeatherMap is an optional alternative if `OPENWEATHER_API_KEY` is provided.
4. Los Angeles, CA coordinates (34.0522°N, 118.2437°W) are fixed; no runtime location configuration is required.
5. UTC is the canonical timezone for all date calculations and report naming.
6. Python 3.10+ is available on GitHub Actions `ubuntu-latest` runner.
7. The `requests` library and standard library modules (`json`, `datetime`, `os`, `pathlib`) are sufficient for all HTTP calls.
8. Overwriting an existing report for the same date (e.g., on re-run or manual dispatch) is acceptable.
9. Repository administrators are responsible for manually configuring GitHub Secrets before workflow activation.
10. The NewsAPI free tier provides adequate daily quota for a single API call per day.

---

## Definition of Done

1. GitHub Actions workflow file (`.github/workflows/morning-brief.yml`) exists with correct cron schedule.
2. Python script (`scripts/morning_brief.py`) successfully fetches data from all 5 sources when credentials are valid.
3. Error handling covers all 8 edge cases (EC-001 through EC-008).
4. Generated markdown report renders correctly in GitHub's UI.
5. All API credentials are read exclusively from environment variables (GitHub Secrets).
6. No credentials appear in source code, logs, or generated reports.
7. Unit tests exist for each data fetcher's response parsing logic.
8. Integration test validates full workflow end-to-end with test credentials.
9. `README.md` or `SETUP.md` documents required GitHub Secrets and setup steps.
10. All 12 acceptance criteria in `acceptance.json` are verifiable and met.
11. Script exits with code `0` on success or partial success; code `1` on total failure.
12. Report filename follows `Morning-Brief-YYYY-MM-DD.md` (UTC date) convention.

---

## Acceptance Criteria
*(See `acceptance.json` for machine-readable format.)*

| ID | Description |
|----|-------------|
| AC-001 | Workflow triggers daily at 6:00 AM UTC via cron `0 6 * * *` |
| AC-002 | JIRA section includes In Progress and New-24h issues with key, summary, assignee, status |
| AC-003 | Weather section includes LA forecast with High/Low temperatures |
| AC-004 | News section includes exactly 5 US political headlines with source, date, and URL |
| AC-005 | Sports section includes Dodgers most recent game score, opponent, and series status |
| AC-006 | MTG section includes announcements/spoilers released within 7 days |
| AC-007 | Report filename is `Morning-Brief-YYYY-MM-DD.md` using UTC date |
| AC-008 | Report stored in `.agents-work/2026-05-01_morning-brief-system/` directory |
| AC-009 | All API credentials read from GitHub Secrets; none hardcoded in source code |
| AC-010 | Script generates partial report if any data source fails (graceful degradation) |
| AC-011 | Report metadata footer includes ISO-8601 UTC generation timestamp and per-source status |
| AC-012 | Report renders cleanly in GitHub markdown viewer with no formatting errors |
