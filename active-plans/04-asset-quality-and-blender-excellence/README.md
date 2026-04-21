# Asset Quality And Blender Excellence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Raise the visual quality bar for generated repos so Scafforge stops accepting technically present but visually embarrassing assets, menus, scenes, and motion.

**Architecture:** Quality is a contract, not a vibe. This plan introduces explicit visual review criteria, screenshot/render evidence requirements, truthful Blender support limits, and distilled design guidance for generated interactive repos. Asset acquisition stays in `03`; this plan defines whether the resulting output actually looks acceptable.

**Tech Stack / Surfaces:** `skills/asset-pipeline/`, `skills/project-skill-bootstrap/`, generated template skills/plugins/docs, the external `C:\Users\PC\Documents\GitHub\blender-agent` repo, copied Game Studio and Remotion source material.
**Depends On:** `03-asset-pipeline-architecture` for canonical asset state surfaces; can start discovery in parallel.
**Unblocks:** stronger completion gating in `05-completion-validation-matrix`, better downstream UX quality in `07-autonomous-downstream-orchestration`, and truthful Blender usage throughout the system.
**Primary Sources:** spinner critique in `_source-material/asset-pipeline/assetsplanning/spinner.md`, copied Game Studio/Remotion notes under `_source-material/asset-pipeline/assetsplanning/pipeline/stolenfromcodex/`, `C:\Users\PC\Documents\GitHub\blender-agent`, visual quality research notes in this folder.

---

## Problem statement

Scafforge currently lacks a clear contract for:

- UI composition and menu ergonomics
- visual hierarchy and readability
- intentional style direction
- Blender output quality and support limits
- screenshot/render review before a repo can claim completion

That is why downstream repos can be “working” while obviously looking wrong.

## Required deliverables

- a visual acceptance rubric for generated repos
- screenshot and render evidence requirements
- a Blender capability/support matrix based on the real `blender-agent` surface
- generated-repo guidance for menu/layout quality, especially for game and interactive repos
- distilled Scafforge-owned guidance extracted from external plugin material instead of copied bundles

## Package and adjacent surfaces likely to change during implementation

- `skills/asset-pipeline/SKILL.md`
- `skills/project-skill-bootstrap/references/blender-mcp-workflow-reference.md`
- `skills/project-skill-bootstrap/references/local-skill-catalog.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/workflow.md`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/model-matrix.md`
- `skills/agent-prompt-engineering/references/examples.md`
- `skills/agent-prompt-engineering/references/prompt-contracts.md`
- documentation and integration notes that point to `C:\Users\PC\Documents\GitHub\blender-agent`

## Quality dimensions this plan must own

- screen-fit and responsive layout
- menu readability and affordance clarity
- typography, spacing, and hierarchy
- 2D asset clarity and stylistic consistency
- 3D silhouette, material readability, and finish
- animation/motion “juice” where the product type requires it
- screenshot/render evidence sufficient for review

## Phase plan

### Phase 1: Define the visual quality rubric

- [ ] Write a quality rubric with named failure categories instead of generic “looks bad” language.
- [ ] Split the rubric by surface: 2D UI, 2D game art, 3D props, scenes, and presentation/motion.
- [ ] Define what counts as a blocker versus a polish issue for each category.
- [ ] Ensure the rubric is strict enough to catch spinner/womanvshorse-style failures without forcing one art style.

### Phase 2: Translate the rubric into generated-repo guidance

- [ ] Update generated template guidance so repos know what “screen-fit,” “menu centered,” “visual hierarchy,” and “proof of appearance” actually mean.
- [ ] Add layout guidance for common interactive surfaces such as menus, title screens, HUDs, and modal overlays.
- [ ] Require generated repos to capture screenshots or short visual summaries at specific checkpoints where visual regression matters.
- [ ] Ensure the stage-gate plugin has a hook for visual proof requirements, not only code/test proof.

### Phase 3: Define a truthful Blender contract

- [ ] Audit the real `blender-agent` capability surface and document what it can currently prove, not what we wish it did.
- [ ] Split Blender usage into supported lanes such as hard-surface prop work, basic material/lookdev, export, and QA, versus unsupported or experimental lanes.
- [ ] Define what evidence a Blender-derived asset must emit before it can be considered usable in a generated repo.
- [ ] Document where the asset pipeline should stop and fall back to sourced assets or simpler routes instead of pretending the Blender path is magical.

### Phase 4: Distill useful external design knowledge into Scafforge-owned guidance

- [ ] Review the copied Game Studio and Remotion materials and extract only the concepts that materially improve Scafforge guidance.
- [ ] Re-express those concepts in Scafforge language and file locations instead of copying external bundles wholesale.
- [ ] Decide which ideas belong in generated template skills, which belong in package references, and which remain only as source material.
- [ ] Ensure the resulting guidance is narrow enough for weak models to follow and does not create redundant skill sprawl.

### Phase 5: Add visual review to validation and audit

- [ ] Define when screenshot or render evidence is mandatory by repo type.
- [ ] Ensure visual failures can show up in validation, audit, and handoff language as first-class blockers.
- [ ] Add at least one intentionally ugly fixture or screenshot set to prove the review lane catches real failures.
- [ ] Confirm the system cannot mark a visually broken repo “complete” just because tests pass.

## Validation and proof requirements

- generated repos that need visual quality proof must emit screenshots or renders
- spinner-style screen-fit failures are caught by the quality rubric
- Blender-derived assets are assessed against a truthful support matrix
- copied external plugin ideas are distilled into Scafforge-owned guidance instead of being treated as shipped product behavior

## Risks and guardrails

- Do not confuse style choice with quality. The contract should judge intent, readability, and finish, not only realism.
- Do not promise that Blender can make everything. Document supported lanes and stop there.
- Do not build a generic “art critic” with no evidence model. Every failure category needs concrete review language.
- Keep design guidance concise enough for generated repos; do not dump giant art-theory essays into template skills.

## Documentation updates required when this plan is implemented

- asset-pipeline docs
- project-skill-bootstrap references
- generated template skills/plugins/docs related to standards and stage gates
- package docs that describe Blender support
- root documentation sweep outputs where visual proof becomes part of the contract

## Completion criteria

- Scafforge has a named visual quality rubric
- visual proof becomes part of completion for the stacks that need it
- Blender support is documented honestly and can be validated
- generated repos receive clearer design and menu-quality guidance than they do today
