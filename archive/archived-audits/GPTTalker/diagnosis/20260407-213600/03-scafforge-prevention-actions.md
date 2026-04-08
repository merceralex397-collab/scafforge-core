# Scafforge Prevention Actions

- **Subject repo:** `/home/pc/projects/GPTTalker`
- **Diagnosis timestamp:** 2026-04-07T21:36:00Z

## Package Changes Required

### PA-001 — Repair runner must not auto-detect completion for skill-execution stages

- **Change target:** `scafforge-repair` runner, `repair-execution.json` stage-tracking logic
- **Why it prevents recurrence:** Auto-detected completion recorded `opencode-team-bootstrap` and `agent-prompt-engineering` as done without executing those skills. A repair cycle must require explicit skill invocation for any stage in the `agent_team` and `prompt_hardening` categories. Completion should only be recorded after the skill returned a result and the resulting files were confirmed to exist or changed.
- **Safe or intent-changing:** safe
- **Validation:** After a repair run, verify that `.opencode/agents/` files were actually modified by diffing them against the template. A repair stage recorded as complete with unchanged agent files must be treated as a failed stage, not a passed one.

### PA-002 — Add post-repair content-diff check for managed agent surfaces

- **Change target:** `scafforge-repair` post-repair verification step
- **Why it prevents recurrence:** Without a content-diff check, a repair cycle that leaves managed surfaces unchanged can pass all stage-completion gates. A diff between generated agent files and the current template should be required before recording `opencode-team-bootstrap` as complete.
- **Safe or intent-changing:** safe
- **Validation:** Run `audit_repo_process.py` after repair and confirm no agent drift findings remain.

## Validation and Test Updates

### PA-003 — Add `review-audit-bridge` wiring verification to audit script

- **Change target:** `audit_repo_process.py` or `audit_execution_surfaces.py`
- **Why it prevents recurrence:** The audit script did not detect that reviewer-code, reviewer-security, and tester-qa were missing `review-audit-bridge`. A check for `review-audit-bridge` in the skill permissions of reviewer and QA agents would have caught this automatically.
- **Safe or intent-changing:** safe
- **Validation:** Confirm the audit script flags agents missing `review-audit-bridge` in reviewer/QA roles.

### PA-004 — Add compile-check bash allowlist verification to audit script

- **Change target:** `audit_repo_process.py` or `audit_execution_surfaces.py`
- **Why it prevents recurrence:** The audit script did not detect that reviewer-code had no compile-check bash entries. A check that reviewer-code has at least one of `python -m py_compile*`, `cargo check*`, or `tsc --noEmit*` would catch this class of drift.
- **Safe or intent-changing:** safe
- **Validation:** Confirm the audit script flags reviewer-code agents without compile-check bash permissions.

### PA-005 — Exclude `node_modules` from local-import resolution in audit script

- **Change target:** `audit_execution_surfaces.py` or the import-resolution logic in `audit_repo_process.py`
- **Why it prevents recurrence:** The REF-003 false positive was caused by the script scanning `.opencode/node_modules/zod/src/`. The script should exclude all `node_modules` directories from local-import checks.
- **Safe or intent-changing:** safe
- **Validation:** Rerun audit and confirm REF-003 no longer appears.

## Documentation or Prompt Updates

### PA-006 — Document that `ticket_reconcile` was added to ticket-creator template

- **Change target:** `repo-scaffold-factory` template changelog or `opencode-team-bootstrap` skill reference
- **Why it prevents recurrence:** The ticket-creator capability gap (missing `ticket_reconcile`) was invisible because the change wasn't surfaced during repair. A changelog or migration note would make this class of capability addition discoverable.
- **Safe or intent-changing:** safe
- **Validation:** Confirm ticket-creator template includes `ticket_reconcile: allow` and the migration note is present.

## Open Decisions

None. All prevention actions above are safe, non-intent-changing, and do not require operator decisions before repair can proceed.
