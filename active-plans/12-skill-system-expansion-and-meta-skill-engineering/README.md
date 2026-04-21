# Skill System Expansion And Meta Skill Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Create the disciplined path by which Scafforge learns from failures, external skill research, and the Meta-Skill-Orchestration concept without degenerating into random skill sprawl.

**Architecture:** Skill evolution becomes a bounded lifecycle: detect gap -> evaluate evidence -> distill external knowledge -> package the change into Scafforge-owned skill assets -> validate it -> decide whether downstream repos need an immediate skill repair. The system must preserve the package-versus-repo skill boundary and keep the skill catalog navigable for weak models.

**Tech Stack / Surfaces:** `skills/project-skill-bootstrap/`, `skills/opencode-team-bootstrap/`, `skills/agent-prompt-engineering/`, package references, future skill-validation surfaces, external skill-source repos and copied reference bundles.
**Depends On:** `08-meta-improvement-loop` for package evidence intake; `11-repository-documentation-sweep` for durable documentation structure.
**Unblocks:** safer skill evolution, downstream skill repair policy, and any future `scafforge-meta-skill-engineer-agent`.
**Primary Sources:** user requirement for Meta-Skill-Orchestration, `_source-material/asset-pipeline/assetsplanning/pipeline/stolenfromcodex/`, `skills/project-skill-bootstrap/references/local-skill-catalog.md`, package skill-boundary rules in `AGENTS.md`.

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
- an external-source evaluation rubric
- packaging rules for new or revised Scafforge skills
- downstream skill injection and repair rules
- regression and readability checks for the skill catalog

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
- the external Meta-Skill-Orchestration repository once its exact repo path/URL is recorded in package references
- public docs or skill ecosystems used as research inputs

The key rule is that researched material is input, not shippable output.

## Phase plan

### Phase 1: Define the skill-gap intake path

- [ ] Decide how audits, investigations, reviews, and operator feedback submit skill-gap candidates.
- [ ] Define the minimum evidence required before a skill gap becomes package work.
- [ ] Separate prompt-quality gaps, workflow-boundary gaps, and missing-capability gaps so they are not all handled the same way.
- [ ] Record where those skill-gap candidates live while awaiting evaluation.

### Phase 2: Define the external-source evaluation rubric

- [ ] Create a checklist for evaluating external skill sources: fit to Scafforge mission, originality needed, overlap risk, weak-model navigability, and licensing/provenance.
- [ ] Require copied bundles and researched repos to be distilled into Scafforge-owned language rather than copied verbatim.
- [ ] Decide how the Meta-Skill-Orchestration repo will be documented and evaluated once its exact location is recorded.
- [ ] Explicitly ban blind import of external skills into the package or into generated repos.

### Phase 3: Define the packaging path for new or revised skills

- [ ] Document where new package skills belong and how their boundaries are named.
- [ ] Define when a capability belongs in `project-skill-bootstrap`, `opencode-team-bootstrap`, `agent-prompt-engineering`, or a new dedicated skill.
- [ ] Require every new or changed skill to include provenance, purpose, and validation expectations.
- [ ] Keep skill count under control by merging or pruning overlaps instead of only adding new surfaces.

### Phase 4: Define downstream injection and repair policy

- [ ] Decide when a generated repo receives a new skill pack at greenfield time versus a later targeted skill repair.
- [ ] Ensure repo-local skills and package skills remain separate concepts.
- [ ] Define how a downstream repo records that a skill was synthesized, repaired, or refreshed because of package improvements.
- [ ] Prevent the meta-skill path from silently mutating downstream repos without explicit routing.

### Phase 5: Define regression and readability checks

- [ ] Add checks for skill duplication, fuzzy boundaries, and excessive catalog growth.
- [ ] Add review criteria for weak-model readability and operational clarity.
- [ ] Ensure changed skills update any linked prompt-engineering or team-bootstrap references.
- [ ] Confirm every skill change has a bounded validation story, not only text review.

## Validation and proof requirements

- a known skill gap can become a bounded improvement task
- external skill material is distilled rather than copied into package output
- new or revised skills remain navigable to weak models
- downstream skill changes are routed explicitly and leave provenance behind

## Risks and guardrails

- Do not let “meta skill engineering” justify random skill accumulation.
- Do not confuse package skills with repo-local synthesized skills.
- Do not copy external plugin bundles into the product and call them finished.
- Do not add skills when a sharper reference or prompt-contract fix would solve the problem more cleanly.

## Documentation updates required when this plan is implemented

- `AGENTS.md` skill-synthesis and boundary guidance
- project-skill-bootstrap, opencode-team-bootstrap, and prompt-engineering docs
- new skill-evolution policy references
- any generated guidance affected by new or changed skill packs

## Completion criteria

- Scafforge has a disciplined path for discovering, evaluating, packaging, and validating skill improvements
- external knowledge is distilled into Scafforge-owned artifacts
- downstream skill injection is governed instead of ad hoc
- the meta-skill-engineer concept is concrete enough to implement safely
