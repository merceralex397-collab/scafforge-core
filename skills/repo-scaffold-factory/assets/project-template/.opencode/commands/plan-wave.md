---
description: Select the next safe execution wave and parallel lane candidates
agent: __AGENT_PREFIX__-team-leader
model: __FULL_PLANNER_MODEL__
---

Read the active backlog, dependency graph, bootstrap readiness, and trust state, then choose the next foreground ticket and any safe parallel lane candidates.

Rules:

- Treat this slash command as a human entrypoint only.
- Only select parallel candidates that are `parallel_safe: true`, `overlap_risk: low`, dependency-clean, and credible for distinct lane ownership.
- Keep one visible team leader coordinating fan-out and fan-in.
