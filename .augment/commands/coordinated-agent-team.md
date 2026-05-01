---
description: Run the full multi-agent pipeline (spec → architect → plan → code → review → qa → security → integrate → docs → design → research)
argument-hint: [describe your goal or feature]
---

Use the **coordinated-agent-team** agent to deliver the following goal end-to-end:

$ARGUMENTS

Run the full pipeline in sequence:
1. **Orchestrator** — control workflow and state tracking
2. **Spec Agent** — turn the goal into an unambiguous specification
3. **Architect** — design the architecture and record ADRs
4. **Planner** — create a prioritized task backlog
5. **Coder** — implement each task from the backlog
6. **Reviewer** — structured code review for quality and correctness
7. **QA** — write and run tests, verify acceptance criteria
8. **Security** — identify risks and provide concrete fixes
9. **Integrator** — ensure green CI and repeatable builds
10. **Docs** — create runnable documentation
11. **Designer** — produce UX/UI design specs
12. **Researcher** — investigate patterns and best practices

After each stage, output `✅ Stage N complete — [summary]` before proceeding.
If a stage does not apply, output `⏭ Stage N skipped — [reason]` and continue.
