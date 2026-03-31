# Diagnosis Architecture and Naming Proposal

This document is a proposed replacement contract only. It describes the intended future architecture and naming direction, not the current implemented package state.

## Purpose

This document refines the diagnosis plan in `DIAGNOSIS-4-REPORT-PLAN.md`.

It proposes the package architecture, naming direction, and routing model that should govern the later implementation work.

## Core Decision

The clean direction is to stop expanding `repo-process-doctor` as a combined diagnosis/repair skill and replace it with two clearer host-side skills:

- `scafforge-audit`
- `scafforge-repair`

This is not just a wording change. It is a boundary correction.

## Public Entry Model

### `scaffold-kickoff` remains the single public entrypoint

Users should not need to decide between internal host-side skills.

`scaffold-kickoff` should classify the request as:

1. Greenfield scaffold
2. Retrofit scaffold
3. Managed repair/update
4. Diagnosis/review of an in-progress or claimed-complete repo

Then it should route internally to the correct downstream path.

This preserves one public mental model while still allowing the package to separate responsibilities internally.

### No standalone refinement route

The package should not preserve `refinement` as a separate routed flow.

Reason:

- the scaffold contract should be strong enough on the first pass that repeated package-level refinement is not a core operating model
- any genuinely useful refinement behavior should be redistributed into the relevant skills instead of surviving as a loose extra route

## Proposed Host-Side Skill Shape

### `scafforge-audit`

Role:

- read-only host-side diagnosis and review
- professional codebase review
- workflow/process/artifact/agent diagnosis
- optional PR evidence intake
- four-report diagnosis output

This skill should not:

- implement fixes
- mutate the subject repo as part of diagnosis, except for the intentional `diagnosis/` output folder
- apply workflow repairs
- become a generated repo-local skill by default

### `scafforge-repair`

Role:

- consume audit outputs, especially Report 4
- apply safe Scafforge-side or managed-surface repairs
- escalate intent-changing repairs for approval
- record provenance and contract-version changes
- trigger ticket follow-up when repair work creates new remediation or verification work

This skill should not:

- perform the primary diagnosis pass
- become the main evidence-gathering or review surface
- silently change workflow contracts without leaving clear version/provenance state

## Generated Repo-Local Review Skill

The generated repo-local `review-audit-bridge` should not be treated as a Scafforge core skill.

Recommended direction:

- keep it in the generated repo skill tree under `project-skill-bootstrap`
- let `project-skill-bootstrap` own its creation, repair, and documentation
- place heavier instructions, heuristics, or examples in that generated skill's `references/` subfolder if the skill body would otherwise become too large
- let it review the live repo, identify weak implementations, recommend remediation tickets, and emit a log folder recording what went wrong in the development process

This keeps the host-side audit capability and the generated repo-local self-review capability clearly separated.

## Naming Rationale

### Why replace `repo-process-doctor`

Problems with the current name:

- it is vague
- it mixes diagnosis and mutation
- it sounds process-only even though the desired audit must also review code, artifacts, workflow evidence, and optional PR inputs

Benefits of the new names:

- `scafforge-audit` clearly reads as review and diagnosis
- `scafforge-repair` clearly reads as mutation and follow-up
- the pair makes the analysis/action boundary obvious

### Why fold `pr-review-ticket-bridge`

PR evidence is useful, but it is optional evidence, not a complete workflow on its own.

Recommended direction:

- absorb PR comment validation and review triage into `scafforge-audit`
- keep a standalone bridge only if a deliberately narrow PR-only helper still proves valuable after the wider audit flow exists

## CLI Position

The package CLI should be removed.

Reason:

- Scafforge is fundamentally a host-side skill bundle
- the CLI does not replace the LLM reasoning required for scaffold generation, diagnosis, tickets, or documentation synthesis
- the current CLI only wraps scripts and adds conceptual noise
- keeping it encourages the wrong mental model of Scafforge as a script-first tool rather than a host-orchestrated skill system

Implication:

- remove the package CLI wrapper
- remove CLI-specific docs and commands
- do not design the audit/repair architecture around CLI entrypoints
- do not preserve npm-facing packaging concerns as a design constraint

## Diagnosis Output Position

Diagnosis output should live inside the subject repo as the single intentional exception to the normal non-mutation rule.

Recommended location:

- `<subject-repo>/diagnosis/<YYYYMMDD-HHMMSS>/`

Recommended contents:

- the four reports
- `manifest.json`
- optional `logs/` and captured verification output where useful

## Ticketing Direction

Audit and repair need a clearer ticket follow-up path, but the current system is fragmented rather than absent.

Current fragments already exist across:

- `ticket-pack-builder`
- generated repo guarded ticket-creation tools
- existing doctor guidance
- existing PR-review triage surfaces

Recommended architecture:

- `scafforge-audit` produces ticket recommendations in Report 4
- `scafforge-repair` consumes those recommendations after Scafforge-side changes are made
- backlog updates route through `ticket-pack-builder` and the generated repo's guarded ticket-creation surfaces where they exist
- the generated repo-local review skill can propose poor-implementation tickets and process logs, but it does not become the canonical ticket owner

This means `ticket-pack-builder` likely needs refinement so it explicitly covers remediation-oriented follow-up, not just backlog bootstrap.

## Contract-Version Direction

`scafforge-repair` should be contract-version aware.

It should compare:

- the workflow/process version recorded in the subject repo
- the current Scafforge package contract version

To support that, the package should maintain a change-reference surface that explains:

- what changed
- when it changed
- what managed surfaces or workflow assumptions are affected

## Skill-Creation Direction

If `scafforge-audit` and `scafforge-repair` are created as new skills instead of in-place renames, the package refactor should explicitly use the local `skill-creator` guidance.

Reason:

- the new skills should be single-purpose
- the prompt metadata and supporting references should be regenerated cleanly
- the split should reduce skill bloat instead of merely renaming it

This is an implementation aid for the package refactor, not a runtime dependency.

## Recommended Supporting Artifacts

The support docs under `out/` should include:

- `DIAGNOSIS-PLAN-ADDENDUM.md`
- `DIAGNOSIS-EVIDENCE-AND-NON-TAINT-RULES.md`
- `REFERENCE-UPDATE-INVENTORY.md`

## Recommended Decision

The cleanest long-term shape is:

- keep `scaffold-kickoff` as the only public entrypoint
- replace `repo-process-doctor` with `scafforge-audit` and `scafforge-repair`
- fold `pr-review-ticket-bridge` into `scafforge-audit` by default
- keep generated repo-local `review-audit-bridge` under `project-skill-bootstrap`
- remove the CLI and treat Scafforge as a skill bundle only
- remove the standalone refinement route
- refine `ticket-pack-builder` to support post-audit/post-repair ticket follow-up
- use `skill-creator` guidance during the package refactor that creates the new skill surfaces
