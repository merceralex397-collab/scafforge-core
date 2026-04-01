---
description: Start the autonomous planning cycle for the current repo state
agent: __AGENT_PREFIX__-team-leader
model: __FULL_PLANNER_MODEL__
---

Read the canonical project docs in order, resolve the active ticket from `tickets/manifest.json`, verify bootstrap readiness, and begin the internal lifecycle.

Rules:

- Treat this slash command as a human entrypoint only.
- Use agents, tools, plugins, and local skills for the internal autonomous cycle.
- Treat `tickets/manifest.json` and `.opencode/state/workflow-state.json` as canonical state; `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart views.
- Do not implement before a reviewed plan exists.
- Use `ticket_lookup`, `ticket_update`, and registered artifacts instead of raw file edits for stage control.
- Read `ticket_lookup.transition_guidance` before each `ticket_update` call.
- If the same lifecycle error repeats, stop and return a blocker instead of trying alternate stage or status values.
- Use `environment_bootstrap` first when bootstrap is missing, failed, or stale. only Wave 0 setup work may claim a write-capable lease before bootstrap is ready.
- The team leader owns `ticket_claim` and `ticket_release`. The team leader claims and releases write leases. Specialists author artifacts and code only under the already-active lease for the current ticket.
- Default to one active write lane at a time. Use lease-based execution only for bounded parallel work instead of overlapping unmanaged edits.
- Route post-completion defects through `issue_intake`, not ad hoc ticket history edits.
- Route open-parent decomposition through `ticket_create(source_mode=split_scope)` and stale lineage repair through `ticket_reconcile`.
- Update ticket state and handoff artifacts as the cycle progresses.
