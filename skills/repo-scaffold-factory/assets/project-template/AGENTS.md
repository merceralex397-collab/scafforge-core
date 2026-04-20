# __PROJECT_NAME__ Agent Rules

This file is the project-local instruction source for this repository.

If this file conflicts with any global AI instruction file, this file wins for this repo.

## Operating priorities

1. Read `START-HERE.md` first.
2. Treat `docs/spec/CANONICAL-BRIEF.md` as the project source of truth.
3. Use `tickets/manifest.json` as the machine-readable work queue.
4. Use `.opencode/state/workflow-state.json` for transient stage approval, bootstrap, coordinator-owned lease, and reverification state.
5. Treat the stage-specific artifact directories as the canonical stage-proof body locations.
6. Use the process version and verification state in `.opencode/state/workflow-state.json` before trusting old completed work.
7. Keep the repo signposted and deterministic for weaker models.
8. Follow the internal stage gates: plan -> plan review -> implement -> review -> QA -> smoke test -> closeout.

## Truth hierarchy

- `docs/spec/CANONICAL-BRIEF.md` owns durable project facts and decisions
- `tickets/manifest.json` owns machine queue state and registered artifact metadata
- `tickets/BOARD.md` is the derived human queue board
- `.opencode/state/workflow-state.json` owns the transient foreground stage, per-ticket approval state, bootstrap readiness, coordinator-owned lane leases, and the active process-version plus post-migration verification state
- `.opencode/state/plans/`, `.opencode/state/implementations/`, `.opencode/state/reviews/`, `.opencode/state/qa/`, `.opencode/state/smoke-tests/`, and `.opencode/state/handoffs/` own stage artifact bodies
- `.opencode/state/artifacts/registry.json` owns the cross-stage artifact registry
- `.opencode/meta/bootstrap-provenance.json` owns bootstrap and repair provenance
- `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces

## Required read order

1. `START-HERE.md`
2. `AGENTS.md`
3. `docs/spec/CANONICAL-BRIEF.md`
4. `docs/process/workflow.md`
5. `docs/process/agent-catalog.md`
6. `docs/process/model-matrix.md`
7. `docs/process/git-capability.md`
8. `tickets/README.md`
9. `tickets/manifest.json`
10. `tickets/BOARD.md`

## Rules

- Every substantive change should map to a ticket.
- Do not implement before an approved plan exists.
- Do not treat slash commands as the autonomous workflow.
- Prefer local tools, plugins, and project skills over prompt-only improvisation.
- Keep queue status coarse: `todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`.
- Keep plan approval in workflow state and artifacts, not in ticket status.
- Keep historical completion separate from current trust. Use `resolution_state` and `verification_state` instead of mutating ticket history.
- Treat `tickets/BOARD.md` as a derived human view, not a second state machine.
- Use ticket tools and workflow-state instead of raw file edits for stage transitions.
- Treat `ticket_lookup.transition_guidance` as the canonical description of the next legal stage move.
- If the same lifecycle-tool error repeats, stop and return a blocker instead of probing alternate stage or status values.
- Only Wave 0 setup work may claim a write-capable lease before bootstrap is ready.
- The team leader owns `ticket_claim` and `ticket_release`. Specialists work only inside the already-active lease for the current ticket.
- Default to one active write lane at a time. Use lane leases only for bounded parallel work instead of overlapping unmanaged edits.
- Keep `START-HERE.md`, `tickets/BOARD.md`, and `tickets/manifest.json` aligned with the canonical sources that feed them.
- Use Ubuntu-safe commands and paths in generated project docs unless the project explicitly says otherwise.
- Keep the default orchestration shape as one visible team leader with a single-lane-first posture. Only fan out into bounded parallel lanes when the brief and ticket graph prove the work is safely disjoint.
- Treat manager or section-leader hierarchies as advanced project-specific customization, not a first-class scaffold profile.
- Treat `.opencode/meta/bootstrap-provenance.json` as the canonical source for the repo's process-contract version; workflow state mirrors that contract for active execution and verification routing.
- Only create migration follow-up tickets from backlog-verifier findings during an active process-verification window.
- Use `ticket_create(source_mode=split_scope)` when an open parent ticket needs child decomposition; do not encode that as `net_new_scope` or `post_completion_issue`.
- Use `ticket_reconcile` to repair stale or contradictory ticket lineage from evidence instead of editing `tickets/manifest.json` directly.
- Treat `.opencode/meta/bootstrap-provenance.json` as provenance only, not as a mutable resume or queue surface.
- Use `smoke_test` to generate smoke-test proof. Do not fabricate smoke-test PASS artifacts through generic artifact tools.
- Use `smoke_test(smoke_deferred_until=[ticket_ids])` when a ticket's acceptance smoke test requires functionality from a later ticket that is not yet done. Do NOT use `command_override` to scope-narrow around missing functionality.

## Machine / Clone Check

**Bootstrap state is machine-specific.** The bootstrap status stored in `.opencode/state/workflow-state.json` and published in `START-HERE.md` was verified on a specific machine. It is NOT valid on a different machine or a fresh clone.

**Before starting any ticket work on a new or different machine:**

1. Check `.opencode/state/workflow-state.json` `.bootstrap.environment_fingerprint` — if it is set but does not match the current host, bootstrap is stale.
2. Run `environment_bootstrap` to re-verify prerequisites on this host.
3. Tools will throw `"Bootstrap stale. Run environment_bootstrap."` if you try to run smoke tests without re-verifying. This is correct behavior — it means bootstrap needs to re-run, NOT that anything is broken.
4. Only after `environment_bootstrap` succeeds on this machine can ticket lifecycle work resume normally.

Do not skip this check if you cloned the repo from remote, switched machines, or if the CI environment differs from the development environment.
