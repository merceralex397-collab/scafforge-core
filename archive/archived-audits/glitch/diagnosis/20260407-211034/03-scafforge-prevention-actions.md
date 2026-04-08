# Scafforge Prevention Actions

## Package Changes Required

### ACTION-001

- source_finding: CYCLE002
- change_target: scafforge-audit diagnosis contract
- why_it_prevents_recurrence: Teach audit to stop repeated diagnosis-pack churn when the repo has no newer package or process-version change; require Scafforge package work before the next subject-repo audit.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-002

- source_finding: REF-003
- change_target: generated repo reference integrity and configuration surfaces
- why_it_prevents_recurrence: Add reference-integrity checks and keep engine, config, and local-import paths aligned with real repo files before diagnosis or handoff treats the project as runnable.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-003

- source_finding: SESSION001
- change_target: scafforge-audit transcript chronology and causal diagnosis surfaces
- why_it_prevents_recurrence: Teach scafforge-audit to treat supplied session logs as first-class temporal evidence and explain final reasoning failures before reconciling current repo state.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun transcript-backed audit coverage plus the related curated GPTTalker fixture family

### ACTION-004

- source_finding: SESSION003
- change_target: scafforge-audit transcript chronology and causal diagnosis surfaces
- why_it_prevents_recurrence: Reject unsupported stage probing and explicit workflow bypass attempts in both generated tools and prompt hardening.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun transcript-backed audit coverage plus the related curated GPTTalker fixture family

### ACTION-005

- source_finding: SKILL001
- change_target: project-skill-bootstrap and agent-prompt-engineering surfaces
- why_it_prevents_recurrence: Detect and repair leftover placeholder local skills so generated stack guidance is concrete before implementation continues.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

## Validation and Test Updates

- CYCLE002: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- REF-003: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- SESSION001: rerun transcript-backed audit coverage plus the related curated GPTTalker fixture family.

- SESSION003: rerun transcript-backed audit coverage plus the related curated GPTTalker fixture family.

- SKILL001: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

## Documentation or Prompt Updates

- SESSION001: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- SESSION003: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- SKILL001: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

## Open Decisions

- None recorded.

