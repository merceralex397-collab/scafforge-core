# __PROJECT_NAME__

## Overview

This repository was scaffolded for a deterministic, ticketed, agent-friendly workflow.

## Start Here

1. Read `START-HERE.md`
2. Read `AGENTS.md`
3. Read `docs/spec/CANONICAL-BRIEF.md`
4. Read `docs/process/workflow.md`
5. Read `docs/process/model-matrix.md`
6. Read `tickets/README.md`
7. Read `tickets/manifest.json`
8. Read `tickets/BOARD.md`

## Repository Layout

- `docs/` for canonical process and spec material
- `tickets/` for the work queue and machine-readable state
- `.opencode/` for project-local OpenCode agents, tools, plugins, commands, and skills
- `opencode.jsonc` for project-local OpenCode configuration
- `.opencode/state/workflow-state.json` for transient stage state, plan approval, bootstrap readiness, coordinator-owned lease state, and the active copy of process-version verification flags

## Truth hierarchy

- `docs/spec/CANONICAL-BRIEF.md` owns durable project facts, constraints, accepted decisions, and open questions
- `tickets/manifest.json` owns machine queue state and registered artifact metadata
- `tickets/BOARD.md` is the derived human queue board
- `.opencode/state/workflow-state.json` owns transient stage, approval, bootstrap, trust-routing, and lease state
- `.opencode/state/plans/`, `.opencode/state/implementations/`, `.opencode/state/reviews/`, `.opencode/state/qa/`, `.opencode/state/smoke-tests/`, and `.opencode/state/handoffs/` store canonical stage artifact bodies
- `.opencode/state/artifacts/registry.json` stores artifact metadata
- `.opencode/meta/bootstrap-provenance.json` records how this operating layer was generated and later repaired
- `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces

## Workflow Notes

- `tickets/manifest.json` is the machine source of queue state.
- registered artifact metadata belongs on the owning ticket entry in `tickets/manifest.json` and is mirrored into `.opencode/state/artifacts/registry.json`
- `tickets/BOARD.md` is a derived human board.
- `.opencode/commands/` are human entrypoints only; the autonomous workflow lives in tools, plugins, skills, and canonical state.
- Ticket `status` stays coarse and queue-oriented.
- Historical completion and current trust are separate. `status` stays queue-oriented, while `resolution_state` and `verification_state` tell you whether completed work is still trusted.
- Plan approval, bootstrap readiness, and coordinator-owned lease state live in workflow state plus registered stage artifacts, not in ticket status.
- Only Wave 0 setup work may claim a write-capable lease before bootstrap is ready.
- Default to one active write lane at a time. Use lane leases only for bounded parallel work that is explicitly safe and disjoint.
- Use `.opencode/meta/bootstrap-provenance.json` as the canonical process-contract record, and use the process-version fields in workflow state to decide whether completed tickets need post-migration verification before they are trusted.
- Use `.opencode/skills/model-operating-profile/SKILL.md` when shaping prompts or delegation for the selected downstream model profile.
