# Live Repo Repair Plan

## Preconditions

- This diagnosis run stayed non-mutating except for the diagnosis pack itself.
- 18 prior diagnosis packs were reviewed before writing this plan.
- Current canonical repo truth:
  - active ticket: `EXEC-007`
  - stage: `planning`
  - bootstrap: `failed`
  - bootstrap proof: `.opencode/state/artifacts/history/exec-007/bootstrap/2026-03-25T23-02-26-471Z-environment-bootstrap.md`
  - active lease: `EXEC-007`, owner `gpttalker-team-leader`, `write_lock: false`
  - `pending_process_verification: true`
- This repo should not go straight into another ordinary repair run yet because the latest diagnosis shows a still-live package-level workflow contradiction.

## Package Changes Required First

### RP-001

- Linked findings: `R1-F2`, `R1-F3`, `R1-F4`, `R1-F5`
- Action type: `safe Scafforge package change`
- Target repo: `Scafforge package repo`
- Should `scafforge-repair` run now in this repo: `no`
- Must the user manually carry this diagnosis pack into the Scafforge dev repo first: `yes`
- Required package work:
  - make bootstrap failure a hard short-circuit across `ticket_lookup`, the team-leader prompt, and `ticket-execution`
  - align planning and `plan_review` mutations with the actual lease/write-lock model so the planning path is executable during bootstrap recovery
  - prevent coordinator-authored specialist artifacts from becoming the fallback behavior under contradiction
  - make repeat-cycle audit logic and restart-surface publication fail closed when post-repair evidence still shows workflow risk

### RP-002

- Linked findings: `R1-F1`, `R1-F5`
- Action type: `safe Scafforge package change`
- Target repo: `Scafforge package repo`
- Should `scafforge-repair` run now in this repo: `no`
- Must the user manually carry this diagnosis pack into the Scafforge dev repo first: `yes`
- Required package work:
  - regenerate and validate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical manifest/workflow state after every workflow mutation or repair
  - block “workflow repaired” and “bootstrap ready” claims when canonical state still says otherwise

## Post-Update Repair Actions

### RP-003

- Linked findings: `R1-F1`, `R1-F2`, `R1-F3`, `R1-F4`, `R1-F5`
- Action type: `generated-repo remediation ticket/process repair`
- Target repo: `subject repo`
- Should `scafforge-repair` run: `yes`, but only after package changes from `RP-001` and `RP-002` exist locally
- Must the user manually carry this diagnosis pack into the Scafforge dev repo first: `yes`
- Repair intent:
  - refresh the managed workflow surfaces in GPTTalker
  - regenerate the derived restart surfaces
  - remove the planning/bootstrap lease contradiction
  - leave product code and accepted project intent unchanged

### RP-004

- Linked findings: `R1-F1`, `R1-F2`
- Action type: `generated-repo remediation ticket/process repair`
- Target repo: `subject repo`
- Should `scafforge-repair` run: `no` for the verification itself; this is the required post-repair check
- Must the user manually carry this diagnosis pack into the Scafforge dev repo first: `yes`
- Required verification after repair:
  - rerun `environment_bootstrap`
  - confirm `.opencode/state/workflow-state.json` records `bootstrap.status = ready`
  - confirm `START-HERE.md` and `.opencode/state/context-snapshot.md` reference the current bootstrap proof and current lease state
  - rerun `scafforge-audit` and confirm `R1-F1` through `R1-F5` are gone

### RP-005

- Linked findings: `R1-F6`
- Action type: `generated-repo remediation ticket/process repair`
- Target repo: `subject repo`
- Should `scafforge-repair` run: `not for the source fixes themselves`
- Must the user manually carry this diagnosis pack into the Scafforge dev repo first: `no`, but package-side process repair should happen first
- Repair intent:
  - continue the already-existing Wave 10 source work (`EXEC-007` through `EXEC-011`) only after the workflow layer is trustworthy again

## Ticket Follow-Up

- Do not create duplicate source tickets for the existing 13 failing tests; keep using `EXEC-007` through `EXEC-011`.
- Package-side follow-up proposals:
  - `REMED-001`: bootstrap-first short-circuit plus planning-write contract alignment
  - `REMED-002`: restart-surface regeneration and overclaim guardrails
  - `REMED-003`: repeat-cycle audit regression and coordinator-ownership hardening
- Subject-repo follow-up proposals after managed repair:
  - `REMED-004`: rerun backlog verification until `pending_process_verification` is cleared
  - `REMED-005`: resume existing Wave 10 source tickets only after post-repair audit is clean

## Reverification Plan

1. Manually carry `diagnosis/20260326-031228/` into the Scafforge dev repo.
2. Implement the package changes from `RP-001` and `RP-002`.
3. Add the prevention regressions described in Report 3.
4. Return to `/home/pc/projects/GPTTalker` and run `scafforge-repair`.
5. In GPTTalker, rerun `environment_bootstrap`.
6. Confirm these repo-local truths before resuming source work:
   - bootstrap is `ready`
   - restart surfaces match canonical workflow state
   - the active planning ticket has one executable legal path into `plan_review`
   - no coordinator-authored specialist artifact is needed to get there
7. Rerun `scafforge-audit` with `continuallylocked.md` and confirm the workflow-layer findings are gone.
8. Only then continue Wave 10 source remediation and backlog reverification.
