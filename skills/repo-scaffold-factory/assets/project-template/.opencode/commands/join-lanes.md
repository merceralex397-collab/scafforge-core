---
description: Reconcile completed parallel lanes into one foreground workflow state
agent: __AGENT_PREFIX__-team-leader
model: __PLANNER_MODEL__
---

Inspect completed lane artifacts, reviews, QA status, and lease state, then fold safe parallel outputs back into one foreground synthesis path.

Rules:

- Treat this slash command as a human entrypoint only.
- Require released leases and registered artifacts before treating a lane as join-ready.
- Resolve trust, reverification, and handoff status before closing out the combined result.
