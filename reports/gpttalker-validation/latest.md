# GPTTalker Migration Validation

- generated_at: `2026-04-22T02:24:30.772954+00:00`
- source_repo_path: `C:\Users\PC\AppData\Local\Temp\scafforge-gpttalker-fixture-w2aeh6e_\restart-surface-drift-after-repair`

## Source Repo State

```text
git status unavailable for C:\Users\PC\AppData\Local\Temp\scafforge-gpttalker-fixture-w2aeh6e_\restart-surface-drift-after-repair: fatal: not a git repository (or any of the parent directories): .git
```

## Scenario: control

- migration_policy: `current`
- migration_state: `current`
- repair_follow_on_outcome: `managed_blocked`
- handoff_allowed: `False`
- migration_history_count_before: `0`
- migration_history_count_after: `0`
- repair_history_count_before: `0`
- repair_history_count_after: `1`
- provenance_process_version_after: `7`
- workflow_process_version_after: `7`
- pending_process_verification_after: `True`
- restart_surface_truth: `start_here_process_version_7=True, start_here_pending_process_verification=True, context_process_version_7=True, context_pending_process_verification=True, latest_handoff_process_version_7=True, latest_handoff_pending_process_verification=True`
- audit_codes: `WFLOW035, WFLOW010, WFLOW008`

### Blocking Reasons
- project-skill-bootstrap must still run: Repo-local skills still contain generic placeholder/model drift that must be regenerated with project-specific content.
- Post-repair verification failed repair-contract consistency checks: placeholder_local_skills_survived_refresh.

## Scenario: safe-legacy-upgrade

- migration_policy: `safe_auto_upgrade`
- migration_state: `migrated`
- repair_follow_on_outcome: `managed_blocked`
- handoff_allowed: `False`
- migration_history_count_before: `0`
- migration_history_count_after: `1`
- repair_history_count_before: `0`
- repair_history_count_after: `1`
- provenance_process_version_after: `7`
- workflow_process_version_after: `7`
- pending_process_verification_after: `True`
- restart_surface_truth: `start_here_process_version_7=True, start_here_pending_process_verification=True, context_process_version_7=True, context_pending_process_verification=True, latest_handoff_process_version_7=True, latest_handoff_pending_process_verification=True`
- audit_codes: `WFLOW035, WFLOW010`

### Blocking Reasons
- project-skill-bootstrap must still run: Repo-local skills still contain generic placeholder/model drift that must be regenerated with project-specific content.
- Post-repair verification failed repair-contract consistency checks: placeholder_local_skills_survived_refresh.

## Scenario: too-old-escalation

- migration_policy: `too_old`
- migration_state: `blocked`
- repair_follow_on_outcome: `managed_blocked`
- handoff_allowed: `False`
- migration_history_count_before: `0`
- migration_history_count_after: `0`
- repair_history_count_before: `0`
- repair_history_count_after: `0`
- provenance_process_version_after: `5`
- workflow_process_version_after: `5`
- pending_process_verification_after: `False`
- restart_surface_truth: `start_here_process_version_7=True, start_here_pending_process_verification=False, context_process_version_7=True, context_pending_process_verification=False, latest_handoff_process_version_7=True, latest_handoff_pending_process_verification=False`
- audit_codes: `WFLOW035, WFLOW010`

### Blocking Reasons
- Legacy contract migration requires operator approval before an unsafe or structurally inconsistent repo can be mutated.

### Escalation
- attempted_operation: `legacy-contract-migration`
- process_version 5 is too old for the safe migration window (minimum supported legacy version is 6).

## Scenario: structural-mismatch-escalation

- migration_policy: `structurally_unsafe`
- migration_state: `blocked`
- repair_follow_on_outcome: `managed_blocked`
- handoff_allowed: `False`
- migration_history_count_before: `0`
- migration_history_count_after: `0`
- repair_history_count_before: `0`
- repair_history_count_after: `0`
- provenance_process_version_after: `6`
- workflow_process_version_after: `6`
- pending_process_verification_after: `False`
- restart_surface_truth: `start_here_process_version_7=True, start_here_pending_process_verification=False, context_process_version_7=True, context_pending_process_verification=False, latest_handoff_process_version_7=True, latest_handoff_pending_process_verification=False`
- audit_codes: `WFLOW035, WFLOW010`

### Blocking Reasons
- Legacy contract migration requires operator approval before an unsafe or structurally inconsistent repo can be mutated.

### Escalation
- attempted_operation: `legacy-contract-migration`
- workflow state and repair_follow_on disagree on process_version

## Interpretation

- Control and safe-legacy scenarios validate the current migration path and the upgrade proof trail.
- Blocked scenarios demonstrate that too-old or structurally inconsistent legacy repos fail closed before ordinary repair mutation.
- Safe upgrades record migration history separately from repair history so later repair runs can distinguish migrated repos from untouched legacy ones.
