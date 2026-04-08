# Scafforge Prevention Actions

## Package Changes Required

### ACTION-001

- source_finding: REF-003
- change_target: generated repo reference integrity and configuration surfaces
- why_it_prevents_recurrence: Add reference-integrity checks and keep engine, config, and local-import paths aligned with real repo files before diagnosis or handoff treats the project as runnable.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

## Validation and Test Updates

- REF-003: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

## Documentation or Prompt Updates

- None recorded.

## Open Decisions

- None recorded.

