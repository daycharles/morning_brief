# Architecture — Daily Morning Briefing System

## Overview

The Daily Morning Briefing System is a scheduled GitHub Actions workflow that runs every day at 6:00 AM UTC. It invokes a Python 3.10+ script (`scripts/morning_brief.py`) that concurrently fetches data from five independent APIs (JIRA, Open-Meteo, NewsAPI, MLB Stats API, and Scryfall), assembles the results into a structured markdown report using a report builder module, and writes the dated file to `.agents-work/2026-05-01_morning-brief-system/Morning-Brief-YYYY-MM-DD.md`. All credentials are supplied exclusively through GitHub Secrets as environment variables. Any single fetcher failure causes only that section to be marked as failed in the report metadata footer; the remaining sections are always generated.

---

## Modules / Components

| Module | Responsibility |
|---|---|
| `scripts/morning_brief.py` | Main orchestrator. Validates secrets, dispatches all fetchers via `ThreadPoolExecutor`, collects `FetchResult` objects, calls report builder, writes output file, and determines exit code. |
| `scripts/fetchers/jira_fetcher.py` | Queries JIRA REST API v3 (`/rest/api/3/search`) for In-Progress and New-24h sprint issues. Deduplicates by issue key. Returns structured issue list. |
| `scripts/fetchers/weather_fetcher.py` | Queries Open-Meteo API for LA forecast (lat 34.0522, lon -118.2437). Returns High/Low temps in °F and precipitation probability. |
| `scripts/fetchers/news_fetcher.py` | Queries NewsAPI for top 5 US political headlines. Returns title, source, published date, and URL per article. |
| `scripts/fetchers/sports_fetcher.py` | Queries MLB Stats API for Dodgers (team ID 119) most recent completed game. Returns opponent, score, and series status. |
| `scripts/fetchers/mtg_fetcher.py` | Queries Scryfall API for MTG sets released within the last 7 days. Returns set name, release date, and description. |
| `scripts/formatters/report_builder.py` | Accepts the dict of `FetchResult` objects and renders the final markdown string from a template. Produces the metadata footer. |
| `scripts/utils/http_client.py` | Shared HTTP helper wrapping `requests.Session`. Enforces 10-second timeout and 2-retry exponential backoff (1s, 2s) for transient errors (5xx, connection error, timeout). All calls use HTTPS. |
| `scripts/notifiers/slack_notifier.py` | Posts a summary notification to a Slack channel via Incoming Webhook when report generation completes. Skipped gracefully if `SLACK_WEBHOOK_URL` is not set. |
| `.github/workflows/morning-brief.yml` | GitHub Actions workflow. Triggers on `schedule: cron: '0 6 * * *'` and `workflow_dispatch`. Installs Python deps, exposes secrets as env vars, executes `scripts/morning_brief.py`, commits and pushes the generated report. |

---

## Data Flow

1. **Trigger** — GitHub Actions cron fires at 06:00 UTC (or manual `workflow_dispatch`).
2. **Environment setup** — Workflow runner installs Python dependencies (`requests`), sets env vars from GitHub Secrets.
3. **Startup validation** — `morning_brief.py` calls `validate_config()`: reads `JIRA_API_TOKEN`, `JIRA_HOST`, `NEWSAPI_KEY` from `os.environ`; logs which are missing; raises `SystemExit(1)` if all required secrets absent.
4. **Parallel fetch** — `ThreadPoolExecutor(max_workers=5)` submits all five fetcher functions concurrently. Each fetcher is wrapped in a `try/except` that catches all exceptions and returns a failed `FetchResult`.
5. **Result collection** — Orchestrator collects `Future` results; each yields a `FetchResult(source, status, data, error_message)`.
6. **Report assembly** — `report_builder.build_report(results, generated_at)` renders each section from its `FetchResult`. Missing or failed sections render with a graceful placeholder message. Footer lists per-source status and ISO-8601 UTC timestamp.
7. **File write** — Orchestrator computes UTC date, constructs filename `Morning-Brief-YYYY-MM-DD.md`, writes to `.agents-work/2026-05-01_morning-brief-system/`.
8. **Exit code** — Exit `0` if at least one fetch succeeded; exit `1` if all five failed.
9. **Slack notification** — If `SLACK_WEBHOOK_URL` env var is set, `slack_notifier.post_summary(results, report_filename, generated_at)` is called. Posts a Slack message with report filename, ISO-8601 UTC timestamp, and per-source status (✅ / ❌ for each source). Failure to notify does NOT affect exit code.
10. **Commit & push** — Workflow uses `git add / git commit / git push` to persist the report to the repository.

---

## Interfaces / Contracts

### `FetchResult` dataclass (all fetchers must return this)

```python
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class FetchResult:
    source: str                        # e.g. "jira", "weather", "news", "sports", "mtg"
    status: str                        # "success" | "failed" | "skipped"
    data: Any = None                   # Parsed payload; structure is source-specific
    error_message: Optional[str] = None  # Human-readable error; None on success
```

### Fetcher function signature (all five fetchers)

```python
def fetch(config: dict) -> FetchResult:
    """
    config: dict of resolved env vars / constants relevant to this fetcher.
    Returns: FetchResult — never raises; exceptions are caught internally.
    """
```

### `http_client.get` helper

```python
def get(url: str, *, headers: dict = None, params: dict = None, timeout: int = 10) -> dict:
    """
    Performs GET with 10s timeout and 2-retry exponential backoff.
    Raises requests.HTTPError on non-2xx after retries.
    Always uses HTTPS. Logs retries at WARNING level.
    """
```

### `report_builder.build_report`

```python
def build_report(results: dict[str, FetchResult], generated_at: str) -> str:
    """
    results: mapping of source name -> FetchResult
    generated_at: ISO-8601 UTC string
    Returns: complete markdown string ready to write to disk
    """
```

