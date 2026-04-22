# Spec Factory Handoff Contract

Scafforge accepts approved briefs from an **adjacent spec-factory workspace or service**, not from hidden package-side intake logic.

## Boundary

- The spec factory owns idea intake, enrichment, drafting, decision packets, review, and approval workflow.
- Scafforge owns canonical brief normalization, generation, ticketing, audit, repair, and restart publication.
- ChatGPT, MCP, or Apps SDK surfaces are transport and review clients only. They are not approval authorities.
- The runtime trigger that invokes `scaffold-kickoff` belongs to the later orchestration layer from plan `07`, not to the spec factory.

## Eligible handoff bundle

An approved factory brief is eligible for Scafforge intake only when all of these persisted artifacts exist:

- approved brief file (`approved-brief.md`, `approved-brief.json`, or equivalent addressable artifact)
- approval metadata with timestamp and approver identity
- decision-packet residue, including any deferred non-blocking questions
- attachment index with durable references
- provenance linking the approved brief back to the draft and source inputs

Transient chat state, in-memory UI state, or an MCP tool result without persisted files is **not** a legal handoff.

## Required approval rule

- `approved` is human-gated by default.
- Agents may recommend approval and prepare the review packet.
- Agents may not auto-transition an item into `approved`.
- The approval artifact must be written before Scafforge treats the brief as eligible input.

## `spec-pack-normalizer` behavior for approved factory briefs

When Scafforge receives a valid approved factory bundle:

- `spec-pack-normalizer` performs a validator-alignment pass
- it checks bundle presence, schema alignment, and required brief sections
- it may reject malformed or incomplete handoffs cleanly
- it does **not** regenerate a fresh creative decision packet when the bundle already resolves blocking choices

If the bundle is malformed, rejection routes back to the spec factory for repair. Scafforge should not mutate factory approval state as part of that rejection.

## Canonical brief alignment

The approved brief content must still align to the canonical Scafforge brief contract:

1. Project Summary
2. Goals
3. Non-Goals
4. Constraints
5. Required Outputs
6. Tooling and Model Constraints
7. Canonical Truth Map
8. Blocking Decisions
9. Non-Blocking Open Questions
10. Backlog Readiness
11. Acceptance Signals
12. Assumptions
13. Product Finish Contract

The factory may keep richer drafting and review artifacts, but the handoff brief must map cleanly onto these sections.

