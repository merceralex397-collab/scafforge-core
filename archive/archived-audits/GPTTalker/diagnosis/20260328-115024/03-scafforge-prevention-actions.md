# Scafforge Prevention Actions

## Package Changes Required

### ACTION-001

- Change target: installed Scafforge template workflow surfaces already present under `/home/pc/.codex/skills/repo-scaffold-factory/assets/project-template/.opencode/tools/`
- Why it prevents recurrence:
  - The template `ticket_reconcile.ts`, `ticket_create.ts`, and `issue_intake.ts` now provide the missing registry-backed historical reconciliation path and clear the superseded-ticket publish deadlock.
- Safety: `safe`
- Validation:
  - refresh the subject repo with `scafforge-repair`
  - prove the repo-local copies now match the newer template behavior on the `EXEC-012` class of case

### ACTION-002

- Change target: installed workflow guidance in the team-leader prompt and `ticket-execution` skill
- Why it prevents recurrence:
  - The current repo-local and template guidance now explicitly stop repeated lifecycle probing, reserve smoke proof to `smoke_test`, and keep specialist artifact authorship out of the coordinator lane.
- Safety: `safe`
- Validation:
  - preserve these rules during the next managed refresh
  - do not regress them when package templates evolve

## Validation and Test Updates

### ACTION-003

- Change target: Scafforge regression coverage for historical reconciliation
- Why it prevents recurrence:
  - The package should keep a regression that proves a `done + superseded + invalidated + no direct artifacts` ticket can be reconciled from current registered evidence and no longer blocks handoff publication.
- Safety: `safe`
- Validation:
  - run the repair/verification flow against an `EXEC-012`-class fixture
  - confirm `ticket_reconcile` succeeds and the reconciled ticket no longer blocks `handoff_publish`

### ACTION-004

- Change target: transcript-backed workflow-hardening regression coverage
- Why it prevents recurrence:
  - The March 27 transcript failures should remain captured as package regressions so later templates keep the stop-on-repeat, proof-before-PASS, and specialist-owned artifact boundaries.
- Safety: `safe`
- Validation:
  - keep transcript-backed audit fixtures for `SESSION002`, `SESSION004`, `SESSION005`, and `SESSION006`
  - ensure post-package revalidation can distinguish "historical failure already covered by package changes" from "current live blocker still present in the repo"

## Documentation or Prompt Updates

### ACTION-005

- Change target: none newly required by this audit
- Why it prevents recurrence:
  - Current repo-local `.opencode/agents/gpttalker-team-leader.md` and `.opencode/skills/ticket-execution/SKILL.md` already reflect the repaired package contract for the March 27 transcript failures.
- Safety: `safe`
- Validation:
  - keep prompt and skill regeneration aligned with deterministic managed-surface replacement during `scafforge-repair`

## Open Decisions

- No new package design decisions are required from this audit.
- The next action is to refresh the subject repo onto the already-updated package surfaces.
