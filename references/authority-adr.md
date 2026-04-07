# Authority Ownership ADR

## Status

Final for PR-01.

## Purpose

This ADR freezes the package authority map for the Scafforge reliability re-architecture. The goal is to stop split authority before later tickets change workflow, restart, or pivot behavior.

## Ownership Map

| Truth domain | Single owner | Scope |
| --- | --- | --- |
| Diagnosis disposition | `scafforge-audit` | Classifies findings, emits the authoritative disposition bundle, and owns follow-up routing decisions. |
| Repo mutation | Generated runtime workflow layer | Mutates canonical ticket, workflow, artifact, and restart-surface state. Package-side repair and pivot surfaces may invoke it, but they do not redefine it. |
| Pivot-state persistence | `scafforge-pivot` | Owns `.opencode/meta/pivot-state.json` persistence and bounded pivot classification truth. |
| Restart publication | `handoff-brief` | Publishes derived restart surfaces only after the verified final snapshot is available. |
| Contract alignment | `agent-prompt-engineering` | Hardens the contract surfaces that keep prompts, workflow docs, and generated behavior aligned to the same state machine. |

## First Collapse Target

The first duplicate-authority seam to collapse was repair-side restart rendering and raw workflow mutation. `apply_repo_process_repair.py` and `regenerate_restart_surfaces.py` are the package-side paths that the runtime-owned workflow layer replaced.

## Rules

1. Diagnosis owns finding disposition and follow-up classification.
2. Runtime mutation owns canonical repo state changes.
3. Pivot tracking owns pivot-state persistence and stale-surface routing.
4. Restart publication may only happen from the final verified post-mutation state.
5. Contract alignment must keep `AGENTS.md`, `skills/skill-flow-manifest.json`, and the reference contracts in sync with the same owner map.

## Dependent References

- [Invariant Catalog](invariant-catalog.md)
- [Stack Adapter Contract](stack-adapter-contract.md)
- [Competence Contract](competence-contract.md)
- [One-Shot Generation Contract](one-shot-generation-contract.md)
