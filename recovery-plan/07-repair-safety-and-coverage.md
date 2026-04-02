# Phase 07: Repair Safety and Coverage

**Priority:** P1 — High
**Depends on:** Phase 03 (audit must produce richer findings before repair can consume them)
**Goal:** Make managed repair non-destructive, provenance-tracked, and code-quality-aware

---

## Problem Statement

The current repair flow has three issues:

1. **Destructive replacement:** `apply_repo_process_repair.py` uses `shutil.rmtree(target)` + `shutil.copytree(source, target)` to replace managed surfaces. No backup, no diff, no recovery option.

2. **No code-quality ticket generation:** Repair handles workflow surfaces but does not create remediation tickets when audit finds code issues. Code problems are reported in the diagnosis pack but never enter the ticket queue.

3. **Python-only post-repair verification:** Post-repair verification only checks Python execution. After Phase 03's stack adapters exist, repair should use them.

---

## Fix 07-A: Non-Destructive Replacement with Backup

### Evidence

**File:** `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
**Problem:** The function that replaces managed surfaces does `shutil.rmtree(path)` then `shutil.copytree(source, path)`. If the copy fails midway (disk full, permission error, interrupted), the target directory is gone with no recovery.

### Required Changes

1. **Before any `rmtree`:** Create a backup of the target directory:
   ```python
   backup_path = target + ".repair-backup-" + timestamp
   shutil.copytree(target, backup_path)
   ```

2. **After successful replacement:** Remove the backup (or keep it based on a `preserve_backups` flag).

3. **On failure:** Log the error, restore from backup, and report failure:
   ```python
   try:
       shutil.rmtree(target)
       shutil.copytree(source, target)
   except Exception as e:
       if os.path.exists(backup_path):
           shutil.copytree(backup_path, target)
       raise RepairFailure(f"Managed surface replacement failed: {e}. Restored from backup.")
   ```

4. **Add a diff summary** between old and new managed surfaces. Before the replacement, compute a file-level diff (which files changed, added, removed) and include it in the repair provenance record. This helps diagnose what the repair actually changed.

### Files to Change

- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`

---

## Fix 07-B: Repair Provenance Enhancement

### Evidence

**File:** `.opencode/meta/bootstrap-provenance.json` (in generated repos)
**Problem:** Repair provenance records what was repaired but not what the original state was, what diff was applied, or what verification was run.

### Required Changes

1. **Extend the provenance record** written by `record_repair_stage_completion.py`:
   ```json
   {
     "repair_id": "...",
     "timestamp": "...",
     "repair_type": "managed-surface-replacement|code-quality-remediation|...",
     "surfaces_replaced": ["..."],
     "diff_summary": {
       "files_added": [],
       "files_removed": [],
       "files_modified": []
     },
     "audit_findings_addressed": ["WFLOW006", "WFLOW012"],
     "verification_passed": true,
     "verification_findings": [],
     "process_version_before": "...",
     "process_version_after": "..."
   }
   ```

2. **In `record_repair_stage_completion.py`:** Accept the diff summary and verification results as inputs and include them in the provenance record.

### Files to Change

- `skills/scafforge-repair/scripts/record_repair_stage_completion.py`

---

## Fix 07-C: Code-Quality Ticket Generation from Repair

### Problem

When `scafforge-repair` runs after an audit, it handles workflow surface repairs but drops code-quality findings on the floor. The repair skill does not create tickets for code issues.

### Required Changes

1. **In `scafforge-repair/SKILL.md`:** After completing managed-surface repairs, if the audit findings include EXEC or REF findings:
   - Invoke `ticket-pack-builder` in remediation mode (Phase 06-B)
   - Pass the EXEC/REF findings as input
   - `ticket-pack-builder` creates remediation tickets in the subject repo
   - Record the created ticket IDs in the repair provenance

2. **Do NOT have repair fix code itself.** Repair creates tickets; agents fix code through the normal ticket lifecycle. This preserves the separation between workflow repair and code changes.

3. **In the managed repair flow (AGENTS.md):** After step 2 (`scafforge-repair` runs), add: "If code-quality findings were present, `scafforge-repair` creates remediation tickets via `ticket-pack-builder` before the flow continues."

### Files to Change

- `skills/scafforge-repair/SKILL.md`

---

## Fix 07-D: Stack-Aware Post-Repair Verification

### Evidence

**File:** `skills/scafforge-repair/scripts/apply_repo_process_repair.py` and related scripts
**Problem:** Post-repair verification currently only checks Python execution. After Phase 03, stack-specific execution auditors exist but repair doesn't use them.

### Required Changes

1. **In post-repair verification:** After managed-surface replacement, run the full execution audit suite (Phase 03-A's `run_stack_execution_audits()`) against the repaired repo.

2. **Fail the repair** if the stack-specific execution audit finds CRITICAL findings that were NOT present in the pre-repair state. This catches regressions introduced by the repair itself.

3. **Accept pre-existing CRITICAL findings** that were already present before repair — these should become remediation tickets (Fix 07-C), not repair failures.

4. **Write verification results** to the repair provenance (Fix 07-B).

### Implementation Approach

Post-repair verification should compare pre-repair findings with post-repair findings:
- **New findings** (not in pre-repair set): repair regression → fail the repair
- **Disappeared findings** (in pre-repair but not post-repair): repair fixed something → record as success
- **Persistent findings** (in both sets): not repair's fault → create remediation tickets

### Files to Change

- `skills/scafforge-repair/scripts/apply_repo_process_repair.py` (or a new `verify_repair.py`)

---

## Fix 07-E: Repair Escalation for Intent-Changing Fixes

### Evidence

**File:** `skills/scafforge-repair/SKILL.md`
**Problem:** The skill says it should "escalate intent-changing repairs" but does not define what counts as intent-changing or how escalation works.

### Required Changes

1. **Define intent-changing criteria:**
   - Adding or removing an agent from the team
   - Changing the bootstrap command
   - Altering the truth hierarchy (moving canonical ownership between files)
   - Changing the ticket lifecycle stages
   - Adding or removing workflow tools
   - Changing skill allowlists on agents

2. **Define escalation mechanism:**
   - Stop the repair flow
   - Write an escalation record to `.opencode/state/repair-escalation.json` with: what was attempted, why it's intent-changing, what the user should decide
   - Surface the escalation clearly in the handoff brief
   - Do NOT apply the intent-changing repair automatically

3. **In `scafforge-repair/SKILL.md`:** Add the criteria and mechanism as explicit sections.

### Files to Change

- `skills/scafforge-repair/SKILL.md`

---

## Summary Checklist

| Fix | Done? |
|-----|-------|
| 07-A: Non-destructive replacement with backup | |
| 07-A: Diff summary before replacement | |
| 07-B: Enhanced repair provenance records | |
| 07-C: Code-quality ticket generation from repair | |
| 07-D: Stack-aware post-repair verification | |
| 07-D: Pre/post finding comparison | |
| 07-E: Intent-changing repair escalation | |
