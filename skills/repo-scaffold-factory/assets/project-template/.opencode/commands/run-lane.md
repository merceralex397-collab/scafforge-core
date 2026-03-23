---
description: Run one bounded write-capable lane through the lease-based workflow
agent: __AGENT_PREFIX__-team-leader
model: __PLANNER_MODEL__
---

Choose one ready ticket lane, claim the required lease, delegate bounded implementation, then return control to the team leader for synthesis.

Rules:

- Treat this slash command as a human entrypoint only.
- Use `ticket_claim` and `ticket_release` for write-capable lane ownership.
- Prefer `__AGENT_PREFIX__-lane-executor` for bounded parallel implementation.
- Do not overlap write-capable work across lanes with conflicting paths or dependencies.
