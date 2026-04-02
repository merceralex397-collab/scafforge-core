---
description: Resume the Glitch autonomous cycle from the latest canonical state
agent: glitch-team-leader
model: minimax-coding-plan/MiniMax-M2.7
---

Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first. Use `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` only as derived restart surfaces.

Rules:

- reconfirm the active ticket and stage
- reconfirm bootstrap readiness and the next required action
- if bootstrap is `missing`, `failed`, or `stale`, run `environment_bootstrap` before normal lifecycle routing
- keep the active open ticket as the primary foreground lane
- read `ticket_lookup.transition_guidance` before changing ticket stage or status
- continue the required internal stage sequence instead of skipping ahead
