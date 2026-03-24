# Formalize Scafforge Audit and Four-Report Diagnosis Output

This document is a proposed replacement contract only. It describes the intended future architecture and intentionally diverges from the current live package contract until implementation lands.

## Summary

- Keep `scaffold-kickoff` as the single public entrypoint for greenfield, retrofit, managed repair/update, and diagnosis/review flows.
- Replace the old combined `repo-process-doctor` direction with two host-side skills:
  - `scafforge-audit` for read-only review, diagnosis, report generation, and optional PR evidence intake
  - `scafforge-repair` for consuming audit outputs, applying safe workflow repairs, and escalating intent-changing repairs
- Remove the package CLI surface entirely. Scafforge should be treated as a host-side skill bundle, not a CLI or npm-facing product.
- Add a four-report diagnosis pack for live project repos:
  - `01-initial-codebase-review.md`
  - `02-scafforge-process-failures.md`
  - `03-scafforge-prevention-actions.md`
  - `04-live-repo-repair-plan.md`
  - `manifest.json`
- Treat PR comments, review threads, and check metadata as optional evidence only.
- Remove the standalone refinement route. Any useful refinement behavior should be dispersed into the relevant scaffold, ticket, audit, repair, and generated-repo skills instead of surviving as a separate flow.

## Architectural Direction

### Public entrypoint

- `scaffold-kickoff` stays public.
- `scaffold-kickoff` classifies the run as one of:
  - greenfield scaffold
  - retrofit scaffold
  - managed repair/update
  - diagnosis/review of an in-progress or claimed-complete project
- Diagnosis/review routes internally to `scafforge-audit`.
- Repair/update routes internally to `scafforge-repair`.

### Skill split

- `scafforge-audit`
  - read-only professional codebase review
  - workflow/process/artifact/agent diagnosis
  - optional PR evidence intake
  - four-report pack generation
- `scafforge-repair`
  - consume audit outputs, especially Report 4
  - apply safe Scafforge-side or managed-surface repairs
  - escalate intent-changing repairs for approval
  - record provenance and contract-version change state
- `pr-review-ticket-bridge` should be folded into `scafforge-audit` unless a deliberately narrow PR-only helper is still wanted.

### Generated repo-local review skill

- The generated repo-local `review-audit-bridge` concept should remain generated-repo functionality, not a Scafforge core skill.
- Ownership for that generated skill should sit under `project-skill-bootstrap` and its generated skill tree.
- If the generated review skill needs heavier guidance, examples, or reference material, that content should live in the generated skill's `references/` subfolder rather than bloating the skill body.
- Its job is to help the live repo review itself, validate weak implementations, recommend new remediation tickets, and write a process log folder explaining what went wrong in the project workflow.

## Four-Report Contract

- Report 1: validated codebase review findings, severity, file references, and verification gaps
- Report 2: process failure diagnosis mapping Report 1 issues back to specific Scafforge skills, contracts, templates, or generated surfaces
- Report 3: Scafforge-side prevention actions needed to stop recurrence in future repos
- Report 4: live-repo remediation plan after Scafforge is updated, including workflow, managed-surface, and ticket changes

Default output location:

- `<subject-repo>/diagnosis/<YYYYMMDD-HHMMSS>/`

Required files:

- `01-initial-codebase-review.md`
- `02-scafforge-process-failures.md`
- `03-scafforge-prevention-actions.md`
- `04-live-repo-repair-plan.md`
- `manifest.json`

Optional supporting files:

- `logs/`
- captured command output or verification traces when useful

## Key Product Changes

- Create or rename host-side skills so the package contract uses `scafforge-audit` and `scafforge-repair`.
- Update `scaffold-kickoff` routing and completion rules to use the new split.
- Remove the package CLI wrapper, npm-facing framing, and all CLI-oriented documentation, package metadata, and script references.
- Expand audit outputs to include the four-report pack and a machine-readable manifest inside the subject repo's `diagnosis/` folder.
- Fold optional PR evidence intake into the audit contract instead of keeping it as the center of a separate primary workflow.
- Add a Scafforge contract-history or change-reference surface so repair can compare:
  - the repo's recorded workflow/process version
  - the current Scafforge package contract version
- Remove the standalone refinement route and distribute any genuinely useful refinement logic into the relevant package skills and generated-repo skills.

## Ticket Addition and Repair Follow-Up

The current ticket system exists, but it is fragmented across multiple surfaces.

What already exists:

