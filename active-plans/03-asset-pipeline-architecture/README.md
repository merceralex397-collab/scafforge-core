# Asset Pipeline Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Replace the current coarse asset-route concept with a real Scafforge asset operating framework that can classify, generate, source, validate, and prove asset truth in generated repositories.

**Architecture:** Move from four vague route labels to a capability-based asset system. Generated repos should receive canonical asset requirements, manifests, workflow locks, provenance/compliance records, optimization reports, and import QA surfaces. The pipeline must prefer deterministic and curated paths first, AI generation second, and DCC cleanup/export where necessary.

**Tech Stack / Surfaces:** `skills/asset-pipeline/`, generated repo template assets, provenance validators, license/compliance rules, import optimization tools, generated docs.
**Depends On:** `02-downstream-reliability-hardening` and `05-completion-validation-matrix` should inform proof gates, but taxonomy work can begin now.
**Unblocks:** `04-asset-quality-and-blender-excellence`, parts of `07-autonomous-downstream-orchestration`, and downstream asset-related repair improvements.
**Primary Sources:** `skills/asset-pipeline/*`, `active-plans/_source-material/asset-pipeline/assetsplanning/game-asset-generation-research.md`, `active-plans/_source-material/asset-pipeline/assetsplanning/research-about-video-game-art-assets-designs-and-a.md`, `active-plans/_source-material/asset-pipeline/assetsplanning/pipeline/asset-pipeline-agent-research-2026-04-14.md`.

---

## Problem statement

The current asset system can suggest where an asset might come from, but it does not yet provide durable answers for:

- which route should be selected and why
- how source license and model/tool provenance are recorded
- how generated files are optimized and imported into the engine
- how an agent knows what fallback comes next when a route fails
- how a repo proves it is using commercially acceptable and technically valid assets

That is why broken imports and low-confidence asset handling keep leaking into downstream repos.

## Required deliverables

- a capability taxonomy replacing the current vague route family model
- canonical asset state surfaces for generated repos
- license/compliance rules with deny-by-default handling for unsupported sources
- tool/model/workflow provenance for generated assets
- import and optimization QA rules
- fallback ladders by asset category

## Canonical asset surfaces this plan should introduce

Generated repos should converge on these surfaces:

- `assets/requirements.json`
- `assets/manifest.json`
- `assets/ATTRIBUTION.md`
- `assets/PROVENANCE.md` as a derived human ledger, not the only source of truth
- `assets/workflows/`
- `assets/previews/`
- `assets/qa/import-report.json`
- `assets/qa/license-report.json`
- `.opencode/meta/asset-provenance-lock.json`

## Package surfaces likely to change during implementation

