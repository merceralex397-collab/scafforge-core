# Glitch Agent Rules

This file is the project-local instruction source for the Glitch game repo.

If this file conflicts with a broader host instruction file, this file wins for work inside this repository.

## Operating Priorities

1. Read `START-HERE.md` first.
2. Treat `docs/spec/CANONICAL-BRIEF.md` as the durable product truth.
3. Treat `tickets/manifest.json` as the machine queue source of truth.
4. Treat `.opencode/state/workflow-state.json` as the transient lifecycle, bootstrap, lease, and approval state.
5. Keep the first playable vertical slice as the near-term product target unless a ticket explicitly broadens scope.
6. Preserve the game’s fairness contract: glitches must be readable, telegraphed, and recoverable.
7. Keep the repo signposted and deterministic for weaker downstream models.
8. Follow the internal stage order exactly: `planning -> plan_review -> implementation -> review -> qa -> smoke-test -> closeout`.

## Project-Specific Rules

- This is a Godot Android game project, not a generic web or service repo.
- Default implementation language is GDScript unless canonical truth later changes that decision.
- Mobile readability and touch control usability outrank ornamental complexity.
- The glitch system is the core mechanic, but the baseline platforming feel must remain trustworthy.
- Hand-authored room structure with curated glitch variation is preferred over full procedural randomness.
- Early development should bias toward a Startup Sector vertical slice that proves movement, hazard readability, checkpoint flow, and glitch signaling.

## Truth Hierarchy

- `docs/spec/CANONICAL-BRIEF.md` owns durable project facts and accepted decisions.
- `tickets/manifest.json` owns machine queue state and registered artifact metadata.
- `tickets/BOARD.md` is the derived human queue board.
- `.opencode/state/workflow-state.json` owns the transient foreground stage, per-ticket approval state, bootstrap readiness, coordinator-owned lane leases, and process-version state.
- `.opencode/state/plans/`, `.opencode/state/implementations/`, `.opencode/state/reviews/`, `.opencode/state/qa/`, `.opencode/state/smoke-tests/`, and `.opencode/state/handoffs/` own stage artifact bodies.
- `.opencode/state/artifacts/registry.json` owns the cross-stage artifact registry.
- `.opencode/meta/bootstrap-provenance.json` owns scaffold provenance.
- `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces.

## Required Read Order

1. `START-HERE.md`
2. `AGENTS.md`
3. `docs/spec/CANONICAL-BRIEF.md`
4. `docs/process/workflow.md`
5. `docs/process/agent-catalog.md`
6. `docs/process/model-matrix.md`
7. `tickets/README.md`
8. `tickets/manifest.json`
9. `tickets/BOARD.md`

## Workflow Rules

- Every substantive change should map to a ticket.
- Do not implement before an approved plan exists.
- Treat `ticket_lookup.transition_guidance` as the canonical next-step summary.
- Keep queue status coarse and queue-oriented.
- Keep plan approval in workflow state and artifacts, not in ticket status.
- Use ticket tools and workflow-state instead of raw file edits for stage transitions.
- If the same lifecycle-tool error repeats, stop and surface the blocker instead of probing alternate stage or status values.
- Bootstrap readiness is a hard pre-lifecycle gate. If bootstrap is not ready, route `environment_bootstrap` before normal lifecycle work.
- Only Wave 0 setup work may claim a write-capable lease before bootstrap is ready.
- `smoke_test` is the only legal producer of smoke-test artifacts.
- Commands are human entrypoints only; autonomous work stays inside agents, tools, plugins, and local skills.

## Evidence Rules

- Godot validation should be executable where possible: headless startup, import checks, test harnesses, or scene-level smoke commands.
- Do not claim that a scene, script, or system is valid without command output in the stage artifact.
- If a validation command cannot run because Godot, Android tooling, or project files are missing, return a blocker instead of inventing success.
- Review and QA findings should prioritize correctness, regressions, and validation gaps before maintainability commentary.
