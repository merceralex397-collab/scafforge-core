# Diagnosis Implementation Todos

This working checklist turns `DIAGNOSIS-4-REPORT-PLAN.md` into staged package work.

It is an implementation tracker, not a new contract document.

## Stage 1: Baseline audit and migration map

- [x] Read `DIAGNOSIS-4-REPORT-PLAN.md` as the primary contract target
- [x] Read supporting diagnosis docs for architecture, addenda, evidence, and reference fallout
- [x] Audit current package surfaces against the target contract
- [x] Identify the highest-impact files for routing, skill, script, validator, and doc changes
- [x] Preserve awareness of unrelated dirty-worktree files and avoid touching them unless required

## Stage 2: Split diagnosis and repair architecture

- [x] Replace package-level `repo-process-doctor` ownership with `scafforge-audit` and `scafforge-repair`
- [x] Update `scaffold-kickoff` to classify greenfield, retrofit, managed repair/update, and diagnosis/review
- [x] Remove standalone refinement as a routed package flow
- [x] Fold package-level PR evidence handling into `scafforge-audit` by default
- [x] Keep generated repo-local `review-audit-bridge` clearly owned by `project-skill-bootstrap`
- [x] Regenerate or rewrite skill metadata so new skill names and prompts are coherent

## Stage 3: Remove CLI-facing package surface and align automation

- [x] Remove the package `bin` exposure and CLI-oriented product framing
- [x] Delete or retire `bin/scafforge.mjs`
- [x] Update `package.json` description, files, and scripts to match a skill-bundle product
- [x] Re-home audit and repair scripts under the new skill layout
- [x] Align help text and change-summary wording with the new audit/repair contract

## Stage 4: Update package contract, templates, and ticket follow-up surfaces

- [x] Update `AGENTS.md`, `README.md`, and `skills/skill-flow-manifest.json`
- [x] Update `ticket-pack-builder` for explicit post-audit/post-repair remediation follow-up
- [x] Update `project-skill-bootstrap` and generated review-skill wording for repo-local ownership
- [x] Update generated template docs, commands, agents, and process docs for audit/repair terminology
- [x] Clarify diagnosis-pack output, evidence grades, and non-taint wording where the package references diagnosis

## Stage 5: Validators, smoke coverage, and closeout

- [x] Update contract validation to enforce the new skill names, routing, and no-CLI expectation
- [x] Update smoke coverage for the renamed repair path and diagnosis/report contract assumptions
- [x] Run validation and smoke checks
- [x] Fix fallout until the updated contract passes or remaining gaps are explicit
