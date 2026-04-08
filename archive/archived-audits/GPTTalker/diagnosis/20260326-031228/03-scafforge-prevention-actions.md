# Scafforge Prevention Actions

## Package Changes Required

### PA-001

- Change target: repo-scaffold-factory managed workflow surfaces for bootstrap gating
- Why it prevents recurrence:
  - failed bootstrap must become a hard lifecycle stop, not a hint
  - `ticket_lookup`, the team-leader prompt, and `ticket-execution` should all say the same thing: run `environment_bootstrap`, refresh state, rerun `ticket_lookup`, then continue
- Safe or intent-changing: `safe`
- Validation:
  - reproduce a repo state with `bootstrap.status = failed` on a non-Wave-0 active ticket
  - confirm every generated next-action surface points only to `environment_bootstrap`

### PA-002

- Change target: `.opencode/plugins/stage-gate-enforcer.ts`, `.opencode/tools/ticket_claim.ts`, `.opencode/tools/_workflow.ts`, planner/team-leader prompt templates, and workflow docs
- Why it prevents recurrence:
  - planning and `plan_review` must have one executable legal path
  - the package must stop telling agents “write the planning artifact first” while the plugin silently requires a bootstrap-ready write lock the planner cannot obtain
- Safe or intent-changing: `safe`
- Validation:
  - create a regression fixture matching the current failure:
    - active non-Wave-0 planning ticket
    - bootstrap failed
    - no current planning artifact
  - confirm the generated repo can either:
    - write/register the planning artifact and move to `plan_review`, or
    - explicitly reject that path and provide one canonical alternative
  - confirm no coordinator workaround is required

### PA-003

- Change target: restart-surface generation and repair verification
- Why it prevents recurrence:
  - `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` must not claim “bootstrap ready” or “deadlock repaired” when canonical workflow state disagrees
- Safe or intent-changing: `safe`
- Validation:
  - mutate bootstrap state, claim/release leases, and increment `state_revision`
  - verify the generated restart surfaces update immediately and match canonical state exactly
  - fail repair validation if drift remains

### PA-004

- Change target: scafforge-audit repeat-cycle diagnosis logic
- Why it prevents recurrence:
  - current diagnosis needs to compare prior packs, repair history, and restart surfaces directly instead of answering only from current-state code or only from the newest transcript
  - repeat audit-to-repair failure must be a first-class diagnosis outcome
- Safe or intent-changing: `safe`
- Validation:
  - add a regression corpus with:
    - one repair-history entry
    - later packs that still show workflow findings
    - stale restart surfaces that overclaim success
  - confirm the audit emits an explicit repeat-cycle finding and cites the persisted workflow defects

### PA-005

- Change target: coordinator and specialist prompt package surfaces
- Why it prevents recurrence:
  - when the workflow becomes contradictory, the coordinator must stop and surface the blocker instead of writing planner-owned or review-owned artifacts
- Safe or intent-changing: `safe`
- Validation:
  - transcript-based regression test using `continuallylocked.md`
  - assert that the diagnosis surfaces flag coordinator-authored specialist artifacts and recommend prompt plus skill regeneration

## Validation and Test Updates

- Add a package regression test for bootstrap-failed planning on non-Wave-0 tickets.
- Add a package regression test for restart-surface drift after bootstrap state changes and lease changes.
- Add a package regression test for `artifact_write` plus `ticket_update` lease behavior during planning.
- Add a transcript-aware audit regression fixture based on `continuallylocked.md`.
- Add a repeat-cycle audit regression fixture using the March 25, 2026 chronology:
  - `diagnosis/20260325-221327`
  - repair at `2026-03-25T22:19:11Z`
  - `diagnosis/20260325-222852`
  - `diagnosis/20260325-223044`

## Documentation or Prompt Updates

- Update the team-leader prompt so bootstrap failure suspends normal lifecycle routing.
- Update the planner prompt or planner workflow contract so it has an executable legal path to persist planning artifacts.
- Update `ticket-execution` so bootstrap failure and planning mutation ownership are described in the same terms the plugin enforces.
- Update workflow docs so lease requirements for planning, review, QA, and closeout are not left to inference.
- Update handoff publication rules so “workflow repaired” and “bootstrap ready” cannot be emitted unless canonical state agrees.

## Open Decisions

- The package needs one explicit planning-write model. Two safe options exist:
  - allow planning and `plan_review` mutations without a bootstrap-ready write lock, or
  - keep the write-lock model but explicitly allow tightly scoped pre-bootstrap planning mutations on the active ticket
- Either option is acceptable; keeping both partially true is what caused the current deadlock.
