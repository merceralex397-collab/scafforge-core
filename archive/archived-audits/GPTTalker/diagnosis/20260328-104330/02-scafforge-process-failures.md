# Scafforge Process Failures

## Scope

- Subject repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-28T10:43:30Z`
- Failure map reconciled from:
  - current managed workflow surfaces
  - canonical ticket/workflow state
  - supplied transcript `sessionlog2703.md`

## Failure Map

### CURR-001 -> WFLOW018 / WFLOW019 / WFLOW022 cluster

- Linked Report 1 finding id: `CURR-001`
- Implicated surfaces:
  - `.opencode/tools/ticket_reconcile.ts`
  - `.opencode/plugins/stage-gate-enforcer.ts`
  - `.opencode/tools/ticket_create.ts`
  - `.opencode/tools/issue_intake.ts`
  - `.opencode/tools/handoff_publish.ts`
- Ownership class: Scafforge package defect
- How the workflow allowed the issue through:
  - The generated toolchain has no clean path for an already-closed, invalidated, superseded ticket that also lacks source artifacts.
  - `ticket_reconcile` is live-broken by a variable-name typo and, even on the happy path, re-writes the target into `verification_state: invalidated`.
  - `ticket_create(post_completion_issue)` and `issue_intake` both insist that the source ticket reference the evidence artifact, which fails for `EXEC-012` because its artifact list is empty.
  - `handoff_publish` blocks any done ticket that remains invalidated, so the dead state becomes externally visible at closeout time instead of remaining a harmless bookkeeping mismatch.

### SESSION-002

- Linked Report 1 finding id: `SESSION-002`
- Implicated surfaces:
  - coordinator prompt contract
  - lifecycle transition guidance
  - repo-local workflow explainer
- Ownership class: Scafforge package defect
- How the workflow allowed the issue through:
  - The historical session kept retrying repeated lifecycle blockers instead of surfacing one blocker path and stopping.
  - Current prompt surfaces now contain explicit stop-on-repeat instructions, which suggests this part was at least partially repaired after the logged session.

### SESSION-004

- Linked Report 1 finding id: `SESSION-004`
- Implicated surfaces:
  - stage-proof contract
  - QA proof expectations
  - coordinator evidence discipline
- Ownership class: Scafforge package defect
- How the workflow allowed the issue through:
  - The historical session allowed reasoning and artifact prose to outrun executable proof when command execution was unavailable.
  - Later deterministic smoke recovery corrected the outcome, but the earlier workflow still permitted premature PASS-style language.

### SESSION-005

- Linked Report 1 finding id: `SESSION-005`
- Implicated surfaces:
  - coordinator prompt
  - stage artifact ownership contract
  - invocation-log / transcript audit expectations
- Ownership class: Scafforge package defect
- How the workflow allowed the issue through:
  - The coordinator was still able to manufacture specialist-owned stage proof directly instead of remaining on routing and stage transitions only.
  - Current prompt surfaces now forbid this explicitly, so the historical failure should be covered by package regression tests.

## Ownership Classification

- `CURR-001`: Scafforge package defect
- `SESSION-002`: Scafforge package defect
- `SESSION-004`: Scafforge package defect
- `SESSION-005`: Scafforge package defect

## Root Cause Analysis

- The current high-severity live defect is not ordinary repo customization drift. It is a generated workflow-contract bug spanning reconciliation, follow-up intake, lease gating, and closeout publication.
- The historical transcript findings show that earlier package generations did not reliably enforce:
  - stop-on-repeat lifecycle behavior
  - specialist-owned artifact authorship
  - proof-before-PASS evidence discipline
- The current repo already contains some later prompt/tool improvements, but the `EXEC-012` deadlock proves the package repair line is still incomplete.
