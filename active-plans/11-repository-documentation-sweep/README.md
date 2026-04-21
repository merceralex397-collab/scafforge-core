# Repository Documentation Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Rebuild Scafforge’s documentation architecture so both humans and agents can reliably find authority, workflow, scope, and next steps without reading the entire repository.

**Architecture:** Keep root docs short and authoritative, push deep detail into references, and align generated-template docs with package docs. This plan starts immediately and then repeats after every implemented plan in the program. Documentation is not a final cleanup sprint; it is part of the product contract.

**Tech Stack / Surfaces:** root markdown docs, package references, skill docs, generated-template docs, plan/report surfaces.
**Depends On:** starts immediately; continues in parallel with all other plans.
**Unblocks:** every later implementation by reducing context friction and contract drift.
**Primary Sources:** `AGENTS.md`, `architecture.md`, `README.md`, `USERGUIDE.md`, `references/*.md`, generated-template docs under `skills/repo-scaffold-factory/assets/project-template/`.

---

## Problem statement

Scafforge is contract-heavy. That means documentation drift is functionally equivalent to product drift. If agents cannot tell which document owns:

- package authority
- workflow sequence
- stack adapter expectations
- generated repo truth surfaces
- current implementation boundaries

then the package becomes less reliable even when the code has not changed.

## Required deliverables

- a source-of-truth map for package docs
- a rewrite order for root docs and references
- a generated-template documentation alignment plan
- a recurring documentation update rule tied to every other plan
- a lightweight context-acquisition path for new contributors and agents

## Documentation surfaces this plan must rationalize

### Root package docs

- `README.md`
- `USERGUIDE.md`
- `architecture.md`
- `AGENTS.md`
- `active-plans/README.md`
- `active-plans/FULL-REPORT.md`

### Contract references

- `references/authority-adr.md`
- `references/invariant-catalog.md`
- `references/competence-contract.md`
- `references/one-shot-generation-contract.md`
- `references/stack-adapter-contract.md`

### Skill and template docs

- `skills/*/SKILL.md`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/*.md`
- `skills/repo-scaffold-factory/assets/project-template/docs/spec/CANONICAL-BRIEF.md`
- generated template `.opencode/skills/*` docs where package-generated guidance lives

## Phase plan

### Phase 1: Build the documentation authority map

- [ ] Inventory every major package doc and assign its truth domain.
- [ ] Identify overlaps, contradictions, and missing navigation between root docs and references.
- [ ] Decide which documents are canonical, which are derived, and which should become archived/historical only.
- [ ] Publish a one-screen authority map that new contributors can follow without guesswork.

### Phase 2: Rewrite the root-doc routing layer

- [ ] Rewrite `README.md` so it explains what Scafforge is, what it is not, and where deeper contract docs live.
- [ ] Rewrite `USERGUIDE.md` so it serves operators instead of duplicating architecture prose.
- [ ] Update `architecture.md` so it reflects the current package and planned adjacent systems without blurring them.
- [ ] Update `AGENTS.md` so its instructions, boundaries, and active-plan guidance match reality.

### Phase 3: Rationalize the reference set

- [ ] Verify each reference file has one clear purpose and is linked from the right root doc.
- [ ] Remove duplicated contract wording from scattered docs and point back to the canonical reference instead.
- [ ] Add missing references only when a truth domain has no stable home.
- [ ] Keep reference docs durable and conceptual; move transient program-specific details into active plans instead.

### Phase 4: Align generated-template docs with package docs

- [ ] Compare package workflow docs with the generated template’s `docs/process/`, `docs/spec/`, and `.opencode/skills/` guidance.
- [ ] Fix contradictions so generated repos inherit current package truth instead of stale wording.
- [ ] Ensure generated template docs remain OpenCode-oriented and do not import package-root planning semantics.
- [ ] Update any generated guidance that overclaims validation, quality, or restart truth.

### Phase 5: Make documentation updates a standing requirement

- [ ] Add a rule that every contract-changing PR must update docs in the same change.
- [ ] Add a per-plan checklist item to confirm which docs are affected.
- [ ] Ensure the active plans index and report are updated when implementation order or architecture decisions change.
- [ ] Add a lightweight contributor checklist for doc verification before review.

### Phase 6: Verify context acquisition end to end

- [ ] Run a newcomer-context test using only root docs and one reference hop.
- [ ] Run an agent-context test to ensure the repo can answer basic boundary questions quickly from docs alone.
- [ ] Confirm generated-template docs and package docs no longer contradict each other in touched areas.
- [ ] Record residual gaps and route them back into the appropriate active plan if they require implementation work.

## Validation and proof requirements

- every major truth domain has one discoverable canonical document
- root docs route to deeper references instead of duplicating them badly
- generated-template docs match current package behavior in touched areas
- future plan implementations can identify required doc updates without guesswork

## Risks and guardrails

- Do not rewrite all docs at once without an authority map.
- Do not let active plans become the permanent home for durable contract docs.
- Do not collapse package docs and generated-repo docs into one blended narrative.
- Keep root docs navigational; detailed rules belong in references or skill docs.

## Documentation updates required when this plan is implemented

This plan is itself the update policy. It begins immediately and should be revisited after every implemented plan in the program.

## Completion criteria

- root docs clearly route readers to authoritative contract surfaces
- doc drift becomes harder to introduce
- agents can gather correct package context faster
- every future plan carries explicit documentation obligations by default