---

## Directory Layout

```
.
├── .github/
│   └── workflows/
│       └── morning-brief.yml          # Scheduled workflow
├── scripts/
│   ├── morning_brief.py               # Main orchestrator entry point
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── jira_fetcher.py
│   │   ├── weather_fetcher.py
│   │   ├── news_fetcher.py
│   │   ├── sports_fetcher.py
│   │   └── mtg_fetcher.py
│   ├── formatters/
│   │   ├── __init__.py
│   │   └── report_builder.py
│   ├── notifiers/
│   │   ├── __init__.py
│   │   └── slack_notifier.py
│   └── utils/
│       ├── __init__.py
│       └── http_client.py
├── tests/
│   ├── test_jira_fetcher.py
│   ├── test_weather_fetcher.py
│   ├── test_news_fetcher.py
│   ├── test_sports_fetcher.py
│   ├── test_mtg_fetcher.py
│   └── test_report_builder.py
└── .agents-work/
    └── 2026-05-01_morning-brief-system/
        ├── spec.md
        ├── acceptance.json
        ├── architecture.md
        ├── adr/
        │   ├── ADR-001.md
        │   ├── ADR-002.md
        │   ├── ADR-003.md
        │   ├── ADR-004.md
        │   └── ADR-005.md
        └── Morning-Brief-YYYY-MM-DD.md   # Generated daily
```

---

## Error Handling Strategy

- **Per-fetcher isolation**: Each fetcher runs inside its own `try/except Exception` block. Any exception (timeout, HTTP error, JSON parse error, missing key) is caught, logged at `WARNING` level with the source name and error text, and converted into `FetchResult(status="failed", error_message=str(e))`. The exception never propagates to the orchestrator.
- **HTTP retry layer**: `http_client.get` retries up to 2 times with exponential backoff (sleep 1s then 2s) on connection errors, timeouts, and 5xx responses. HTTP 429 is treated as a non-retryable failure with a rate-limit warning log entry.
- **Orchestrator level**: After collecting all `FetchResult` objects, the orchestrator counts successful fetches. If zero succeed → `sys.exit(1)`. Otherwise → `sys.exit(0)`.
- **Logging**: Python `logging` module at `INFO` level for normal flow; `WARNING` for recoverable source failures; `ERROR` for unrecoverable orchestrator failures. Secret values are never interpolated into log messages.

---

## Configuration Strategy

All configuration is read by `morning_brief.py` at startup via `os.environ.get()`:

| Variable | Required | Default | Notes |
|---|---|---|---|
| `JIRA_API_TOKEN` | Yes | — | Bearer token for JIRA REST API v3 |
| `JIRA_HOST` | Yes | — | JIRA instance hostname, e.g. `myorg.atlassian.net` |
| `NEWSAPI_KEY` | Yes | — | API key for newsapi.org |
| `OPENWEATHER_API_KEY` | No | `None` | Optional; enables OpenWeatherMap fallback |
| `SLACK_WEBHOOK_URL` | Optional | None | Slack Incoming Webhook URL; if absent, Slack step is skipped silently. |

Constants (not secrets, hardcoded in module defaults):
- LA coordinates: `lat=34.0522`, `lon=-118.2437`
- Dodgers team ID: `119`
- MTG lookback window: `7` days
- News page size: `5`
- HTTP timeout: `10` seconds
- Retry count: `2`

Startup validation logic: collect all missing required secrets into a list, log each name (not value), and raise `SystemExit(1)` if any required secret is absent so the workflow fails visibly before any API calls are made.

---

## Security Considerations

- **Secrets management**: All credentials stored in GitHub repository Secrets and exposed as env vars by the workflow. Never appear in source code, logs, or the generated report.
- **No secret logging**: Log messages reference secret variable names only (e.g., `"JIRA_API_TOKEN is missing"`), never their values.
- **HTTPS enforcement**: `http_client.get` validates that all URLs begin with `https://` and rejects `http://` schemes.
- **GitHub Actions secret masking**: The Actions runner automatically masks secret values from log output, providing a second layer of protection.
- **Input validation**: API responses are parsed with explicit field access and default fallbacks; no `eval()` or dynamic code execution used.
- **No credential persistence**: The generated markdown report is audited in `report_builder` to ensure no env var values are rendered into output sections.
- **Slack webhook URL**: `SLACK_WEBHOOK_URL` is treated as a secret (GitHub Secret). URL is never logged. Notification POST uses HTTPS (`https://hooks.slack.com/...`). If webhook URL is invalid or returns non-2xx, log a warning and continue — notification failure does not block report delivery.

---

## Testing Strategy

- **Unit tests per fetcher** (`tests/test_*_fetcher.py`): Use `unittest.mock.patch` to mock `http_client.get`. Test: (a) successful parse of a realistic fixture response, (b) HTTP error → `FetchResult(status="failed")`, (c) malformed JSON / missing fields → `FetchResult(status="failed")`, (d) edge-case empty responses (no sprint, off-season, no recent MTG sets).
- **Unit tests for report builder** (`tests/test_report_builder.py`): Supply a mix of successful and failed `FetchResult` objects; assert section headings render, placeholder messages appear for failed sources, metadata footer contains per-source statuses and ISO-8601 timestamp.
- **Unit tests for http_client**: Mock `requests.Session.get`; verify retry count, exponential sleep timing (mock `time.sleep`), and timeout parameter passthrough.
- **Integration test** (optional, marked `@pytest.mark.integration`): Runs against live APIs using test credentials from env; validates full pipeline produces a non-empty markdown file.
- **CI gate**: Unit tests run in the workflow on every push to `main` via a separate `test` job that precedes the `morning-brief` scheduled job.
