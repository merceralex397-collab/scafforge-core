# Diagnosis Evidence and Non-Taint Rules

This document is a proposed diagnosis-contract clarification only. It describes how the future audit flow should treat evidence and non-taint, not the current fully implemented package behavior.

## Purpose

This document clarifies what "read-only diagnosis" means for the proposed `scafforge-audit` flow.

The important distinction is between:

- evidence gathering and verification
- semantic mutation of the live project

These are not the same thing.

## Core Rule

Diagnosis must not implement fixes or alter the live project's managed state as part of the review.

The prohibition is against **semantic mutation**, not against verification.

## What Counts as Taint

For diagnosis purposes, the following should count as taint and must not occur:

- source-code edits
- documentation edits that change repo intent or tracked state
- ticket creation or modification inside the subject repo
- workflow-state changes
- managed-surface rewrites
- automatic process repairs
- generated-file rewrites that change what the repo is

These actions taint the repo because they change the evidence under review.

## What Does Not Count as Taint

The following are allowed during diagnosis:

- reading files
- parsing manifests and workflow state
- running tests
- running linters
- running startup/import checks
- running inspection scripts
- capturing command output into the diagnosis pack
- collecting PR comments or CI metadata when available
- creating the dedicated repo-local `diagnosis/` folder and its report/log outputs

These are verification actions, not repairs.

## Runtime Side Effects

Some verification actions may create operational byproducts such as:

- `.pytest_cache`
- `__pycache__`
- temporary logs
- command output files in the diagnosis directory

These are not the same category as semantic taint.

Recommended handling:

- prefer commands that minimize avoidable byproducts
- write diagnosis outputs into the subject repo's dedicated `diagnosis/` directory
- record noteworthy byproducts in the diagnosis manifest when relevant
- avoid treating ordinary runtime residue as equivalent to source/process edits

## Diagnosis Output Exception

The sole intentional exception to the non-mutation rule is the creation of diagnosis artifacts inside the live repo.

Recommended location:

- `<subject-repo>/diagnosis/<YYYYMMDD-HHMMSS>/`

Recommended contents:

- the four reports
- `manifest.json`
- optional `logs/`
- captured verification output when useful

This exception exists so diagnosis results stay with the subject repo without permitting source or workflow mutation.

## Ticket and Workflow Boundary

Diagnosis should recommend ticket additions and workflow changes, not apply them.

That means:

- Report 4 may recommend remediation tickets
- `scafforge-repair` may later trigger the ticket follow-up path
- `scafforge-audit` should not itself create or edit live repo tickets during diagnosis

## Evidence Grades

All reports should use a simple evidence scale:

- `observed`
- `reproduced`
- `inferred`
- `external-only`
- `missing`

Meaning:

- `observed`: directly visible in the repo or workflow artifacts
- `reproduced`: confirmed by executing a verification step
- `inferred`: strong conclusion derived from available evidence, but not directly reproduced
- `external-only`: based on outside evidence such as PR commentary or external review context
- `missing`: expected evidence was not available

## Result States

The diagnosis pack should distinguish:

- `validated failures found`
- `no validated failures found`
- `inconclusive or partially verified`

This prevents "could not fully verify" from being mistaken for "the repo is healthy."

## Scope Boundary

These non-taint rules are diagnosis rules, not repair rules.

Later repair flows may mutate managed surfaces under the guarded repair contract. Diagnosis may not.

## Practical Rule of Thumb

If the action changes what the repo **is**, it is taint.

If the action only checks what the repo **does**, it is diagnosis.
