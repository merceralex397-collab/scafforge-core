---
name: scafforge-pivot
description: Route a midstream feature, design, architecture, or workflow change through Scafforge's host-side pivot flow. Use when an existing repo needs a controlled contract update that changes canonical truth, ticket lineage, or managed workflow surfaces without collapsing into improvised repair or ad hoc backlog edits.
---

# Scafforge Pivot

Use this skill when an existing repo needs a midstream change that is larger than routine ticket refinement but is not just workflow repair.

This is the host-side pivot surface. It classifies the requested change, updates canonical truth first, records which surfaces are now stale, routes the required downstream refresh work, and requires a post-pivot verification pass before handoff.
Use [../../references/competence-contract.md](../../references/competence-contract.md) as the bar for whether the repo still exposes one clear legal next move after the pivot.

## When to use this skill

- `scaffold-kickoff` classifies the request as a pivot
- the user says to add a feature, expand scope, change the design, change the architecture, or alter the workflow contract midstream
- the requested change crosses canonical brief truth, ticket lineage, prompts, local skills, agent team design, or managed workflow surfaces

If the repo only needs diagnosis, route to `../scafforge-audit/SKILL.md`.
If the repo only needs managed workflow repair with no project-truth change, route to `../scafforge-repair/SKILL.md`.

## Pivot classes

- `feature-add`
- `feature-expand`
- `design-change`
- `architecture-change`
- `workflow-change`

## Procedure

### 1. Classify the pivot and scope impact

Read the current repo truth first:

- `docs/spec/CANONICAL-BRIEF.md`
- `tickets/manifest.json`
- `.opencode/state/workflow-state.json`
- `.opencode/meta/bootstrap-provenance.json`
- `START-HERE.md`

Classify the pivot before editing anything.
Record which class applies, what changed, and which current surfaces are now stale.

Do not treat a true design or architecture pivot as ordinary backlog refinement.
Do not treat a pure managed-surface repair as a pivot when canonical project truth did not change.

### 2. Update canonical truth first

Before refreshing any derived or managed surfaces:

1. update `docs/spec/CANONICAL-BRIEF.md`
2. append a `Pivot History` entry that records:
   - pivot class
   - requested change
   - accepted decisions
   - unresolved follow-up
   - affected contract families
3. note whether the change alters workflow only, product behavior, architecture, or multiple layers

Do not regenerate tickets, prompts, local skills, or restart surfaces against stale brief truth.

### 3. Emit the stale-surface map

Produce a machine-readable stale-surface map that classifies affected surfaces as:

- `stable`
- `replace`
- `regenerate`
- `ticket_follow_up`
- `human_decision`

At minimum, classify these families:

- canonical brief and truth docs
- repo-local skills
- agent prompts and team layout
- managed workflow tools and prompts
- ticket graph and lineage
- restart surfaces

If workflow surfaces drifted, route the managed refresh through `../scafforge-repair/SKILL.md` instead of open-coding the same repair logic here.

### 4. Refresh only the affected downstream surfaces

Use the stale-surface map to route the smallest coherent follow-on set:

- `../project-skill-bootstrap/SKILL.md` when repo-local skills need regeneration
- `../opencode-team-bootstrap/SKILL.md` when the agent team, tools, or allowlists need redesign
- `../agent-prompt-engineering/SKILL.md` when prompt behavior or delegation rules changed
- `../ticket-pack-builder/SKILL.md` when tickets must be refined, reopened, superseded, or reconciled
- `../scafforge-repair/SKILL.md` only when managed workflow surfaces drifted and need safe managed refresh

Do not let `scafforge-pivot` become a second scaffold engine or a second repair engine.

### 5. Repair ticket lineage explicitly

When the pivot invalidates existing ticket assumptions:

- supersede tickets whose acceptance no longer matches the new brief
- reopen tickets that remain valid but are no longer complete under the new design
- create follow-up or decision tickets when new work is introduced
- reconcile stale lineage when old source/follow-up relationships no longer reflect the pivot

Do not leave pre-pivot tickets pretending to satisfy the new design.

### 6. Require post-pivot verification

Before handoff, verify that the pivot left the repo continuable:

- one legal next move still exists
- canonical brief truth and restart surfaces agree
- stale placeholder local skills were not reintroduced
- ticket lineage reflects the pivot truthfully
- managed workflow surfaces still agree on lifecycle semantics

If the pivot included transcript-backed workflow defects, reuse the normal verification basis instead of dropping the original causal evidence.

### 7. Publish a truthful handoff

After pivot work and verification are complete, continue to `../handoff-brief/SKILL.md`.

The handoff must state that a pivot occurred, which surfaces changed, and what follow-up still remains.

## Required outputs

- classified pivot type
- updated `docs/spec/CANONICAL-BRIEF.md` with `Pivot History`
- machine-readable stale-surface map
- explicit downstream refresh decisions
- ticket lineage updates or follow-up routing
- post-pivot verification result
- truthful restart surface inputs for handoff

## Output contract

Before leaving this skill, confirm all of these are true:

- canonical brief truth was updated before any derived refresh work
- the stale-surface map exists and matches the requested pivot
- repair was used only for managed workflow refresh, not for product-truth changes
- ticket lineage and restart surfaces no longer present stale pre-pivot assumptions
- post-pivot verification ran before handoff

## Rules

- Update canonical truth before derived surfaces
- Keep pivot classification explicit
- Use repair only for managed workflow refresh, not for product-truth changes
- Do not hide a pivot inside generic ticket refinement
- Do not leave stale tickets or restart surfaces behind
- Do not skip post-pivot verification
