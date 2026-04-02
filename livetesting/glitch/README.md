# Glitch

## Overview

Glitch is a Godot-based Android 2D action-platformer set inside a collapsing digital simulation. The game’s core hook is a fair but unpredictable glitch system that mutates physics, hazards, and room logic while preserving readable telegraphs and touch-friendly movement.

This repository is the scaffolded operating framework for building that game. It starts with canonical design truth, a ticketed execution model, and an OpenCode agent/tool layer tuned for a Godot mobile game project rather than a generic app repo.

## Start Here

1. Read `START-HERE.md`
2. Read `AGENTS.md`
3. Read `docs/spec/CANONICAL-BRIEF.md`
4. Read `docs/process/workflow.md`
5. Read `docs/process/agent-catalog.md`
6. Read `tickets/manifest.json`
7. Read `tickets/BOARD.md`

## Repository Layout

- `glitch_game_design_document.md` is the original source design document captured during intake.
- `docs/spec/CANONICAL-BRIEF.md` owns the normalized product truth.
- `docs/process/` holds the generated workflow contract, team catalog, and model/process notes.
- `tickets/` holds the machine queue, derived board, and individual ticket briefs.
- `.opencode/agents/` holds the project-specific autonomous team.
- `.opencode/skills/` holds repo-local operating guidance for Godot, Android validation, and Glitch-specific design rules.
- `.opencode/tools/` and `.opencode/plugins/` hold the managed workflow surface.
- `.opencode/state/workflow-state.json` owns transient lifecycle, bootstrap, and lease state.

## Product Direction

- Platform: Android
- Engine: Godot
- Style: side-on 2D action-platformer
- Core differentiator: glitch-driven systemic instability with readable telegraphs
- First build target: a playable Startup Sector vertical slice with baseline movement, glitch events, hazards, checkpoints, and mobile controls

## Truth Hierarchy

- `docs/spec/CANONICAL-BRIEF.md` owns durable project facts, goals, constraints, and open questions.
- `tickets/manifest.json` owns machine-readable queue state and registered artifact metadata.
- `tickets/BOARD.md` is the derived human queue board.
- `.opencode/state/workflow-state.json` owns transient stage, approval, bootstrap readiness, and lease state.
- `.opencode/state/plans/`, `.opencode/state/implementations/`, `.opencode/state/reviews/`, `.opencode/state/qa/`, `.opencode/state/smoke-tests/`, and `.opencode/state/handoffs/` own canonical stage artifact bodies.
- `.opencode/state/artifacts/registry.json` owns cross-stage artifact registration metadata.
- `.opencode/meta/bootstrap-provenance.json` owns scaffold provenance.
- `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces.

## Workflow Notes

- Treat this as a one-active-lane-first repo unless a ticket is explicitly marked safe for parallel work.
- Use `ticket_lookup.transition_guidance` as the canonical next-step explainer before any stage change.
- Bootstrap readiness is a hard pre-lifecycle gate. When bootstrap is not ready, run `environment_bootstrap` first.
- `smoke_test` is the only legal producer of smoke-test artifacts.
- Ticket acceptance should prefer executable Godot validation commands over narrative claims.

## Expected Validation Direction

Once the Godot project exists, tickets should converge on commands in this family:

- `godot --headless --path . --quit`
- `godot --headless --path . --import`
- repo-local smoke commands for specific scenes, systems, or test harnesses when a ticket defines them

Until the engine project is created, missing runtime prerequisites should be surfaced as blockers rather than worked around with fabricated PASS artifacts.
