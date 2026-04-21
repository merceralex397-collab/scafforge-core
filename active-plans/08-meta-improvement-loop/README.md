# Meta Improvement Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Create the Scafforge self-improvement loop that converts repeated downstream failures into package fixes through a controlled chain: audit -> investigate -> package fix -> review -> revalidate -> downstream repair/resume.

**Architecture:** Package mutation must remain high-trust and evidence-backed. The loop starts with audit evidence, produces a structured investigator report, opens a package change path with normal review, and only then revalidates both Scafforge and the affected downstream repo. Archive mining can feed this loop, but never bypass it.

**Tech Stack / Surfaces:** `skills/scafforge-audit/`, `skills/scafforge-repair/`, new package-side investigation/fix roles, GitHub issues/PRs, package validation commands, `active-audits/`, orchestration resume hooks.
**Depends On:** `02-downstream-reliability-hardening`, `05-completion-validation-matrix`, and `07-autonomous-downstream-orchestration`.
**Unblocks:** the credible self-improving factory story and long-running archive intelligence work.
**Primary Sources:** `_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`, `_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`, current audit/repair implementation, `AGENTS.md` sections on `active-audits/` and package authority.

---

## Problem statement

Right now, repeated downstream failures can be observed, but there is no disciplined path that says:

- when a failure graduates from repo-local bug to package evidence
- what evidence must exist before the package may change
- how a package fix is reviewed and validated
- when the affected downstream repo may resume

Without that, “self-improving” is just a slogan.

## Required deliverables

- a package-level escalation trigger matrix
- a structured evidence bundle emitted from audit
- an investigator contract with a root-cause report format
- a package-fix PR contract and review policy
- a revalidation protocol for both package and downstream repo
- a safe rule for how background archive mining feeds the same loop

## Package and adjacent surfaces likely to change during implementation

- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-audit/references/four-report-templates.md`
- `skills/scafforge-audit/scripts/disposition_bundle.py`
- `skills/scafforge-audit/scripts/run_audit.py`
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-repair/SKILL.md`
- `skills/scafforge-repair/scripts/follow_on_tracking.py`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- restore or create package-side `active-audits/` handling described by `AGENTS.md`
- new package-side roles or skills such as `skills/scafforge-investigator/` and `skills/scafforge-package-fixer/`
- GitHub automation or integration docs for issues and PR linking

## Core design rule

Package repair must not be confused with repo repair.

- `scafforge-repair` remains the generated-repo repair mechanism.
- The meta loop adds package-level investigation and package-level fix review on top of that.
- The downstream repo only resumes after package revalidation and targeted downstream revalidation have both passed.

## Phase plan

### Phase 1: Define the escalation trigger matrix

- [ ] Decide which audit findings are repo-local only, which are candidate package evidence, and which automatically require package investigation.
- [ ] Define repetition thresholds, severity thresholds, and contradiction thresholds that trigger escalation.
- [ ] Ensure the trigger matrix references concrete failure families and proof artifacts rather than vague intuition.
- [ ] Record how the orchestration layer and human operators see that escalation decision.

### Phase 2: Define the evidence bundle contract

- [ ] Specify the audit outputs that must be bundled for package investigation: findings, logs, diffs, restart state, validation artifacts, and source repo metadata.
- [ ] Formalize how those bundles are stored in `active-audits/` or a successor surface without editing the raw evidence.
- [ ] Add enough provenance to map one downstream failure back to one package defect hypothesis.
- [ ] Ensure the evidence bundle is concise enough to review but complete enough to support package fixes.

### Phase 3: Define the investigator role

- [ ] Introduce a package-side investigator role that consumes evidence bundles and writes a root-cause report.
- [ ] Standardize the report into sections: downstream symptom, package-owned cause, prevented-by analysis, required package changes, and revalidation plan.
- [ ] Require the investigator to identify the exact Scafforge surface that needs change: skill instructions, template asset, validation logic, or documentation.
- [ ] Ensure the investigator can also conclude “no package change required” when evidence does not support escalation.

### Phase 4: Define the package-fix path

- [ ] Introduce a package-side fixer role or workflow that turns the investigator report into a reviewable PR.
- [ ] Require normal package review, validation, and documentation updates for that PR.
- [ ] Link the PR back to the evidence bundle and any GitHub issue so the causality chain remains visible.
- [ ] Prevent archive-mining outputs or investigator reports from mutating package code directly without that PR path.

### Phase 5: Define revalidation and downstream resume

- [ ] Require package validation after the fix using the canonical package commands and any new regression fixtures tied to the defect family.
- [ ] Require a fresh downstream audit or targeted revalidation against the updated package before the repo resumes.
- [ ] Define exactly when orchestration may mark the downstream repo `resume-ready`.
- [ ] Ensure restart surfaces in both repos reflect the updated truth and do not overclaim success.

### Phase 6: Integrate background archive intelligence safely

- [ ] Define how archive-mining or historical analysis produces suggestions, not direct package mutations.
- [ ] Route archive-derived improvement candidates into the same trigger/investigation/fix pipeline.
- [ ] Decide when archive findings become tickets versus immediate investigation requests.
- [ ] Ensure the background loop can be paused or reviewed by a human without losing the evidence chain.

## Validation and proof requirements

- repeated downstream failures can trigger a structured package-level investigation
- investigator outputs identify concrete package surfaces and required revalidation
- package fixes land through reviewable PRs, not silent automation
- the downstream repo only resumes after package and downstream revalidation both pass

## Risks and guardrails

- Do not blur `scafforge-repair` and package-side fixing into one tool.
- Do not let archive mining write code or file changes directly.
- Do not escalate every downstream bug into package work; evidence quality matters.
- Do not resume downstream work on “package fix merged” alone; revalidation is mandatory.

## Documentation updates required when this plan is implemented

- audit and repair docs
- package workflow docs covering investigation/fix roles
- `AGENTS.md` for `active-audits/` and package-improvement loop behavior
- GitHub issue/PR workflow notes where the package loop depends on them

## Completion criteria

- repeated downstream failures can become package work through a disciplined evidence-backed loop
- package fixes are reviewable, attributable, and revalidated
- downstream repos resume only after trustworthy revalidation
- the “self-improving” claim becomes a real process instead of an aspiration
