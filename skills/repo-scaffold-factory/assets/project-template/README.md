# __PROJECT_NAME__

## Overview

This repository was scaffolded for a deterministic, ticketed, agent-friendly workflow.

## Start Here

1. Read `START-HERE.md`
2. Read `AGENTS.md`
3. Read `docs/spec/CANONICAL-BRIEF.md`
4. Read `docs/process/workflow.md`
5. Read `docs/process/git-capability.md`
6. Read `tickets/BOARD.md`

## Repository Layout

- `docs/` for canonical process and spec material
- `tickets/` for the work queue and machine-readable state
- `.opencode/` for project-local OpenCode agents, tools, plugins, commands, and skills
- `opencode.jsonc` for project-local OpenCode configuration
- `.opencode/state/workflow-state.json` for transient stage state, plan approval, bootstrap readiness, lease ownership, and the active copy of process-version verification flags

## Truth hierarchy

- `docs/spec/CANONICAL-BRIEF.md` owns durable project facts, constraints, accepted decisions, and open questions
- `tickets/manifest.json` owns machine queue state and registered artifact metadata
- `tickets/BOARD.md` is the derived human queue board
- `.opencode/state/workflow-state.json` owns transient stage, approval, bootstrap, trust-routing, and lease state
- `.opencode/state/plans/`, `.opencode/state/implementations/`, `.opencode/state/reviews/`, `.opencode/state/qa/`, `.opencode/state/smoke-tests/`, and `.opencode/state/handoffs/` store canonical stage artifact bodies
- `.opencode/state/artifacts/registry.json` stores artifact metadata
- `.opencode/meta/bootstrap-provenance.json` records how this operating layer was generated and later repaired
- `START-HERE.md` is the derived restart surface

## Workflow Notes

- `tickets/manifest.json` is the machine source of queue state.
- registered artifact metadata belongs on the owning ticket entry in `tickets/manifest.json` and is mirrored into `.opencode/state/artifacts/registry.json`
- `tickets/BOARD.md` is a derived human board.
- Ticket `status` stays coarse and queue-oriented.
- Historical completion and current trust are separate. `status` stays queue-oriented, while `resolution_state` and `verification_state` tell you whether completed work is still trusted.
- Plan approval, bootstrap readiness, and lease ownership live in workflow state plus registered stage artifacts, not in ticket status.
- Write-capable parallel work must run through lane leases rather than overlapping unmanaged edits.
- Use `.opencode/meta/bootstrap-provenance.json` as the canonical process-contract record, and use the process-version fields in workflow state to decide whether completed tickets need post-migration verification before they are trusted.
