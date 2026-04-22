# Skill System Expansion And Meta Skill Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** DONE
**Goal:** Create the disciplined path by which Scafforge learns from failures, external skill research, and the Meta-Skill-Orchestration concept without degenerating into random skill sprawl.

**Architecture:** Skill evolution becomes a bounded lifecycle: detect gap -> evaluate evidence -> distill external knowledge -> package the change into Scafforge-owned skill assets -> validate it -> decide whether downstream repos need an immediate skill repair. The system must preserve the package-versus-repo skill boundary and keep the skill catalog navigable for weak models.

**Tech Stack / Surfaces:** `skills/project-skill-bootstrap/`, `skills/opencode-team-bootstrap/`, `skills/agent-prompt-engineering/`, `skills/skill-flow-manifest.json`, package references, future skill-validation surfaces, external skill-source repos and copied reference bundles.
**Depends On:** plan `08` must at least define its evidence bundle and escalation-trigger contract before this plan finalizes audit-derived skill-gap intake; plan `11` must at least define the stable documentation homes before this plan lands durable policy docs.
**Unblocks:** safer skill evolution, downstream skill repair policy, and any future `scafforge-meta-skill-engineer-agent`.
**Primary Sources:** user requirement for Meta-Skill-Orchestration, `_source-material/asset-pipeline/assetsplanning/pipeline/stolenfromcodex/`, `skills/project-skill-bootstrap/references/local-skill-catalog.md`, package skill-boundary rules in `AGENTS.md`, and `references/competence-contract.md`.

---

## Problem statement

Scafforge already depends on skills, but it does not yet have a rigorous answer to:

- how skill gaps are discovered
- how external skill material is evaluated
- how copied or researched skill ideas become Scafforge-owned artifacts
- when a downstream repo should receive a skill repair versus a package update

Without this plan, any “meta skill engineering” effort becomes a license for skill sprawl.

## Required deliverables

- a skill-gap intake rubric
- an external-source evaluation rubric, published at `active-plans/12-skill-system-expansion-and-meta-skill-engineering/references/external-source-evaluation-rubric.md`
- packaging rules for new or revised Scafforge skills
- downstream skill injection and repair rules
- regression and readability checks for the skill catalog, wired into a named validation surface rather than prose alone

## Package and adjacent surfaces likely to change during implementation

- `skills/project-skill-bootstrap/SKILL.md`
- `skills/project-skill-bootstrap/references/local-skill-catalog.md`
- `skills/opencode-team-bootstrap/SKILL.md`
- `skills/opencode-team-bootstrap/references/agent-system.md`
- `skills/opencode-team-bootstrap/references/tools-plugins-mcp.md`
- `skills/agent-prompt-engineering/references/anti-patterns.md`
- `skills/agent-prompt-engineering/references/prompt-contracts.md`
- `skills/agent-prompt-engineering/references/weak-model-profile.md`
- `AGENTS.md`
- new package reference docs for skill evolution and validation policy

## Source categories this plan must evaluate

- package-generated evidence from audits, reviews, and repair loops
- copied reference material under `_source-material/asset-pipeline/assetsplanning/pipeline/stolenfromcodex/`
- the adjacent `Meta-Skill-Engineering` repository
- public docs or skill ecosystems used as research inputs

The key rule is that researched material is input, not shippable output.

## Boundary with plan 08

Plan `08` owns the intake, escalation, and evidence packaging for audit-derived package defects. This plan owns the later classification question of whether an already-accepted package-improvement signal implies a skill-system change. For audit-originating inputs, plan `08` decides whether the evidence becomes package work at all; only after that decision does plan `12` decide whether the package work belongs in skill evolution, prompt-contract adjustment, workflow-boundary correction, or another package surface. This boundary must remain consistent with `references/authority-adr.md`.

## Execution gate

- Phase 1 may draft non-audit intake categories immediately, but audit-derived skill-gap intake must not be finalized before plan `08`’s evidence contract exists.
- Phase 2 may proceed once plan `11` has settled the destination for durable policy references, or this plan must explicitly use `active-plans/12-skill-system-expansion-and-meta-skill-engineering/references/` as a temporary staging home and later migrate the durable policy docs.
- Plan `13` should not be implemented before this plan’s evaluation rubric exists, because the Meta-Skill-Engineering repo hardening work is one of the first consumers of the rubric.

## Phase plan

### Phase 1: Define the skill-gap intake path

- [x] Decide how audits, investigations, reviews, and operator feedback submit skill-gap candidates.
- [x] Define the minimum evidence required before a skill gap becomes package work.
- [x] Separate prompt-quality gaps, workflow-boundary gaps, and missing-capability gaps so they are not all handled the same way.
- [x] Record where those skill-gap candidates live while awaiting evaluation.
- [x] Keep audit-derived package-evidence intake delegated to plan `08`; this phase only classifies accepted package work into skill-related versus non-skill-related follow-up.

### Phase 2: Define the external-source evaluation rubric

