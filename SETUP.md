# Daily Morning Brief — Setup Guide

This guide explains how to configure and run the automated Daily Morning Briefing system.

---

## Table of Contents

1. [GitHub Secrets Configuration](#github-secrets-configuration)
2. [Step-by-Step Setup](#step-by-step-setup)
3. [Running Manually via workflow_dispatch](#running-manually-via-workflow_dispatch)
4. [Local Development with .env](#local-development-with-env)
5. [Generated Report Format](#generated-report-format)
6. [Troubleshooting](#troubleshooting)

---

## GitHub Secrets Configuration

The system reads all credentials from GitHub Repository Secrets. **No credentials are hardcoded in source code.**

### Required Secrets

| Secret Name | Description | How to Obtain |
|---|---|---|
| `JIRA_API_TOKEN` | JIRA REST API Bearer token for authentication | Generate at [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `JIRA_HOST` | Your JIRA instance hostname (e.g. `company.atlassian.net`) | Your JIRA Cloud URL without `https://` |
| `NEWSAPI_KEY` | NewsAPI.org API key for political headline fetching | Register at [newsapi.org](https://newsapi.org/register) (free tier available) |

### Optional Secrets

| Secret Name | Description | Behavior When Absent |
|---|---|---|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL for delivery notifications | Silently skipped; report is still generated |

> ⚠️ **Security Note:** Secret values are never logged or stored in the generated report. GitHub Actions automatically masks secret values in all workflow logs.

---

## Step-by-Step Setup

### 1. Fork or Clone the Repository

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

### 2. Add GitHub Secrets

1. Navigate to your repository on GitHub.
2. Click **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret** for each secret below:

**Required:**
- Name: `JIRA_API_TOKEN` → Value: your Atlassian API token
- Name: `JIRA_HOST` → Value: `your-company.atlassian.net` (no `https://`)
- Name: `NEWSAPI_KEY` → Value: your NewsAPI.org key

**Optional:**
- Name: `SLACK_WEBHOOK_URL` → Value: `https://hooks.slack.com/services/...`

### 3. Verify the Workflow

The workflow runs automatically every day at **6:00 AM UTC** via:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'
```

The generated report is committed to `.agents-work/2026-05-01_morning-brief-system/` in the repository.

---

## Running Manually via workflow_dispatch

You can trigger the workflow at any time from the GitHub UI:

1. Go to your repository on GitHub.
2. Click **Actions** → **Daily Morning Brief**.
3. Click **Run workflow** → select branch → click **Run workflow**.

The workflow will run immediately and commit the generated report.

---

## Local Development with .env

To run the script locally:

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a `.env` file

Create `.env` at the repo root (already in `.gitignore`):

```env
JIRA_API_TOKEN=your-api-token-here
JIRA_HOST=your-company.atlassian.net
NEWSAPI_KEY=your-newsapi-key-here
# Optional:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 3. Load env vars and run

```bash
# On Linux/macOS:
export $(cat .env | xargs) && python scripts/morning_brief.py

# On Windows (PowerShell):
Get-Content .env | ForEach-Object { $k,$v = $_ -split '=',2; [System.Environment]::SetEnvironmentVariable($k,$v) }
python scripts/morning_brief.py
```

### 4. Run unit tests

```bash
# Unit tests (no live API calls):
python -m pytest tests/ -v --ignore=tests/test_integration.py

# Integration test (requires real credentials in environment):
python -m pytest tests/test_integration.py -v -m integration
```

---

## Generated Report Format

The system generates a markdown file named `Morning-Brief-YYYY-MM-DD.md` saved to:

```
.agents-work/2026-05-01_morning-brief-system/Morning-Brief-YYYY-MM-DD.md
```

The report contains the following sections:

| Section | Content |
|---|---|
| 🗂️ JIRA Sprint Status | In-progress sprint issues and new issues (last 24h) as a markdown table |
| ☀️ Weather — Los Angeles | Daily High/Low °F and precipitation probability |
| 📰 Political Headlines | Top 5 US political headlines with source, date, and URL |
| ⚾ LA Dodgers | Most recent completed game result and series status |
| 🃏 Magic: The Gathering | MTG sets released in the last 7 days |
| 📋 Report Metadata | Generation timestamp (UTC) and per-source success/failed status |

> If any data source fails, that section renders a graceful placeholder message. The report is still generated and committed.

---

## Troubleshooting

### Missing Secrets — Script exits with code 1

**Symptom:** Workflow fails immediately; log shows `"All required secrets missing — cannot proceed"`.

**Fix:** Verify all 3 required GitHub Secrets are set: `JIRA_API_TOKEN`, `JIRA_HOST`, `NEWSAPI_KEY`.

---

### JIRA Authentication Failure (HTTP 401)

**Symptom:** JIRA section shows `⚠️ JIRA data unavailable: 401`.

**Fixes:**
- Regenerate your Atlassian API Token at [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens).
- Confirm `JIRA_HOST` is the hostname only (e.g., `company.atlassian.net`) without `https://`.
- Confirm the token has access to the JIRA project you are querying.

---

### API Rate Limiting (HTTP 429)

**Symptom:** A source section shows `⚠️ ... data unavailable: 429`.

**Behavior:** Rate-limited requests are not retried (to avoid worsening the situation). The affected source is marked as failed; other sources complete normally.

**Fix:** Check the API vendor's rate limit documentation. NewsAPI free tier is limited to 100 requests/day.

---

### Report Not Committed After Run

**Symptom:** Workflow completes successfully but no new file appears in the repository.

**Fix:** Verify the workflow job has `permissions: contents: write`. Check that the `git push || true` step did not silently fail due to a branch protection rule.

---

### Running Locally — ModuleNotFoundError

**Symptom:** `ModuleNotFoundError: No module named 'scripts'` when running `python scripts/morning_brief.py`.

**Fix:** Run from the repository root directory (where `scripts/` is a subdirectory):

```bash
cd /path/to/your-repo  # must be the repo root
python scripts/morning_brief.py
```
