# Repository Documentation Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** DONE
**Goal:** Rebuild Scafforge’s documentation architecture so both humans and agents can reliably find authority, workflow, scope, and next steps without reading the entire repository.

**Architecture:** Keep root docs short and authoritative, push deep detail into references, and align generated-template docs with package docs. This plan starts immediately and then repeats after every implemented plan in the program. Documentation is not a final cleanup sprint; it is part of the product contract.

**Tech Stack / Surfaces:** root markdown docs, package references, skill docs, generated-template docs, plan/report surfaces.
**Depends On:** plan `01` must complete before this plan rewrites `AGENTS.md` or `active-plans/README.md`; reference rationalization and template-alignment work can start in parallel sooner.
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

- a source-of-truth map for package docs, published at `active-plans/11-repository-documentation-sweep/references/documentation-authority-map.md`
- a rewrite order for root docs and references, published in this plan and tracked in implementation PRs
- a generated-template documentation alignment plan
- a recurring documentation update rule tied to every other plan
- a lightweight context-acquisition path for new contributors and agents, including explicit context-test questions and evidence capture

## Documentation surfaces this plan must rationalize

### Root package docs

- `README.md`
- `USERGUIDE.md`
- `architecture.md`
- `AGENTS.md`
- `active-plans/README.md`
- `active-plans/FULL-REPORT.md`
- `active-plans/docscleanup.md`
- `active-plans/13-meta-skill-engineering-repo-hardening/references/meta-skill-engineering-extra-plan-intake.md`

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

- [x] Inventory every major package doc and assign its truth domain.
- [x] Identify overlaps, contradictions, and missing navigation between root docs and references.
- [x] Decide which documents are canonical, which are derived, and which should become archived/historical only.
- [x] Publish a one-screen authority map at `active-plans/11-repository-documentation-sweep/references/documentation-authority-map.md` that new contributors can follow without guesswork.
- [x] Use `references/documentation-architecture-notes.md` as the seeded starting point rather than starting from a blank inventory.

### Phase 2: Rewrite the root-doc routing layer

- [x] Rewrite `README.md` so it explains what Scafforge is, what it is not, and where deeper contract docs live.
- [x] Rewrite `USERGUIDE.md` so it serves operators instead of duplicating architecture prose.
- [x] Update `architecture.md` so it reflects the current package and planned adjacent systems without blurring them.
- [x] Update `AGENTS.md` so its instructions, boundaries, and active-plan guidance match reality.
- [x] Treat the lightweight context-acquisition path as an explicit Phase 2 deliverable across `README.md`, `USERGUIDE.md`, and the authority map rather than an implied side effect.
- [x] After any change to `README.md` or `AGENTS.md`, run `npm run validate:contract`; preserve any literal strings the validator pins or update the validator in the same PR when the contract genuinely changes.

### Phase 3: Rationalize the reference set

- [x] Verify each reference file has one clear purpose and is linked from the right root doc.
- [x] Remove duplicated contract wording from scattered docs and point back to the canonical reference instead.
- [x] Seed the sweep with known contradictions: `references/one-shot-generation-contract.md` duplicates the same entrypoint and lifecycle-boundary sentences, and `architecture.md` still describes the wrong skill count versus the current `skills/*/SKILL.md` set.
- [x] Add missing references only when a truth domain has no stable home.
- [x] Keep reference docs durable and conceptual; move transient program-specific details into active plans instead.
- [x] Before deduplicating `references/one-shot-generation-contract.md`, verify which exact sentence form the contract validator checks and keep that form rather than accidentally deleting the pinned variant.
- [x] After any change to `references/authority-adr.md`, `references/invariant-catalog.md`, `references/competence-contract.md`, `references/one-shot-generation-contract.md`, or `references/stack-adapter-contract.md`, run `npm run validate:contract` and keep validator-backed wording aligned in the same PR.

### Phase 4: Align generated-template docs with package docs

- [x] Compare package workflow docs with the generated template’s `docs/process/`, `docs/spec/`, and `.opencode/skills/` guidance.
- [x] Fix contradictions so generated repos inherit current package truth instead of stale wording.
- [x] Ensure generated template docs remain OpenCode-oriented and do not import package-root planning semantics.
- [x] Update any generated guidance that overclaims validation, quality, or restart truth.

### Phase 5: Make documentation updates a standing requirement

- [x] Add a rule that every contract-changing PR must update docs in the same change.
- [x] Add a per-plan checklist item to confirm which docs are affected.
- [x] Ensure the active plans index and report are updated when implementation order or architecture decisions change.
- [x] Add a lightweight contributor checklist for doc verification before review.
- [x] Decide explicitly whether `active-plans/WORK-JOURNAL.md` and `active-plans/codexinstructions.md` are part of this rationalization sweep or intentionally out of scope, and record that choice.
- [x] Land the durable standing-rule wording in `AGENTS.md` rather than inventing a second policy home, while keeping `active-plans/README.md` as the program-level reminder rather than a duplicate authority source.
- [x] Make the recurring nature of this plan visible through the per-plan checklist mechanism so the “repeat after every implemented plan” rule is trackable rather than aspirational.

### Phase 6: Verify context acquisition end to end

- [x] Run a newcomer-context test using only root docs and one reference hop.
- [x] Run an agent-context test to ensure the repo can answer basic boundary questions quickly from docs alone.
- [x] Require both tests to answer, at minimum: who owns restart publication, what the greenfield skill chain is, where the generated-repo truth hierarchy lives, and where package-versus-output boundaries are defined.
- [x] Capture the results in `active-plans/11-repository-documentation-sweep/references/documentation-context-tests.md`, including the test questions, the exact doc path used to answer each question, and whether the answer was found within one root-doc hop.
- [x] Confirm generated-template docs and package docs no longer contradict each other in touched areas.
- [x] Record residual gaps and route them back into the appropriate active plan if they require implementation work.

## Validation and proof requirements

- every major truth domain has one discoverable canonical document
- root docs route to deeper references instead of duplicating them badly
- generated-template docs match current package behavior in touched areas
- future plan implementations can identify required doc updates without guesswork
- the newcomer-context and agent-context tests both have explicit pass/fail records

## Risks and guardrails

- Do not rewrite all docs at once without an authority map.
- Do not let active plans become the permanent home for durable contract docs.
- Do not collapse package docs and generated-repo docs into one blended narrative.
- Keep root docs navigational; detailed rules belong in references or skill docs.

## Documentation updates required when this plan is implemented

- `README.md`
- `USERGUIDE.md`
- `architecture.md`
- `AGENTS.md`
- `active-plans/README.md`
- `active-plans/FULL-REPORT.md`
- `active-plans/docscleanup.md`
- `active-plans/13-meta-skill-engineering-repo-hardening/references/meta-skill-engineering-extra-plan-intake.md`
- `active-plans/11-repository-documentation-sweep/references/documentation-authority-map.md`
- `active-plans/11-repository-documentation-sweep/references/documentation-context-tests.md`
- `references/authority-adr.md`
- `references/invariant-catalog.md`
- `references/competence-contract.md`
- `references/one-shot-generation-contract.md`
- `references/stack-adapter-contract.md`
- any touched `skills/*/SKILL.md` or generated-template docs proven to carry stale or duplicated contract wording

## Completion criteria

- root docs clearly route readers to authoritative contract surfaces
- doc drift becomes harder to introduce
- agents can gather correct package context faster
- every future plan carries explicit documentation obligations by default
