# Scafforge Process Failures

## Scope

- Subject repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-27T10:35:27Z`
- This report maps the validated current findings from Report 1 back to Scafforge-owned contracts, generated surfaces, and repo-local drift.
- Prior diagnosis context considered:
  - `diagnosis/20260327-053135/`
  - `diagnosis/20260327-053247/`
  - `diagnosis/20260327-053556/`
- Current-state evidence was prioritized over older audit claims and over non-canonical sidecars such as `.opencode/meta/repair-execution.json`.

## Failure Map

### PF1 — Historical follow-up routing still depends on normal live leases

- Linked Report 1 finding: `R2 / WFLOW018`
- Implicated surfaces:
  - `.opencode/plugins/stage-gate-enforcer.ts:150-205`
  - `.opencode/tools/ticket_create.ts:75-109`
  - `.opencode/tools/issue_intake.ts:127-138`
- Ownership class: `generated-repo managed-surface drift`
- Failure type: `current-state repo failure`
- How the workflow allowed it through:
  - the repo tool layer documents guarded historical follow-up creation
  - the plugin still applies ordinary source-ticket lease enforcement underneath that route
  - the resulting contradiction only appears when a completed ticket must spawn a follow-up from current evidence

### PF2 — Public restart and prompt guidance still expose legacy repair gating

- Linked Report 1 finding: `R3 / WFLOW021`
- Implicated surfaces:
  - `START-HERE.md:43-47`
  - `.opencode/state/context-snapshot.md:33-37`
  - `.opencode/state/latest-handoff.md:43-47`
  - `.opencode/commands/resume.md:19`
  - `.opencode/agents/gpttalker-team-leader.md:65`
- Ownership class: `generated-repo managed-surface drift`
- Failure type: `current-state repo failure`
- How the workflow allowed it through:
  - the repo retained the older boolean `handoff_allowed` contract in public guidance
  - the restart and coordinator surfaces therefore still teach models to reason from a field that should be internal or superseded

### PF3 — Open-parent split support exists, but repo ticket data was not migrated to it

- Linked Report 1 finding: `R4 / WFLOW020`
- Implicated surfaces:
  - `tickets/manifest.json:4570-4820`
  - `.opencode/tools/ticket_create.ts:112-119`
  - `.opencode/plugins/stage-gate-enforcer.ts:161-175`
- Ownership class: `repo-specific customization drift`
- Failure type: `current-state repo failure`
- How the workflow allowed it through:
  - a manual reconciliation introduced `EXEC-013` and `EXEC-014` as children of `EXEC-011`
  - later tool support for `split_scope` exists, but the live ticket data was never updated to use that route
  - the repo now mixes a newer tool contract with older queue metadata

### PF4 — Ticket lineage was manually edited without a canonical reconciliation path

- Linked Report 1 finding: `R5 / WFLOW019`
- Implicated surfaces:
  - `tickets/manifest.json:4477-4479`
  - `tickets/manifest.json:4609-4632`
- Ownership class: `repo-specific customization drift`
- Failure type: `current-state repo failure`
- How the workflow allowed it through:
  - the repo has guarded creation tools for new follow-ups, but no first-class reconciliation path for stale lineage after supersession or scope folding
  - the result is lingering orphaned linkage on `EXEC-012`

### PF5 — Bootstrap is still a current blocker, but the package defect is not yet proven

- Linked Report 1 finding: `R1 / ENV002`
- Implicated surfaces:
  - `.opencode/state/workflow-state.json:347-351`
  - `.opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T07-55-04-836Z-environment-bootstrap.md`
  - `.opencode/tools/environment_bootstrap.ts:97-166`
- Ownership class: `repo-specific customization drift`
- Failure type: `both historical chronology failure and current-state repo failure`
- How the workflow allowed it through:
  - the live repo still carries a failed bootstrap proof and a broken validation environment
  - the current managed tool code appears to support dev-extra detection, so the exact package-side defect behind the earlier failed artifact was not re-proven in this non-mutating audit

## Ownership Classification

- `generated-repo managed-surface drift`
  - `R2 / WFLOW018`
  - `R3 / WFLOW021`
- `repo-specific customization drift`
  - `R1 / ENV002`
  - `R4 / WFLOW020`
  - `R5 / WFLOW019`
- `Scafforge package defect`
  - not proven directly from this subject-repo audit, but package-side prevention work is still indicated for `R2` and `R3`
- `subject-repo source bug`
  - none newly validated in this audit pass

## Root Cause Analysis

### 1. This is not pure same-day diagnosis churn

- `diagnosis/20260327-053247/manifest.json` reported `0` findings.
- `diagnosis/20260327-053556/manifest.json` also reported `0` findings.
- The current report therefore is not another identical audit-first loop.
- The live worktree has since drifted, and the repo now contains many modified workflow and ticket surfaces.

### 2. The repo is in a mixed-contract state

- The tool layer already knows about `split_scope`.
- The ticket data for `EXEC-013` and `EXEC-014` still uses `net_new_scope`.
- Restart and prompt surfaces still use the legacy public `handoff_allowed` boolean.
- This is a classic mixed-generation drift pattern: some managed surfaces advanced, while repo-local state and surrounding guidance did not fully follow.

### 3. The repair sidecar is stale, but that is supporting context rather than canonical failure

- `.opencode/meta/repair-execution.json` still records `required_not_run` follow-on stages.
- `docs/process/workflow.md` explicitly says the canonical repair-follow-on truth is `.opencode/state/workflow-state.json`, not the sidecar.
- That means the sidecar contributes to operator confusion, but it is not by itself enough to validate a standalone workflow failure.

### 4. Invocation history confirms repeated bootstrap recovery attempts

- `.opencode/state/invocation-log.jsonl` shows multiple `environment_bootstrap` attempts for `EXEC-014` around `2026-03-27T07:51:46Z`, `07:53:39Z`, and `07:55:04Z`.
- The current failed bootstrap state is therefore not an audit artifact; it reflects a real blocked lane that retrying did not clear.

### 5. The audit script needs human reconciliation for mixed-state repos

- The script correctly found the historical follow-up deadlock and the live bootstrap blocker.
- It overstated `WFLOW010` by assuming the newer outcome-model state already existed in canonical workflow state.
- It also overstated `WFLOW020` by treating missing data migration as missing feature support.
- In this repo, chronology and current file inspection are both required to distinguish package drift from repo-local ticket drift.
