---
description: Pull Jira issues by JQL and produce a structured investigation report (triage, codebase cross-reference, recommended next actions)
argument-hint: [JQL query]
---

Use the **jira-investigator** agent to investigate the following Jira issues:

JQL: `$ARGUMENTS`

Run the full investigation workflow:

1. **Fetch** — Query Jira using the JQL above via the `jira` tool (`/search/jql`). Request fields: summary, description, status, priority, assignee, reporter, labels, components, issuetype, created, updated, comment.
2. **Triage** — Classify each issue by severity (Critical / High / Medium / Low), type (Bug / Feature / Task / Spike / Debt), and flag blockers or missing acceptance criteria.
3. **Investigate** — For each issue, read the full description and comments. Use `codebase-retrieval` to identify affected files, modules, or components in this codebase.
4. **Report** — Output a structured Markdown report:

```
# Jira Investigation Report
JQL: <query>
Date: <today>
Total Issues: <N>

## Executive Summary
<2-5 sentence overview>

## Issue Breakdown
| Key | Summary | Type | Priority | Status | Affected Area |
|-----|---------|------|----------|--------|---------------|

## Critical / High Issues
<Detail each with description, affected code, and recommended next action>

## Ambiguities & Gaps
<Issues with missing context, unclear acceptance criteria, or blocked dependencies>

## Recommended Pipeline Seed
<What Spec Agent and Planner should focus on first>
```

If the JQL returns 0 results, report that and suggest a revised query.
Do not modify any Jira issues or codebase files — this is a read-only investigation.
