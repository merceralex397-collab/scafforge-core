# Scafforge Prevention Actions

## Package Changes Required

### PA-1 — Remove normal source-ticket lease enforcement from historical follow-up routes

- Change target: Scafforge workflow package
- Prevents recurrence of: `R2 / WFLOW018`
- Why it prevents recurrence:
  - `ticket_create(process_verification|post_completion_issue)` and `issue_intake` will stop deadlocking on completed tickets
  - the tool contract and the stage gate will finally agree on historical evidence routing
- Safe or intent-changing: `safe`
- Validation:
  - add tests proving these routes succeed from a completed source ticket without requiring that source ticket's live write lease

### PA-2 — Move public repair-follow-on guidance to one outcome-based contract

- Change target: Scafforge workflow package
- Prevents recurrence of: `R3 / WFLOW021`
- Why it prevents recurrence:
  - `/resume`, restart-surface generation, and coordinator prompts will stop teaching models to reason from `handoff_allowed`
  - a single public outcome model reduces stale-reasoning branches for weaker agents
- Safe or intent-changing: `safe`
- Validation:
  - generated `START-HERE.md`, `.opencode/state/context-snapshot.md`, `.opencode/state/latest-handoff.md`, `/resume`, and team-leader prompt must contain no public `handoff_allowed` guidance

### PA-3 — Add a canonical ticket-graph reconciliation path

- Change target: Scafforge workflow package
- Prevents recurrence of: `R4 / WFLOW020`, `R5 / WFLOW019`
- Why it prevents recurrence:
  - manual manifest edits will no longer be the only way to repair stale `source_ticket_id`, `follow_up_ticket_ids`, and superseded-child lineage
  - split-child migrations and superseded follow-up cleanup can become atomic and repeatable
- Safe or intent-changing: `safe`
- Validation:
  - reconcile tests should cover:
    - open-parent split migration to `split_scope`
    - superseded child retained as source-linked follow-up
    - parent-child link repair after manual drift

### PA-4 — Harden the audit package against false positives in mixed-contract repos

- Change target: Scafforge audit package
- Prevents recurrence of: rejected script claim `WFLOW010` and amended script claim `WFLOW020`
- Why it prevents recurrence:
  - the audit should distinguish “legacy but internally consistent” from “derived surfaces disagree with canonical state”
  - the audit should not report missing `split_scope` support when the code already supports it and only ticket data is stale
- Safe or intent-changing: `safe`
- Validation:
  - add audit fixtures for:
    - legacy `repair_follow_on` boolean state that is still internally consistent
    - repos where `split_scope` exists in tools but older ticket records remain `net_new_scope`

## Validation and Test Updates

### VT-1 — Add workflow tests for historical follow-up routing

- Change target: package tests for stage gate and ticket tools
- Why it prevents recurrence:
  - it catches the exact contradiction currently present between historical follow-up tools and lease enforcement
- Safe or intent-changing: `safe`
- Validation:
  - direct tool tests for `ticket_create(process_verification)`
  - direct tool tests for `ticket_create(post_completion_issue)`
  - direct tool tests for `issue_intake`

### VT-2 — Add restart-surface contract tests

- Change target: package tests for handoff publication and resume-facing guidance
- Why it prevents recurrence:
  - it prevents public `handoff_allowed` leakage and restart-surface drift
- Safe or intent-changing: `safe`
- Validation:
  - snapshot tests for generated restart surfaces and `/resume`

### VT-3 — Add end-to-end bootstrap tests for uv repos with dev extras

- Change target: package tests for `environment_bootstrap`
- Why it prevents recurrence:
  - this repo is uv-managed and depends on dev extras for `pytest` and `ruff`
  - the bootstrap layer should prove it installs and verifies those executables in the repo-local environment
- Safe or intent-changing: `safe`
- Validation:
  - fixture repo with `[project.optional-dependencies].dev`
  - expected bootstrap command includes `--extra dev`
  - expected post-bootstrap probes include repo-local `pytest` and `ruff`

## Documentation or Prompt Updates

### DP-1 — Update resume and coordinator guidance to stop using public `handoff_allowed`

- Change target:
  - `.opencode/commands/resume.md`
  - team-leader prompt template
  - docs-handoff template
- Why it prevents recurrence:
  - it removes the current stale reasoning branch from the most influential agent-facing surfaces
- Safe or intent-changing: `safe`
- Validation:
  - grep generated surfaces for `handoff_allowed` after regeneration

### DP-2 — Document split-scope migration and historical lineage reconciliation

- Change target:
  - workflow docs
  - tooling docs
  - ticket-system docs
- Why it prevents recurrence:
  - weaker models need an explicit procedure for open-parent decomposition and later graph cleanup
- Safe or intent-changing: `safe`
- Validation:
  - repo docs must explain when `split_scope` is required and when reconciliation is required

### DP-3 — Clarify that `repair-execution.json` is supporting evidence only

- Change target:
  - workflow docs
  - resume-facing docs
- Why it prevents recurrence:
  - it reduces confusion when the repair sidecar is stale but workflow-state is canonical
- Safe or intent-changing: `safe`
- Validation:
  - generated docs must explicitly state that `.opencode/state/workflow-state.json` owns repair-follow-on truth

## Open Decisions

### OD-1

- Decision: should Scafforge add a first-class `ticket_reconcile` tool, or keep reconciliation as a repair-only internal action?
- Why it matters:
  - this repo now demonstrates that guarded creation alone is not enough once ticket lineage drifts after supersession or split migration

### OD-2

- Decision: should `repair_follow_on.outcome` be persisted canonically in workflow state, or derived at render time for backward compatibility?
- Why it matters:
  - the current audit false positive came from assuming a newer outcome model that this repo has not yet fully adopted
