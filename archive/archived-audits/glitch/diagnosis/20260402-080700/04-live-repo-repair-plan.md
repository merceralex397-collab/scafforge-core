# Live Repo Repair Plan

## Preconditions

- Repo: /home/pc/projects/Scafforge/livetesting/glitch
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Triage Order

- package_first_count: 1
- subject_repo_follow_up_count: 2
- host_or_manual_prerequisite_count: 1

## Repeated Failure Note

- This repo has already gone through at least one audit-to-repair cycle and still reproduces workflow-layer findings.
- Before another repair run, compare the latest previous diagnosis pack against repair history and explain why those findings survived.
- Do not keep rerunning subject-repo audit until a Scafforge package or process-version change exists.

## Package Changes Required First

### REMED-001

- linked_report_id: CYCLE001
- action_type: Scafforge package work required before the next subject-repo run
- requires_scafforge_repair_afterward: no, not until the package or host prerequisite gap is resolved
- carry_diagnosis_pack_into_scafforge_first: yes
- target_repo: Scafforge package repo
- summary: Before another repair run, compare the latest diagnosis pack against repair_history, identify which findings persisted, and treat repeated deprecated package-managed drift as a repair failure to fix rather than as preserved intent.

## Post-Update Repair Actions

- Route 5 workflow-layer finding(s) into `scafforge-repair` for deterministic managed-surface refresh.

- After deterministic repair, rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

### REMED-004

- linked_report_id: WFLOW012
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Adopt one lease model everywhere: the team leader owns `ticket_claim` and `ticket_release`, specialists work only inside the already-active ticket lease, and only Wave 0 setup work may claim before bootstrap is ready.

### REMED-005

- linked_report_id: WFLOW024
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Document review, QA, smoke-test, and bootstrap failure recovery paths in ticket-execution, and instruct the team leader to follow transition_guidance.recovery_action whenever it is present.

### REMED-006

- linked_report_id: read-only-shell-mutation-loophole
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Keep read-only shell allowlists to inspection commands only and move mutation into write-capable roles.

### REMED-007

- linked_report_id: SKILL001
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Populate every baseline local skill with concrete repo-specific rules and validation commands; generated `.opencode/skills/` files must not retain template filler.

### REMED-008

- linked_report_id: WFLOW006
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Tell the team leader to route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle errors, leave stage artifacts to the owning specialist, and keep slash commands human-only.

## Ticket Follow-Up

### REMED-002

- linked_report_id: EXEC-GODOT-004
- action_type: generated-repo remediation ticket/process repair
- should_scafforge_repair_run: only after managed workflow repair converges
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Run a deterministic `godot --headless --path . --quit` validation during audit and keep the repo blocked until it succeeds or returns an explicit environment blocker instead.
- assignee: implementer
- suggested_fix_approach: Run a deterministic `godot --headless --path . --quit` validation during audit and keep the repo blocked until it succeeds or returns an explicit environment blocker instead.

### REMED-003

- linked_report_id: REF-003
- action_type: generated-repo remediation ticket/process repair
- should_scafforge_repair_run: only after managed workflow repair converges
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Audit local relative import paths and fail when the referenced module file is missing.
- assignee: implementer
- suggested_fix_approach: Audit local relative import paths and fail when the referenced module file is missing.

## Reverification Plan

- After package-side fixes land, run one fresh audit on the subject repo before applying another repair cycle.
- After managed repair, rerun the public repair verifier and confirm restart surfaces, ticket routing, and any historical trust restoration paths match the current canonical state.
- Do not treat restart prose alone as proof; the canonical manifest and workflow state remain the source of truth.

