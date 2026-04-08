# Live Repo Repair Plan

## Preconditions

- Audit scope stayed non-mutating with respect to product code and managed workflow files. Only the diagnosis pack under `diagnosis/20260328-104330/` was written.
- This pack should be treated as the canonical reconciled result for the current audit run; the raw script findings were manually reconciled against the transcript chronology and current repo state.

## Package Changes Required First

- Yes. The current blocker is a Scafforge package defect, not a subject-repo source bug.
- Move this diagnosis pack into the Scafforge dev repo before recommending another subject-repo repair cycle.
- Package work required first:
  - fix `ticket_reconcile` runtime/semantic defects
  - add a clean path for invalidated historical tickets with missing source artifacts
  - keep closeout publication outside impossible closed-ticket lease assumptions
  - preserve the already-fixed `smoke_test` override/acceptance behavior with regression tests

## Post-Update Repair Actions

- After the package changes land, return to this subject repo and run `scafforge-repair`.
- The repair run should refresh the deterministic managed surfaces together:
  - `.opencode/tools/`
  - `.opencode/plugins/`
  - `.opencode/lib/`
  - `docs/process/workflow.md`
  - `docs/process/model-matrix.md`
  - `docs/process/git-capability.md`
  - managed restart-surface publication
- Do not route repo-specific source tickets first. The current blocker is the workflow layer.

## Ticket Follow-Up

### REMED-001

- Linked finding ids: `CURR-001`
- Action type: safe Scafforge package change
- Target repo: Scafforge package repo
- Should `scafforge-repair` run afterward: yes
- Manual carry required first: yes
- Summary: Restore one legal reconciliation/publish path for invalidated superseded tickets, including the `EXEC-012` class of failure.

### REMED-002

- Linked finding ids: `SESSION-002`
- Action type: safe Scafforge package change
- Target repo: Scafforge package repo
- Should `scafforge-repair` run afterward: yes
- Manual carry required first: yes
- Summary: Keep stop-on-repeat lifecycle behavior enforced by prompt, workflow skill, and regression tests.

### REMED-003

- Linked finding ids: `SESSION-004`, `SESSION-005`
- Action type: safe Scafforge package change
- Target repo: Scafforge package repo
- Should `scafforge-repair` run afterward: yes
- Manual carry required first: yes
- Summary: Keep specialist-owned artifact authorship and proof-before-PASS enforcement covered by package regression tests.

## Reverification Plan

- After package work and subject-repo repair:
  - rerun a transcript-backed audit with `sessionlog2703.md`
  - prove `ticket_reconcile` no longer throws on the `EXEC-012` reconciliation path
  - prove `handoff_publish` can complete with truthful restart surfaces once historical blockers are reconciled
  - confirm the current `smoke_test` behavior still:
    - parses shell-style environment-prefixed overrides
    - prioritizes acceptance-backed smoke commands over heuristics
  - confirm no coordinator-authored planning/implementation/review/QA artifacts are accepted as canonical stage proof
