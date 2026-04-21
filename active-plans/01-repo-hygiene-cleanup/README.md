# Repo Hygiene And Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Turn `active-plans/` into a stable, low-ambiguity planning system where canonical plans, supporting references, and root summaries are easy for both humans and weak models to distinguish.

**Architecture:** Keep `active-plans/` as a two-layer system. Numbered folders and root summaries are the canonical execution program; `_source-material/` remains in-repo as active supporting documentation. The work here is not “archive cleanup.” It is information architecture, placement rules, and contributor hygiene for future Scafforge planning.

**Tech Stack / Surfaces:** Markdown documentation, `active-plans/`, root package docs, `AGENTS.md`, repository contributor guidance.
**Depends On:** Nothing.
**Unblocks:** Every other plan, because this plan defines how the portfolio is maintained.
**Primary Sources:** `active-plans/docscleanup.md`, `active-plans/_source-material/repo-hygiene/docscleanup-original.md`, `AGENTS.md`, `active-plans/README.md`.

---

## Why this plan exists

The first planning pass proved the core problem: raw notes, copied research, and active implementation guidance were all mixed together. Even after the folder split, the operating rule still needs to become explicit enough that a later agent cannot accidentally turn `active-plans/` back into a draft dump or misclassify active documents as removable noise.

This plan therefore owns:

- the canonical-plan versus supporting-reference rule
- the placement rule for new planning material
- the root navigation rules for `active-plans/`
- the maintenance checklist that prevents drift after later plans are implemented

## Required deliverables

- a documented classification rule for every document under `active-plans/`
- a stable root index that explains canonical versus supporting surfaces in one screen
- a repeatable naming rule for future plan folders, reference notes, and reports
- package-doc wording that matches the new `active-plans/` structure
- a verification pass proving a new contributor can identify the real plans quickly

## Package surfaces likely to change during implementation

- `active-plans/README.md`
- `active-plans/docscleanup.md`
- `active-plans/WORK-JOURNAL.md`
- `active-plans/FULL-REPORT.md`
- `active-plans/_source-material/README.md`
- `active-plans/*/README.md` where folder roles need clearer labels
- `AGENTS.md`
- `README.md` and `USERGUIDE.md` if they reference the planning area

## Boundaries and non-goals

### In scope

- clarifying document roles
- reducing root-level ambiguity
- standardizing how future plans are created and updated
- ensuring the package docs agree on what `active-plans/` is for

### Out of scope

- moving active documents out of the repository
- changing runtime package behavior
- deleting `_source-material/`
- turning `active-plans/` into a generated state machine

## Phase plan

### Phase 1: Classify the current planning surfaces

- [ ] Build a path-by-path inventory of everything under `active-plans/` grouped as `canonical plan`, `root summary`, `supporting reference`, or `historical provenance`.
- [ ] Confirm every numbered folder has exactly one primary implementation plan document and that the document is identifiable at a glance.
- [ ] Review root-level markdown files and remove any wording that implies `_source-material/` is disposable or external-only.
- [ ] Record any files that still act like hidden canonical plans and either promote them into a numbered folder or relabel them as references.

### Phase 2: Codify the placement rules

- [ ] Document the rule that new implementation planning work starts in a numbered folder, not at the root.
- [ ] Document the rule that research dumps, copied docs, and raw notes go into `_source-material/` or a plan-local `references/` note, never directly into the canonical plan body.
- [ ] Document the rule that root-level files are reserved for portfolio-wide navigation, reporting, or journal entries.
- [ ] Add a naming convention for new plan folders and their companion reference files so future additions do not regress into ad hoc labels.

### Phase 3: Align package docs with the planning layout

- [ ] Update `AGENTS.md` so its `active-plans/` description matches the two-layer structure and clearly states that `_source-material/` is still active in-repo documentation.
- [ ] Update any root docs that still imply `active-plans/` is a loose scratch area.
- [ ] Add a concise “where planning material belongs” note to the package contributor documentation path.
- [ ] Ensure the package docs never describe numbered plan folders as optional summaries; they are the working program.

### Phase 4: Add contributor and agent hygiene rules

- [ ] Add a maintenance checklist for future planning edits: create/update the numbered folder plan, update the root index if sequencing changes, update the report if the program shape changes, and add source material only where it improves traceability.
- [ ] Add an anti-pattern list covering: hidden canonical plans in `_source-material/`, duplicate summaries at the root, and plan folders with no actionable implementation body.
- [ ] Require every plan folder to show status explicitly so “active but not started” versus “implemented and archived” is obvious.
- [ ] Define how completed plans leave `active-plans/` and where their historical copies live, while keeping the active set readable.

### Phase 5: Verify that the planning area is actually usable

- [ ] Run a newcomer-context check using only `active-plans/README.md` and one numbered folder to confirm the portfolio is navigable.
- [ ] Run a wording pass to eliminate contradictory phrases like `archive candidate`, `temporary staging area`, or `future removal` from authored docs.
- [ ] Verify that every numbered folder has a clear summary, dependencies, and TODO status.
- [ ] Record the final rule set in `WORK-JOURNAL.md` and summarize the outcome in `FULL-REPORT.md`.

## Validation and proof requirements

- a reader should be able to identify the canonical plans within 30 seconds
- `AGENTS.md`, `active-plans/README.md`, and `docscleanup.md` must agree on the same boundary model
- no authored document in `active-plans/` should imply `_source-material/` is an automatic removal queue
- future-plan placement rules must be explicit enough that another agent can follow them without interpretation

## Risks and guardrails

- Do not solve this by stripping context. A clean planning area with no useful provenance is worse than a noisy one.
- Do not create a new root-level “meta tracker” that duplicates the numbered plan folders.
- Do not invent generated-repo workflow-state semantics for package planning.
- Keep the system legible to weak models: few layers, explicit labels, one obvious place for active instructions.

## Documentation updates required when this plan is implemented

- `active-plans/README.md`
- `active-plans/docscleanup.md`
- `active-plans/_source-material/README.md`
- `AGENTS.md`
- `README.md` or `USERGUIDE.md` if planning guidance is exposed there

## Completion criteria

- every numbered plan folder has a clearly marked TODO-state implementation plan
- root planning docs agree on the canonical-versus-supporting-reference model
- no hidden canonical instructions remain buried in supporting material
- future contributors can tell where to add plans, reports, and source notes without guessing