- [x] Create a checklist for evaluating external skill sources: fit to Scafforge mission, originality needed, overlap risk, weak-model navigability, and licensing/provenance.
- [x] Publish that checklist and decision model at `active-plans/12-skill-system-expansion-and-meta-skill-engineering/references/external-source-evaluation-rubric.md`.
- [x] Require copied bundles and researched repos to be distilled into Scafforge-owned language rather than copied verbatim.
- [x] Evaluate the adjacent `Meta-Skill-Engineering` repository with the same rubric rather than treating its location as unknown.
- [x] Treat that evaluation as a local operator exercise that produces portable package policy docs; the resulting rubric and conclusions must not depend on machine-specific paths.
- [x] Use `references/competence-contract.md` as the canonical bar for weak-model navigability and operational clarity.
- [x] Define an explicit reject/quarantine path for failed provenance or licensing checks, using `active-plans/12-skill-system-expansion-and-meta-skill-engineering/references/rejected-sources.md` as the staging record until plan `11` finalizes a durable home.
- [x] Apply the completed rubric to the in-repo `stolenfromcodex` bundle as the first disposition exercise and record the result before broadening to other sources.
- [x] Explicitly ban blind import of external skills into the package or into generated repos.

### Phase 3: Define the packaging path for new or revised skills

- [x] Document where new package skills belong and how their boundaries are named.
- [x] Define when a capability belongs in `project-skill-bootstrap`, `opencode-team-bootstrap`, `agent-prompt-engineering`, or a new dedicated skill.
- [x] Require every new or changed skill to include provenance, purpose, and validation expectations.
- [x] Require manifest registration in `skills/skill-flow-manifest.json` for any new package skill or skill-backed role created through this lifecycle.
- [x] Keep skill count under control by merging or pruning overlaps instead of only adding new surfaces.

### Phase 4: Define downstream injection and repair policy

- [x] Decide when a generated repo receives a new skill pack at greenfield time versus a later targeted skill repair.
- [x] Ensure repo-local skills and package skills remain separate concepts.
- [x] Define how a downstream repo records that a skill was synthesized, repaired, or refreshed because of package improvements.
- [x] Extend or formally relate this provenance record to the existing `project-skill-bootstrap-completion.md` repair artifact shape rather than inventing an unrelated parallel format.
- [x] Prevent the meta-skill path from silently mutating downstream repos without explicit routing.

### Phase 5: Define regression and readability checks

- [x] Add checks for skill duplication, fuzzy boundaries, and excessive catalog growth.
- [x] Implement those checks by extending `npm run validate:contract` through `scripts/validate_scafforge_contract.py` rather than inventing a separate validation entrypoint first.
- [x] Define the initial enforcement thresholds for catalog growth, overlap, and boundary ambiguity so the checks can fail predictably.
- [x] Use the following draft starter thresholds until real evidence justifies refinement: generated repo baseline skill packs should stay within the smallest navigable set needed for the project; any proposed new package skill that overlaps substantially with an existing skill or only narrows wording without creating a distinct workflow must merge into the existing surface instead of adding a new one; any role or skill proposal that creates a second owner for a truth domain fails immediately pending `references/authority-adr.md` review.
- [x] Add review criteria for weak-model readability and operational clarity, anchored to `references/competence-contract.md`.
- [x] Ensure changed skills update any linked prompt-engineering or team-bootstrap references.
- [x] Confirm every skill change has a bounded validation story, not only text review.
- [x] Treat distillation quality as a required PR-review question in addition to automated checks, because automation can catch structure and drift but not prove originality on its own.

## Forward-reference guardrail

The future `scafforge-meta-skill-engineer-agent` is not created by this plan. If that agent is later introduced, it must be registered in `skills/skill-flow-manifest.json`, checked against `references/authority-adr.md`, and scoped as a bounded package role rather than an open-ended autonomy surface.

## Validation and proof requirements

- a known skill gap can become a bounded improvement task
- external skill material is distilled rather than copied into package output
- new or revised skills remain navigable to weak models
- downstream skill changes are routed explicitly and leave provenance behind
- the skill-governance checks run through a named validation surface and can fail predictably

## Risks and guardrails

- Do not let “meta skill engineering” justify random skill accumulation.
- Do not confuse package skills with repo-local synthesized skills.
- Do not copy external plugin bundles into the product and call them finished.
- Do not add skills when a sharper reference or prompt-contract fix would solve the problem more cleanly.

## Documentation updates required when this plan is implemented

- `AGENTS.md` skill-synthesis and boundary guidance
- `skills/skill-flow-manifest.json`
- project-skill-bootstrap, opencode-team-bootstrap, and prompt-engineering docs
- new skill-evolution policy references
- any generated guidance affected by new or changed skill packs

## Completion criteria

- Scafforge has a disciplined path for discovering, evaluating, packaging, and validating skill improvements
- external knowledge is distilled into Scafforge-owned artifacts
- downstream skill injection is governed instead of ad hoc
- the meta-skill-engineer concept is concrete enough to implement safely
