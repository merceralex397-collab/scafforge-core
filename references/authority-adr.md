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
| Orchestration job state | Adjacent orchestration service | Owns job envelopes, phase grouping, idempotency and retry tokens, PR automation, and pause or resume controls, but stays read-only over generated canonical repo truth. |
| Managed repair execution | `scafforge-repair` | Applies safe package-managed repairs, refreshes generated workflow surfaces, and delegates canonical state mutation back through the generated runtime workflow layer. |
| Pivot-state persistence | `scafforge-pivot` | Owns `.opencode/meta/pivot-state.json` persistence and bounded pivot classification truth. |
| Restart publication | `handoff-brief` | Publishes derived restart surfaces only after the verified final snapshot is available. |
| Contract alignment | `agent-prompt-engineering` | Hardens the contract surfaces that keep prompts, workflow docs, and generated behavior aligned to the same state machine. |

## First Collapse Target

The first duplicate-authority seam to collapse was repair-side restart rendering and raw workflow mutation. `apply_repo_process_repair.py` and `regenerate_restart_surfaces.py` are the package-side paths that were converted to thin adapters delegating to the runtime-owned workflow layer. Dead rendering functions were removed in the final review cleanup.

## Rules

1. Diagnosis owns finding disposition and follow-up classification.
2. Runtime mutation owns canonical repo state changes.
3. Pivot tracking owns pivot-state persistence and stale-surface routing.
4. Restart publication may only happen from the final verified post-mutation state.
5. Contract alignment must keep `AGENTS.md`, `skills/skill-flow-manifest.json`, and the reference contracts in sync with the same owner map.
6. Adjacent orchestration may derive wrapper state from Scafforge and GitHub outputs, but it may not rewrite `tickets/manifest.json`, `.opencode/state/workflow-state.json`, or restart publication directly.

## Dependent References

- [Invariant Catalog](invariant-catalog.md)
- [Stack Adapter Contract](stack-adapter-contract.md)
- [Competence Contract](competence-contract.md)
- [One-Shot Generation Contract](one-shot-generation-contract.md)
- [Orchestration Wrapper Contract](orchestration-wrapper-contract.md)
