# Ticket System

This Scafforge package repo uses:

- `tickets/manifest.json` as the machine-readable backlog index
- `tickets/BOARD.md` as the derived human board
- `tickets/*.md` as the source of execution instructions, affected surfaces, and verification steps
- `tickets/templates/TICKET.template.md` as the ticket authoring template

Rules for this backlog:

- treat the RFC implementation backlog as the canonical queue for the reliability re-architecture
- this repo is the Scafforge package, not a generated repo; do not add root `.opencode/` runtime state surfaces to manage this backlog
- treat `tickets/manifest.json` as a tracker only; it may name a current focus ticket, but it is not a workflow-state manager
- keep `stage`, `status`, `resolution_state`, and `verification_state` as coarse package-planning metadata only
- put the actual work instructions, target files, and verification steps in the ticket markdown itself rather than relying on external workflow state
- follow `IMPLEMENTATION-HANDOFF.md` for branch naming, PR order, reviewer gates, and ticket bundling during implementation
- use `npm run validate:contract`, `npm run validate:smoke`, `python3 scripts/integration_test_scafforge.py`, and `python3 scripts/validate_gpttalker_migration.py` as the baseline package validation entrypoints referenced by ticket acceptance
- keep `tickets/BOARD.md` derived from `tickets/manifest.json`
- if work changes generated-repo behavior, edit package sources or template assets under `skills/repo-scaffold-factory/assets/project-template/`; do not simulate generated-repo runtime state in the package root
- use the Notes section in each ticket to name the RFC phase, workstream, and primary package surfaces that must be touched before the ticket can close
