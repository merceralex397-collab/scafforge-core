# Live Repo Repair Plan

## Preconditions

- Audit scope stayed non-mutating with respect to product code and current managed workflow files. Only the diagnosis pack under `diagnosis/20260328-115024/` was written.
- This is a reconciled `post_package_revalidation` result, not a raw script dump.
- The supplied transcript `sessionlog2703.md` remains the historical causal basis for the earlier package defects, but the current installed package already reflects those transcript-driven hardening changes.

## Package Changes Required First

- No additional package work is required before the next subject-repo action.
- Evidence:
  - installed template `ticket_reconcile.ts` now accepts registry-backed evidence and sets superseded reconciliation targets to `verification_state = "reverified"`
  - installed template `ticket_create.ts` and `issue_intake.ts` now accept current registry artifacts instead of requiring direct historical attachment
  - current repo-local prompt and `ticket-execution` skill already carry the transcript-hardening rules from the earlier audit cycle
- The remaining blocker is that the subject repo has not yet been refreshed onto those newer managed surfaces.

## Post-Update Repair Actions

- Next required action: run `scafforge-repair` against `/home/pc/projects/GPTTalker`.
- Repair scope should refresh the deterministic managed workflow surfaces together:
  - `.opencode/tools/`
  - `.opencode/plugins/`
  - `.opencode/lib/` when the package runner includes shared workflow helpers
  - `docs/process/workflow.md`
  - `docs/process/model-matrix.md`
  - `docs/process/git-capability.md`
  - managed restart-surface publication
- After the deterministic refresh, rerun project-local prompt and skill regeneration if the repair runner does not already do so, so the repo-local prompt/skill layer stays aligned with the repaired tool contract.

## Ticket Follow-Up

### REMED-001

- Linked Report 1 / Report 2 ids: `CURR-001`
- Action type: `generated-repo remediation ticket/process repair`
- Should `scafforge-repair` run: `yes`
- Manual carry into Scafforge dev repo first: `no`
- Target repo: `subject repo`
- Summary:
  - Refresh the repo-local managed surfaces so the current `EXEC-012` historical reconciliation deadlock is removed using the already-updated package logic.

## Reverification Plan

- After `scafforge-repair` lands in the subject repo:
  - rerun exactly one fresh audit or repair-owned verification pass against the updated repo state
  - prove repo-local `ticket_reconcile.ts` no longer carries the `supersededTarget` typo
  - prove the repo-local `ticket_reconcile` supersede path no longer leaves the target ticket `invalidated`
  - prove repo-local `ticket_create.ts` and `issue_intake.ts` accept current registry-backed evidence for historical follow-up routing
  - prove `handoff_publish` is no longer blocked once the historical superseded ticket is reconciled
  - keep `pending_process_verification` truthful; do not collapse that visible state into a package defect if restart surfaces and routing already report it correctly
