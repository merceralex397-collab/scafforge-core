# Documentation Architecture Notes

## Suggested Package Truth Hierarchy

- `AGENTS.md` for repo operating rules and package/output boundary discipline
- `architecture.md` for system structure and major moving parts
- `references/` for contracts, ADRs, invariants, and detailed operational truth
- `README.md` for fast orientation and navigation
- `USERGUIDE.md` for operator-facing usage guidance
- `tickets/` for package backlog and implementation sequencing

## Root Doc Problems To Watch

- duplicate explanation of the same contract in multiple files
- missing navigation between high-level and detailed docs
- outdated references to workflows or plan locations
- root docs trying to hold too much deep implementation detail

## Primary Inputs

- `../../AGENTS.md`
- `../../architecture.md`
- `../../references/competence-contract.md`
- `../../references/authority-adr.md`
- `../../references/one-shot-generation-contract.md`

## Planning Consequence

This plan should start early and stay active. Every other plan in this program will require documentation alignment work once implemented.
