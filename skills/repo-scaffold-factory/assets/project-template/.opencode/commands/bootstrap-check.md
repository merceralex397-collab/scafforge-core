---
description: Verify and refresh environment bootstrap readiness for the current repo
agent: __AGENT_PREFIX__-team-leader
model: __PLANNER_MODEL__
---

Resolve the current workflow state, inspect bootstrap readiness, and route the environment bootstrap lane if runtime, dependency, or verification prerequisites are missing or stale.

Rules:

- Treat this slash command as a human entrypoint only.
- Use `ticket_lookup` and `environment_bootstrap` instead of manual dependency improvisation.
- Keep bootstrap proof global to the repo and register the resulting artifact.
- If bootstrap is already ready, summarize the current proof and stop.
