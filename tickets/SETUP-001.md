# SETUP-001: Establish package-local execution baseline and affected-surface inventory

## Summary

Bootstrap the Scafforge package repo for the RFC implementation itself by fixing the local queue surfaces, naming the canonical validation commands, freezing the affected-surface inventory from the RFC, and making the first legal move explicit so later work does not start from stale assumptions.

## Why

This ticket resets the backlog onto package-repo terms before any implementation work starts. The package needs a clean planning surface that does not pretend the Scafforge repo is itself a generated OpenCode-managed repo.

## Package Boundary

- Work only in package-owned planning and documentation surfaces.
- Do not add or rely on package-root `.opencode/` runtime state.
- If later tickets need generated-repo behavior changes, they must target package scripts or template assets.

## Do This

1. Remove any package-root backlog machinery that assumes a generated-repo workflow-state manager exists.
2. Make the ticket pack self-describing: the manifest tracks the backlog, the board summarizes it, and the ticket markdown carries the work instructions.
3. Freeze the validation command list that later tickets must reference.
4. Confirm the ticket pack covers the RFC appendix surfaces before implementation starts.

## Files To Update

- `tickets/README.md`
- `tickets/manifest.json`
- `tickets/BOARD.md`
- `tickets/templates/TICKET.template.md`
- `.github/prompts/plan-scafforgeReliabilityRearchitecture.prompt.md`

## Verify

1. Confirm there is no package-root `.opencode/` workflow-state file driving the backlog.
2. Confirm `tickets/manifest.json` marks `SETUP-001` complete and advances the current package focus to `ARCH-001`.
3. Confirm the validation commands referenced here match `package.json` and runnable package scripts.
4. Confirm the ticket pack documentation says the ticket markdown, not external runtime state, carries the execution detail.

## Wave

0

## Lane

repo-foundation

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

complete

## Status

done

## Trust

- resolution_state: completed
- verification_state: verified
- finding_source: None
- source_ticket_id: None
- source_mode: None

## Depends On

None

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `tickets/manifest.json`, `tickets/BOARD.md`, and `tickets/templates/TICKET.template.md` exist and record the cleaned package backlog with `SETUP-001` complete and `ARCH-001` as the next focus
- [ ] Package validation entrypoints are documented as `npm run validate:contract`, `npm run validate:smoke`, `python3 scripts/integration_test_scafforge.py`, and `python3 scripts/validate_gpttalker_migration.py`
- [ ] The ticket pack accounts for every primary surface named in the RFC appendix with no unowned package area left outside the backlog
- [ ] The package repo backlog makes the first implementation ticket obvious without relying on generated-repo workflow state

## Artifacts

- 2026-04-05: package backlog cleanup completed; package-root generated-repo runtime state removed; ticket pack rewritten to be self-contained for strong-host package work

## Notes

- RFC coverage: Wave 0 bootstrap, package-local queue setup, affected-surface inventory freeze.
- Primary surfaces: `tickets/manifest.json`, `tickets/BOARD.md`, `tickets/templates/TICKET.template.md`, `.github/prompts/plan-scafforgeReliabilityRearchitecture.prompt.md`.
- Validation focus: baseline entrypoints for contract, smoke, integration, and migration validation.
