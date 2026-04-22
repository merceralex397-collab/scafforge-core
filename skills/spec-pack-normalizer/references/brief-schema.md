# Canonical Brief Schema

Use this structure when normalizing a spec pack or opportunistically scanned input repo.

## 1. Project Summary

- One paragraph.
- State what is being built and why.

## 2. Goals

- Flat bullet list of desired outcomes.

## 3. Non-Goals

- Flat bullet list of explicit exclusions.

## 4. Constraints

- Platform/runtime constraints
- Model/provider constraints
- Repository/process constraints
- Integration/tooling constraints

## 5. Required Outputs

- Required repo structure
- Required docs
- Required agent/tool/plugin outputs
- Required validation expectations

## 6. Tooling and Model Constraints

- provider expectations
- primary model
- optional helper model
- runtime or host constraints

## 7. Canonical Truth Map

- canonical facts file
- canonical queue state
- canonical transient workflow state
- canonical artifact/proof locations
- canonical provenance surface
- derived handoff surfaces

## 8. Blocking Decisions

- unresolved choices that materially change implementation
- grouped into one batched decision packet that is written down as a required generation artifact
- resolved before the greenfield generation pass continues

## 9. Non-Blocking Open Questions

- unresolved questions that do not prevent the first execution wave

## 10. Backlog Readiness

- whether the first execution wave can be detailed now after blocking decisions are resolved
- which areas remain non-blocking open questions instead of generation blockers

## 11. Acceptance Signals

- What must be true for the result to be considered usable

## 12. Assumptions

- Only include non-blocking assumptions that do not silently decide major project behavior

## 13. Product Finish Contract

For consumer-facing repos, unresolved finish requirements must become explicit blocking decisions rather than implicit assumptions.
For internal tools and services, this section may be intentionally minimal.

- `deliverable_kind` — what the user expects at the end: service, internal tool, playable prototype, packaged mobile product, store-ready build, etc.
- `placeholder_policy` — whether placeholder or procedural output is acceptable as final output (`placeholder_ok` or `no_placeholders`)
- `visual_finish_target` — the visual quality bar that counts as done for this repo; describe explicitly or note "procedural-only acceptable"
- `audio_finish_target` — the audio bar that counts as done; describe explicitly or note "no audio required" or "procedural-only acceptable"
- `content_source_plan` — where visuals, audio, and other creative content come from: custom authored, licensed pack, procedural-only, mixed, or intentionally none
- `licensing_or_provenance_constraints` — any constraints on generated, licensed, or bundled assets
- `finish_acceptance_signals` — the explicit signals that let audit and closeout know the finish bar was met

## Approved factory handoff bundle

When the source input is an approved adjacent spec-factory brief, the brief content still uses the 13 sections above. The persisted handoff bundle must also carry:

- approval metadata with approver identity and timestamp
- decision residue for unresolved or deferred non-blocking questions
- attachment index and durable attachment references
- provenance linking intake inputs, draft, approval, and approved brief artifacts

In that mode, `spec-pack-normalizer` validates alignment against this schema and rejects malformed bundles cleanly; it does not become a second creative drafting stage.
