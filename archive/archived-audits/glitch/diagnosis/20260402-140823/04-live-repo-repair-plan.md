# Live Repo Repair Plan

## Preconditions

- Repo: /home/pc/projects/Scafforge/livetesting/glitch
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Triage Order

- package_first_count: 1
- subject_repo_follow_up_count: 3
- host_or_manual_prerequisite_count: 1

## Package Changes Required First

### REMED-004

- linked_report_id: WFLOW025
- action_type: Scafforge package work required before the next subject-repo repair run
- requires_scafforge_repair_afterward: no, not until the package or host prerequisite gap is resolved
- carry_diagnosis_pack_into_scafforge_first: yes
- target_repo: Scafforge package repo
- summary: For Godot Android repos, always create `ANDROID-001` in lane `android-export` for repo-local export surfaces and `RELEASE-001` in lane `release-readiness` for debug APK proof. Do not let generic polish tickets stand in for release ownership.

## Post-Update Repair Actions

- Route 1 workflow-layer finding(s) into `scafforge-repair` for deterministic managed-surface refresh.

### REMED-005

- linked_report_id: WFLOW026
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Keep one shared artifact verdict extractor that accepts plain and markdown-emphasized verdict labels, then route ticket_lookup and ticket_update through that shared parser instead of treating explicit review or QA verdicts as unclear.

## Ticket Follow-Up

### REMED-001

- linked_report_id: REF-003
- action_type: generated-repo remediation ticket/process repair
- should_scafforge_repair_run: only after managed workflow repair converges
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Audit local relative import paths and fail when the referenced module file is missing.
- assignee: implementer
- suggested_fix_approach: Audit local relative import paths and fail when the referenced module file is missing.

### REMED-002

- linked_report_id: SESSION001
- action_type: generated-repo remediation ticket/process repair
- should_scafforge_repair_run: only after managed workflow repair converges
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: When session logs are supplied, audit chronology first: separate stale resume state from later evidence, then explain any final summary that outruns the executed commands before reconciling current repo state.
- assignee: implementer
- suggested_fix_approach: When session logs are supplied, audit chronology first: separate stale resume state from later evidence, then explain any final summary that outruns the executed commands before reconciling current repo state.

### REMED-003

- linked_report_id: SESSION003
- action_type: generated-repo remediation ticket/process repair
- should_scafforge_repair_run: only after managed workflow repair converges
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.
- assignee: implementer
- suggested_fix_approach: Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.

## Reverification Plan

- After package-side fixes land, run one fresh audit on the subject repo before applying another repair cycle.
- After managed repair, rerun the public repair verifier and confirm restart surfaces, ticket routing, and any historical trust restoration paths match the current canonical state.
- Do not treat restart prose alone as proof; the canonical manifest and workflow state remain the source of truth.

