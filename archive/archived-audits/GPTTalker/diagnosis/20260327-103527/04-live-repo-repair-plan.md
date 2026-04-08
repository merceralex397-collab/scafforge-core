# Live Repo Repair Plan

## Preconditions

- Subject repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-27T10:35:27Z`
- Audit mode: non-mutating
- No repo or product-code edits were made by this diagnosis run.
- This diagnosis applies to the current dirty worktree, not to a clean historical commit.
- Full executable reverification is blocked until bootstrap is restored.

## Package Changes Required First

### RP-1

- Linked findings: `R2 / WFLOW018`
- Action type: `safe Scafforge package change`
- Target repo: `Scafforge package repo`
- `scafforge-repair` should run: `yes, after package update lands`
- Manual carry of this diagnosis pack first: `yes`
- Action:
  - repair historical follow-up routing so completed source tickets do not require ordinary live write leases
  - refresh the generated stage gate and related tool surfaces together

### RP-2

- Linked findings: `R3 / WFLOW021`
- Action type: `safe Scafforge package change`
- Target repo: `Scafforge package repo`
- `scafforge-repair` should run: `yes, after package update lands`
- Manual carry of this diagnosis pack first: `yes`
- Action:
  - refresh the public repair-follow-on contract so prompts, restart surfaces, and `/resume` stop routing from `handoff_allowed`
  - keep any legacy boolean parsing internal only

### RP-3

- Linked findings: rejected script claim `WFLOW010`, amended script claim `WFLOW020`
- Action type: `safe Scafforge package change`
- Target repo: `Scafforge package repo`
- `scafforge-repair` should run: `no immediate subject-repo repair from this item alone`
- Manual carry of this diagnosis pack first: `yes`
- Action:
  - harden the audit package so mixed-contract repos do not produce false “derived drift” or false “missing split support” findings

## Post-Update Repair Actions

### RR-1

- Linked findings: `R2`, `R3`
- Action type: `generated-repo remediation ticket/process repair`
- Target repo: `subject repo`
- `scafforge-repair` should run: `yes`
- Manual carry of this diagnosis pack first: `after package updates land`
- Action:
  - rerun `scafforge-repair` against this repo to refresh managed workflow surfaces
  - specifically refresh:
    - stage gate
    - resume guidance
    - restart-surface generation
    - team-leader prompt

### RR-2

- Linked findings: `R4 / WFLOW020`
- Action type: `generated-repo remediation ticket/process repair`
- Target repo: `subject repo`
- `scafforge-repair` should run: `optional if the repair flow already includes graph reconciliation; otherwise manual repo repair is still needed`
- Manual carry of this diagnosis pack first: `no`
- Action:
  - reconcile the `EXEC-011` split so `EXEC-013` and `EXEC-014` use the canonical open-parent source mode
  - decide whether `EXEC-011` should stay `blocked` or become open/non-foreground under the current split model

### RR-3

- Linked findings: `R5 / WFLOW019`
- Action type: `generated-repo remediation ticket/process repair`
- Target repo: `subject repo`
- `scafforge-repair` should run: `optional`
- Manual carry of this diagnosis pack first: `no`
- Action:
  - reconcile `EXEC-012` lineage against `EXEC-008`
  - either restore the parent follow-up link intentionally or supersede/remove the stale linkage through one canonical repair path

### RR-4

- Linked findings: `R1 / ENV002`
- Action type: `generated-repo remediation ticket/process repair`
- Target repo: `subject repo`
- `scafforge-repair` should run: `no`
- Manual carry of this diagnosis pack first: `no`
- Action:
  - rerun `environment_bootstrap`
  - do not continue lifecycle verification until repo-local `pytest` and `ruff` are available again

## Ticket Follow-Up

### REMED-001

- Linked findings: `R2 / WFLOW018`
- Proposed target repo: `Scafforge package repo`
- Proposal:
  - create a package-side workflow fix ticket for historical follow-up lease gating

### REMED-002

- Linked findings: `R3 / WFLOW021`
- Proposed target repo: `Scafforge package repo`
- Proposal:
  - create a package-side workflow fix ticket for public repair-follow-on outcome migration

### REMED-003

- Linked findings: `R4 / WFLOW020`, `R5 / WFLOW019`
- Proposed target repo: `subject repo`
- Proposal:
  - create a repo-local process repair ticket to reconcile `EXEC-011`, `EXEC-013`, `EXEC-014`, and `EXEC-012` lineage without changing product intent

### REMED-004

- Linked findings: `R1 / ENV002`
- Proposed target repo: `subject repo`
- Proposal:
  - create or route an operator follow-up to restore bootstrap proof and repo-local test tools before further lifecycle work

## Reverification Plan

1. Apply the Scafforge package changes for `R2` and `R3` first.
2. Return to this repo and run `scafforge-repair` once those package changes are available.
3. Reconcile ticket lineage for `EXEC-011`, `EXEC-013`, `EXEC-014`, and `EXEC-012`.
4. Rerun `environment_bootstrap`.
5. Verify:
   - `.venv/bin/pytest --version`
   - `.venv/bin/ruff --version`
   - no public restart or prompt surface references `handoff_allowed`
   - historical follow-up routes no longer require a completed ticket's live write lease
   - `EXEC-013` and `EXEC-014` no longer use `net_new_scope`
6. Run one fresh subject-repo audit after repair. Do not loop through more subject-repo audits before the package-side changes land.
