# Scafforge Prevention Actions

## Package Changes Required

### ACTION-001

- Change target: transcript-backed audit coverage in `scafforge-audit`
- Why it prevents recurrence:
  - The deterministic audit pass missed a live contradiction between canonical workflow state and derived restart prose.
  - Audit reconciliation should include explicit checks for claims like “pending_process_verification cleared” whenever canonical workflow state still says `true`.
- Safety: `safe`
- Validation:
  - add a fixture where restart prose claims completion while `.opencode/state/workflow-state.json` still records `pending_process_verification: true`
  - require the audit to surface a finding instead of reporting `0`

### ACTION-002

- Change target: restart-surface publication guardrails
- Why it prevents recurrence:
  - Whether the contradiction came from `handoff_publish`, a docs-handoff path, or a session-level write sequence, the managed workflow should not let derived restart prose claim state transitions that canonical workflow tools have not yet established.
- Safety: `safe`
- Validation:
  - add a regression where restart publication attempts to claim process verification is cleared while `ticket_lookup.process_verification.affected_done_tickets` is still non-empty
  - require the publication step either to refuse the contradictory prose or to regenerate from canonical truth

## Validation And Test Updates

### ACTION-003

- Change target: raw-log-assisted transcript audit guidance
- Why it prevents recurrence:
  - Raw OpenCode logs add evidence classes that agent exports do not: actual write telemetry, tool availability, and reread chronology.
  - This is useful for distinguishing narration-only claims from real state mutation.
- Safety: `safe`
- Validation:
  - preserve transcript-backed audit guidance that samples raw logs selectively for execution telemetry
  - ensure the audit still avoids full-log ingestion unless necessary

## Documentation Or Prompt Updates

### ACTION-004

- Change target: team-leader closeout and reverification guidance
- Why it prevents recurrence:
  - The prompt already states the correct rule, but the `session2.md` chronology shows that weaker models can still misread the relationship between `pending_process_verification`, `affected_done_tickets`, and derived restart prose.
  - A short explicit “do not publish cleared prose while canonical flag remains true” rule would raise the floor.
- Safety: `safe`
- Validation:
  - add a closeout example showing the only two legal outcomes:
    - canonical flag cleared and derived surfaces say cleared
    - canonical flag still true and derived surfaces continue to say pending

## Open Decisions

- No package change is required before the subject repo can be repaired.
- Package hardening is still worthwhile because both the audit script and restart publication path under-detect this contradiction class today.
