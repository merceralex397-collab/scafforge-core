---
description: Start the Glitch autonomous planning cycle from the current canonical state
agent: glitch-team-leader
model: minimax-coding-plan/MiniMax-M2.7
---

Read the canonical project docs in order, resolve the active ticket from `tickets/manifest.json`, verify bootstrap readiness, and begin the internal lifecycle.

Rules:

- Treat this slash command as a human entrypoint only.
- Use agents, tools, plugins, and local skills for the internal autonomous cycle.
- Treat `tickets/manifest.json` and `.opencode/state/workflow-state.json` as canonical state.
- Use `environment_bootstrap` first when bootstrap is missing, failed, or stale.
- Keep the repo on the vertical-slice-first track unless the active ticket explicitly broadens scope.
- Read `ticket_lookup.transition_guidance` before each `ticket_update` call.
- If the same lifecycle error repeats, stop and return a blocker instead of trying alternate stage or status values.