- `ticket-pack-builder` can bootstrap or refine a backlog
- generated repos already have guarded ticket-creation concepts through `ticket_create`
- existing doctor and PR-review flows already expect remediation tickets in some cases

What is missing:

- an explicit post-audit/post-repair ticket flow as a first-class contract
- a clear contract for how audit findings become canonical remediation tickets
- documented routing between audit outputs, repair actions, and backlog updates

Recommended plan addition:

- refine `ticket-pack-builder` so it explicitly supports remediation-oriented follow-up after audit and repair
- require guarded ticket creation where the generated repo provides the relevant tool and workflow state
- have `scafforge-audit` emit ticket recommendations in Report 4, and optionally a machine-readable recommended-ticket payload for later consumption
- have `scafforge-repair` route through the ticket system after repair work when new remediation or verification tickets are required
- ensure the generated repo-local review skill can recommend poor-implementation tickets and process-log output without becoming the canonical ticket owner itself

## Skill-Creation Workstream

If `scafforge-audit` and `scafforge-repair` are created as genuinely new skills rather than simple in-place edits, a structured skill-design pass should be part of implementation.

Recommended use of the local `skill-creator` guidance:

- use it during the package refactor that creates the new skill folders, metadata, prompts, and supporting resources
- do not treat it as a runtime dependency of Scafforge itself
- use it to keep the new skills concise, single-purpose, and non-overlapping

## Evidence and Non-Taint Direction

Diagnosis must be read-only in the sense that it must not implement fixes or alter the project's source/process state as part of the review.

That does **not** mean "never execute checks."

Clarified rule:

- forbidden during diagnosis:
  - source edits
  - workflow/ticket edits
  - managed-surface rewrites
  - repair execution
- allowed during diagnosis:
  - verification commands
  - tests
  - inspection scripts
  - artifact capture for reports
  - creation of the repo-local `diagnosis/` folder and its report/log outputs as the sole intentional file-creation exception

Transient runtime byproducts such as logs, caches, or bytecode are not the same category of taint as implementation changes. The real prohibition is against semantic mutation of the live project while it is being used as evidence.

## Execution Check Fixes Needed Before Audit Expansion

Before the diagnosis workflow depends on the current execution audit, fix these issues:

- startup-import checks must validate the real startup module, not just package-root import success
- ordinary failing tests must be detected by running the real suite, not just collection
- interpreter and pytest resolution must be cross-platform, including `.venv/bin/*` and `.venv/Scripts/*`
- the `smoke_test` workflow/ticket status contract must be normalized across templates, ticket docs, and audit logic

Current short-code names such as `EXEC001` should be treated as current internal identifiers only or renamed to plain-English runtime/test labels in user-facing outputs.

## Validation Plan

- update validators to require the new skill names, routing, report contract, and reference docs
- add smoke coverage for diagnosis-pack creation in the subject repo's `diagnosis/` folder
- add fixture-based coverage for runtime/test execution findings
- add validation for ticket-follow-up routing after audit/repair
- add checks that the package no longer exposes or documents the removed CLI surface
- add checks that no standalone refinement route remains in the documented flow

## Assumptions

- Diagnosis remains a host-side Scafforge capability, not a Scafforge core generated-repo skill by default.
- `scaffold-kickoff` remains the single public entrypoint.
- PR metadata is optional and may be absent.
- The CLI should be removed, not expanded.
- The package should be treated as a skill bundle rather than an npm-facing product.
- `repo-process-doctor` and `pr-review-ticket-bridge` are expected to be superseded or folded into the clearer audit/repair architecture.
- The generated repo-local review skill remains under `project-skill-bootstrap`, not as a top-level Scafforge core skill.

## Supporting Docs

This plan should be read together with:

- [DIAGNOSIS-ARCHITECTURE-AND-NAMING-PROPOSAL.md](C:/Users/PC/Documents/GitHub/Scafforge/out/DIAGNOSIS-ARCHITECTURE-AND-NAMING-PROPOSAL.md)
- [DIAGNOSIS-PLAN-ADDENDUM.md](C:/Users/PC/Documents/GitHub/Scafforge/out/DIAGNOSIS-PLAN-ADDENDUM.md)
- [DIAGNOSIS-EVIDENCE-AND-NON-TAINT-RULES.md](C:/Users/PC/Documents/GitHub/Scafforge/out/DIAGNOSIS-EVIDENCE-AND-NON-TAINT-RULES.md)
- [REFERENCE-UPDATE-INVENTORY.md](C:/Users/PC/Documents/GitHub/Scafforge/out/REFERENCE-UPDATE-INVENTORY.md)
