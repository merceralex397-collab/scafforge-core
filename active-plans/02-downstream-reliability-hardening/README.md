# Downstream Reliability Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Eliminate the current womanvshorse and spinner failure families from both fresh Scafforge-generated repositories and the audit/repair recovery path.

**Architecture:** Treat repeated downstream breakage as package evidence. This plan adds a formal failure taxonomy, stronger greenfield proof gates, richer audit classification, and repair routing that distinguishes package-managed defects from genuine repo-local implementation work. The result must satisfy both user criteria: prevention on fresh scaffolds and truthful recovery through `scafforge-audit` plus `scafforge-repair`.

**Tech Stack / Surfaces:** `skills/scafforge-audit/`, `skills/scafforge-repair/`, `skills/repo-scaffold-factory/`, generated template plugins/docs, package validators, fixture repos under `tests/fixtures/`.
**Depends On:** `01-repo-hygiene-cleanup` for portfolio clarity. Can run in parallel with `11-repository-documentation-sweep`, but should land before autonomy plans.
**Unblocks:** `05-completion-validation-matrix`, `07-autonomous-downstream-orchestration`, `08-meta-improvement-loop`.
**Primary Sources:** `active-plans/_source-material/downstream-failures/womanvshorseissues/README.md`, `active-plans/_source-material/asset-pipeline/assetsplanning/spinner.md`, current audit/repair scripts, package validation commands.

---

## Problem statement

Current evidence shows that downstream agents can claim completion when a generated repo:

- fails to load in Godot
- has broken imports or malformed asset references
- has parse/type/runtime errors
- renders mostly off-screen or with obviously broken layout
- looks bad enough that a human would immediately reject it

That is not a downstream-only problem. It means Scafforge currently lacks truthful generation proof, runtime evidence, visual acceptance criteria, and recovery routing.

## Success standard

This plan is not done until both of these statements are true:

1. A fresh Scafforge-generated repo no longer reproduces the same trap family without being blocked by a truthful gate.
2. Once Scafforge is fixed, `scafforge-audit` plus `scafforge-repair` can identify the package-managed part of the failure and leave only genuine repo-local work for the downstream agent.

## Required deliverables

- a concrete failure taxonomy for womanvshorse/spinner-class defects
- seeded regression fixtures for those defect families
- stronger generation-time proof gates for parse/import/load/layout truth
- audit outputs that classify `package defect`, `repo-local defect`, and `mixed defect`
- repair routing that can regenerate Scafforge-managed surfaces without overclaiming repo health
- updated restart/handoff surfaces that name the next legal move after failure or repair

## Package surfaces likely to change during implementation

- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-audit/references/*.md`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-audit/scripts/run_audit.py`
- `skills/scafforge-audit/scripts/target_completion.py`
- `skills/scafforge-audit/scripts/shared_verifier.py`
- `skills/scafforge-repair/SKILL.md`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/follow_on_tracking.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/workflow.md`
- `skills/handoff-brief/assets/templates/START-HERE.template.md`
- `scripts/smoke_test_scafforge.py`
- `scripts/validate_scafforge_contract.py`
- `tests/fixtures/` with new downstream reliability cases

## Failure families this plan must encode

- script parse/type/configuration failures
- broken engine boot or scene boot
- broken asset import or missing resource linkage
- viewport/layout/screen-fit failures
- false-positive completion claims where evidence is absent or contradictory
- package-versus-repo ownership confusion during audit and repair

## Phase plan

### Phase 1: Convert the current evidence into a real defect model

- [ ] Read the womanvshorse and spinner source notes and translate them into explicit failure families rather than vague “repo broken” wording.
- [ ] For each family, define the observable signal, the likely Scafforge-owned cause, the likely repo-local cause, and the evidence artifact required to prove the difference.
- [ ] Record which failures should block handoff immediately versus which should generate follow-up tickets.
- [ ] Add the resulting taxonomy to this plan folder’s reference notes and mirror the core terms into audit reporting language.

### Phase 2: Seed reproducible regression fixtures

- [ ] Create new fixture directories under `tests/fixtures/` for at least `womanvshorse` and `spinner`, following the existing fixture style used by `gpttalker`.
- [ ] For each fixture, write a short `README.md` that states the defect family, expected audit classification, expected repair behavior, and final expected next move.
- [ ] Add index metadata if needed so the package tests can discover the new fixtures consistently.
- [ ] Make sure the fixtures represent package evidence, not only one-off downstream accidents.

### Phase 3: Strengthen greenfield proof before handoff

- [ ] Extend generation-time verification so a repo cannot be handed off on file presence alone.
- [ ] Add explicit gate expectations for parse success, import success, load success, and first-screen truth where the stack supports them.
- [ ] Update the generated stage-gate and restart surfaces so a repo that fails these checks cannot present itself as “ready to continue.”
- [ ] Ensure the proof ladder is cheap-first but truthful: static checks before runtime, runtime before visual approval, visual approval before completion claims.

### Phase 4: Upgrade audit classification

- [ ] Update audit evidence collection so failure families appear as first-class findings rather than generic drift.
- [ ] Teach the audit output to label whether the root cause is primarily package-owned, repo-local, or mixed.
- [ ] Ensure the audit report points to the exact Scafforge surface that likely allowed the failure through: template, validator, generated guidance, or repair logic.
- [ ] Add explicit restart-language guidance so the failure report still leaves one legal next move.

### Phase 5: Upgrade repair routing

- [ ] Update repair logic so Scafforge-managed defects trigger regeneration or package follow-up instead of pretending the repo is clean.
- [ ] Separate “repair managed surfaces now” from “create repo-local remediation ticket” so downstream agents know what remains.
- [ ] Ensure restart regeneration reflects the post-repair truth and does not publish stale success claims.
- [ ] Preserve evidence bundles so the same failure family can later feed the meta-improvement loop.

### Phase 6: Lock the regression story

- [ ] Add package validation coverage for the new fixture families.
- [ ] Run `npm run validate:contract`, `npm run validate:smoke`, and `python3 scripts/integration_test_scafforge.py` with the new fixtures in scope.
- [ ] Confirm that a seeded bad fixture produces the right audit finding and the right repair posture.
- [ ] Confirm that a healthy fixture does not get downgraded by the stronger gates.

## Validation and proof requirements

- at least one womanvshorse-style fixture and one spinner-style fixture exist
- a generated repo cannot clear handoff if it fails parse/import/load/layout truth
- audit output distinguishes package-managed and repo-local responsibility
- repair output leaves a truthful next step and does not silently mark the repo complete
- package validation commands cover the new failure families

## Risks and guardrails

- Do not let “visual problems” collapse back into “polish.” Spinner proves they can be functional blockers.
- Do not treat Godot-only rules as universal. Generalize the failure family, then specialize by stack.
- Do not make repair destructive; preserve evidence and causality.
- Do not allow stronger gates to become vague human taste checks. Each blocked state needs named evidence.

## Documentation updates required when this plan is implemented

- audit and repair skill docs
- generated process docs under the project template
- handoff/restart templates
- package validation references
- `active-plans/FULL-REPORT.md` and `11-repository-documentation-sweep` outputs where sequencing or contracts change

## Completion criteria

- the womanvshorse/spinner trap family is encoded in fixtures, validators, and audit reporting
- fresh scaffolds cannot silently reproduce the same defect family
- audit and repair route the failures truthfully
- downstream agents receive enough structured evidence to fix repo-local issues without guesswork
