---
description: Resume the current autonomous cycle using the latest repo state
agent: __AGENT_PREFIX__-team-leader
model: __FULL_PLANNER_MODEL__
---

Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first. Use `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` only as derived restart surfaces that must agree with canonical state.

Rules:

- Reconfirm the active ticket and stage.
- Reconfirm `repair_follow_on.outcome`; only `managed_blocked` is a primary blocker for ordinary ticket lifecycle work.
- Treat the active open ticket as the primary lane even when historical reverification is pending.
- Reconfirm bootstrap readiness and whether the current environment fingerprint has gone stale.
- Reconfirm the process-version state and whether post-migration verification is pending.
- Reconfirm whether post-repair follow-on work still blocks handoff or restart.
- Reconfirm whether any completed tickets are reopened, suspect, or pending reverification.
- If bootstrap is `missing`, `failed`, or `stale`, run `environment_bootstrap` before normal lifecycle routing.
- If repeated bootstrap proofs show the same command trace but it still contradicts the repo's declared dependency layout, stop retrying and route a managed bootstrap defect instead of bypassing bootstrap with raw package-manager commands.
- If `repair_follow_on.outcome` is `managed_blocked`, stop ordinary lifecycle routing and surface the repair blocker from canonical state instead of trying to continue ticket execution.
- Regenerate the derived restart surfaces if they disagree with canonical state or look stale.
- Reconfirm the required artifact proof for the next stage before continuing.
- Reconfirm whether the team leader must claim a write lease before the next specialist writes an artifact body, code, or handoff text.
- Read `ticket_lookup.transition_guidance` before changing ticket stage or status.
- If a lifecycle-tool error repeats, stop and return a blocker instead of probing alternate stage or status values.
- Continue the required internal stage sequence instead of skipping ahead.