- `skills/asset-pipeline/SKILL.md`
- `skills/asset-pipeline/references/PROVENANCE-template.md`
- `skills/asset-pipeline/references/asset-description-skill.md`
- `skills/asset-pipeline/scripts/init_asset_pipeline.py`
- `skills/asset-pipeline/scripts/validate_provenance.py`
- `skills/repo-scaffold-factory/assets/project-template/`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/`
- `skills/project-skill-bootstrap/references/local-skill-catalog.md`
- `references/stack-adapter-contract.md`
- `scripts/validate_scafforge_contract.py`
- `tests/fixtures/` for mixed-asset validation coverage

## Proposed capability taxonomy

This plan should replace route guesswork with explicit capability families:

- `source-open-curated`
- `source-mixed-license`
- `procedural-2d`
- `procedural-layout`
- `procedural-world`
- `local-ai-2d`
- `local-ai-audio`
- `reconstruct-3d`
- `dcc-assembly`
- `optimize-import`
- `provenance-compliance`

The purpose is not to advertise every tool. The purpose is to make route choice and fallback explicit.

## Phase plan

### Phase 1: Replace the current route model

- [ ] Audit the current `asset-pipeline` skill and identify where route selection is currently too coarse or keyword-driven.
- [ ] Replace the current route family wording with the capability taxonomy above or a refined version that still keeps the same operational split.
- [ ] Document what each capability owns, what it requires as input, and what evidence it must emit.
- [ ] Update the bootstrap logic so route choice is recorded explicitly instead of inferred later from vague text.

### Phase 2: Define the canonical asset state model

- [ ] Design the file contract for `requirements`, `manifest`, `workflow`, `preview`, and QA surfaces.
- [ ] Define which fields are authoritative in machine-readable JSON versus derived in markdown summaries.
- [ ] Ensure the manifest can distinguish sourced assets, procedural assets, AI-generated assets, reconstructed assets, and Blender-assembled assets.
- [ ] Define how generated repos are expected to use the state model during greenfield generation, later repair, and final handoff.

### Phase 3: Build provenance and compliance rules

- [ ] Expand provenance from “file listed in `PROVENANCE.md`” into source URL, author, license, tool, model, prompt/workflow, and version lock where applicable.
- [ ] Define an allowlist/denylist policy for asset sources and model licenses.
- [ ] Make sure mixed-license sources such as OpenGameArt or Freesound require explicit attribution/commercial policy handling.
- [ ] Define how generated repos build `ATTRIBUTION.md` and machine-readable license reports from the authoritative manifest.

### Phase 4: Add optimization and import QA to the contract

- [ ] Specify a standard optimization stage for 2D, 3D, and audio assets where the stack supports it.
- [ ] Define import-report expectations for Godot and any other stack Scafforge claims to support in asset-heavy contexts.
- [ ] Require preview artifacts or contact-sheet style outputs for human audit when assets are not trivially inspectable.
- [ ] Ensure import success and optimization status are recorded in the QA surfaces, not left as transient console output.

### Phase 5: Define fallback ladders by asset category

- [ ] Write category-specific fallback ladders for fonts, icons, UI kits, sprites/tiles, VFX, SFX, props, terrain, environments, and characters.
- [ ] Make deterministic/procedural and curated open sources the default first choices before AI generation.
- [ ] Define the exact moment an agent is allowed to escalate to local AI generation or Blender assembly.
- [ ] Document where the pipeline should stop and ask for human input instead of hallucinating a route.

### Phase 6: Integrate with audit, repair, and validation

- [ ] Ensure asset-state surfaces can be consumed by `scafforge-audit` and `scafforge-repair`.
- [ ] Update package validation so missing provenance, banned licenses, or missing import QA fail cleanly.
- [ ] Add a mixed-asset fixture repo or fixture pack to prove the contract works across sourced, procedural, and generated assets together.
- [ ] Confirm the handoff and restart surfaces can summarize asset truth without making the operator read the full manifest.

## Validation and proof requirements

- a generated repo receives canonical asset state surfaces, not only `PROVENANCE.md`
- the validator rejects missing provenance, unsupported licenses, and missing QA reports
- mixed-source asset projects can be represented truthfully in one manifest
- audit and repair can consume the same asset-truth surfaces without inventing new state

## Risks and guardrails

- Do not turn the pipeline into a brand list. Capability and proof matter more than which product name is fashionable.
- Do not promise autonomous AAA asset generation; the pipeline must stay honest about supported routes.
- Do not overload `PROVENANCE.md` as the only truth surface.
- Keep the pipeline navigable to weaker models: few core concepts, explicit fallbacks, and no hidden policy.

## Documentation updates required when this plan is implemented

- `skills/asset-pipeline/SKILL.md`
- asset-pipeline reference notes and templates
- project-template asset docs and process docs
- package references that describe supported asset handling
- any generated repo contributor docs that currently describe asset work too vaguely

## Completion criteria

- Scafforge can classify asset work by capability rather than guesswork
- generated repos receive canonical asset requirements, state, and QA surfaces
- provenance and compliance are machine-checkable
- fallback ladders exist for the asset categories Scafforge claims to support
