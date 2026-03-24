# PR Review Workflow

Use this playbook when `scafforge-audit` receives PR comments, review threads, check failures, or external bug claims.

The goal is to turn noisy review input into evidence-backed diagnosis output without letting review chatter become canonical state.

## Inputs

- pull request diff, commits, and changed files when available
- review comments, summary notes, or issue claims
- current repo files and workflow surfaces
- audit outputs and diagnosis-pack scope when the review is part of a broader diagnosis

## Triage sequence

### 1. Normalize each claim

Convert each external claim into one candidate finding with:

- a short claim id
- the source comment, thread, or external note
- the allegedly affected file or workflow surface
- the claimed impact

Do not merge unrelated claims into one item.

### 2. Inspect current repo reality

For each candidate finding:

- read the current implementation or workflow surface directly
- compare the claim against the current repo contract
- check whether the comment is outdated relative to later commits or regenerated surfaces
- reproduce the behavior when practical

### 3. Assign a review disposition

Each candidate must end in exactly one state:

- `valid`
- `partially_valid`
- `outdated`
- `invalid`
- `blocked` when evidence is missing and the reviewer cannot complete verification

### 4. Grade surviving findings

For every `valid` or `partially_valid` item, assign:

- severity: `critical`, `major`, or `minor`
- evidence grade: `observed`, `reproduced`, `inferred`, `external-only`, or `missing`
- ownership classification:
  - `Scafforge package defect`
  - `generated-repo managed-surface drift`
  - `repo-specific customization drift`
  - `subject-repo source bug`

### 5. Route the result into the diagnosis pack

- Put validated implementation failures into Report 1
- Map workflow-contract or package-root causes into Report 2
- Put future-package prevention work into Report 3
- Put subject-repo remediation, repair prerequisites, and ticket proposals into Report 4
- Record rejected, outdated, or blocked claims so the diagnosis pack explains why they did not survive

## Ticket proposal rule

Review validation during audit proposes follow-up work. It does not directly mutate the live repo backlog.

Use Report 4 and the optional machine-readable ticket payload as the canonical handoff surface for:

- remediation tickets
- decision tickets
- reverification tickets

## Practical rule

A PR comment is evidence input, not truth.

It becomes a diagnosis finding only after the current repo proves it.
