---
name: scafforge-audit
description: Run Scafforge's host-side diagnosis flow for an existing repository. Use when a repo needs workflow diagnosis, contract verification, professional codebase review, or a four-report diagnosis pack with evidence-backed ticket recommendations and no repair edits.
---

# Scafforge Audit

Use this skill to inspect an existing repository in full diagnostic mode without mutating it.

This is the host-side diagnosis surface. It replaces the old mixed doctor-plus-bridge behavior by keeping diagnosis, review evidence intake, and report generation together in one non-mutating skill.
Every audit run produces the full four-report diagnosis pack.

## When to use this skill

- The user asks for diagnosis, review, audit, or report generation
- `scaffold-kickoff` reaches the final verification pass in a greenfield or retrofit flow
- A managed repo needs a current-state diagnosis before any repair work
- A PR or review thread has findings that need evidence validation and ticket recommendations
- A generated repo needs a diagnosis pack that the user will manually carry into the Scafforge dev repo for package work

If the user explicitly asks to repair or refresh the managed workflow layer, route to `../scafforge-repair/SKILL.md` instead.

## Procedure

### 1. Establish scope and evidence

Read the repo state first.

- Inspect workflow surfaces, docs, ticketing, and managed state
- Inspect `diagnosis/` and `.opencode/meta/bootstrap-provenance.json` to determine whether this is a repeat audit after a prior repair attempt
- If session logs or transcript exports were supplied, inspect them before current-state reconciliation and treat them as first-class temporal evidence
- Reconstruct transcript chronology explicitly when logs are supplied:
  - repeated lifecycle errors
  - workaround or bypass attempts
  - verification failures
  - later executable recovery evidence
  - later PASS claims or artifact publication
  - coordinator-authored specialist artifacts
- If review comments, PR notes, or external findings were provided, treat them as candidate evidence only
- Apply the evidence and non-taint rules from `references/review-contract.md`

Do not convert an unverified claim into a canonical finding.
If this is a repeat audit, explain why the previous audit-to-repair cycle failed before recommending another repair run.

### 2. Run the audit script

Run:

```sh
python3 scripts/audit_repo_process.py <repo-root> --format both --emit-diagnosis-pack
```

The script is at `scripts/audit_repo_process.py` relative to this skill.
Pass `--supporting-log <path>` for each supplied session log or transcript export.
If the audited repo is outside the current host's writable roots, pass `--diagnosis-output-dir <writable-path>` so the diagnosis pack is still emitted in a host-writable location.

It produces:
- a markdown audit report
- a JSON audit report
- the timestamped diagnosis pack in `<repo-root>/diagnosis/<YYYYMMDD-HHMMSS>/` or another writable host-selected output directory

The script diagnoses only. It does not modify files.

### 3. Interpret findings against the repair contract

Read:
- `references/process-smells.md`
- `references/repair-playbook.md`
- `references/safe-stage-contracts.md`

For each finding, identify:
- the concrete problem
- the root cause
- the safer target pattern
- whether the issue is workflow-layer drift, source-layer implementation drift, or review noise
- whether the issue is a host prerequisite blocker such as missing `uv`, `pytest`, `rg`, git identity, or diagnosis-pack output permissions
- when logs were supplied, whether the issue is a historical chronology failure, a current-state repo failure, or both
- whether the repo-local workflow explainer, coordinator prompt, and tool contract agree on the same lifecycle semantics

### 4. Validate review findings when present

If the request includes PR comments, review notes, or claimed bugs:

1. inspect the cited implementation directly
2. compare the claim against the current repo contract and actual code
3. reject unsupported, outdated, or tainted findings
4. keep validated findings with tight file evidence
5. when the input is a session transcript, explain stale early-state evidence separately from later reasoning failures

This skill owns professional review validation and ticket recommendation generation at the host layer. Do not route to a separate PR-bridge skill.

### 5. Generate the four-report diagnosis pack

Produce the report pack described by the diagnosis docs on every run.

Use:
- `references/four-report-templates.md` for report structure
- `references/pr-review-workflow.md` for review-triage procedure
- `references/review-contract.md` for evidence grades, ownership classification, and ticket-proposal rules

Required outputs:
- Report 1: `01-initial-codebase-review.md`
- Report 2: `02-scafforge-process-failures.md`
- Report 3: `03-scafforge-prevention-actions.md`
- Report 4: `04-live-repo-repair-plan.md`

At minimum, the pack must capture:
- validated findings, severity, evidence grade, and file references
- supporting session logs or transcript exports when supplied
- whether a previous diagnosis and repair cycle already failed, and which workflow-layer findings persisted
- whether the transcript shows workflow thrash, bypass-seeking, or evidence-free PASS claims
- whether the transcript shows coordinator-authored specialist artifacts or a recovery run that clears an earlier verification failure
- ownership classification for each issue: package defect, managed-surface drift, repo customization drift, or source bug
- rejected or outdated external claims when review evidence was supplied
- Scafforge prevention actions needed in the package repo
- live-repo repair actions that can happen only after the package changes are available
- a clear split between historical session truth and current repo truth whenever the repo changed after the logged session

Report 4 must:
- distinguish safe repairs from intent-changing repairs
- identify whether `scafforge-repair` should run
- state whether Scafforge package work must happen first
- include ticket recommendations for post-repair or source-layer follow-up
- optionally emit a machine-readable recommended-ticket payload when useful

### 6. Decide the next workspace, then stop

This skill is non-mutating.

- If no repair is needed, record a clean diagnosis result
- If the diagnosis identifies a Scafforge package defect or prevention gap, stop after writing the diagnosis pack
- Tell the user to manually copy the diagnosis pack from the subject repo into the Scafforge dev repo
- Apply Scafforge package changes in the Scafforge dev repo before recommending repair
- Return to the subject repo and route to `../scafforge-repair/SKILL.md` only after the required package changes are available to the repair run
- If safe workflow repair is needed but no package work is required and the current repair surface already matches Report 4, repair may be the next separate step
- If only source-layer follow-up is needed, recommend tickets through `ticket-pack-builder`

Do not modify the repo from this skill.
Do not tell the user to go straight from report generation to repair unless you have first confirmed that the required Scafforge-side changes already exist.

## How this differs from scafforge-repair

- `scafforge-audit` diagnoses, validates evidence, and recommends next actions
- `scafforge-repair` consumes diagnosis outputs and applies safe managed-surface repairs

Keep those responsibilities separate.

## After this step

- Continue to `../handoff-brief/SKILL.md` after a clean audit
- Ask the user to manually move the diagnosis pack into the Scafforge dev repo when Report 4 identifies Scafforge package work
- Continue to `../scafforge-repair/SKILL.md` only after those package changes are implemented and the subject repo is back in scope

## Required outputs

- Full diagnosis scope
- Evidence-backed findings only
- Root cause for each validated finding
- Prior diagnosis/repair-cycle analysis when this is a repeat audit
- Four-report diagnosis pack
- Clear repair recommendation boundary
- Ticket recommendations for post-audit follow-up where needed
- Explicit statement that no repo edits were made

## Rules

- Keep diagnosis non-mutating
- Treat missing host prerequisites as first-class findings instead of silent verification skips
- Do not preserve contradictory workflow semantics because they already exist
- Do not accept review claims without repo evidence
- Do not let PR comments taint canonical state
- Do not answer a supplied causal transcript question with current-state findings alone
- Do not treat repeated lifecycle retries, unsupported-stage probing, or PASS artifacts without executable proof as harmless transcript noise
- Keep workflow-layer findings separate from source-layer implementation findings
- Fold review validation into this skill instead of reviving a separate bridge

## References

- `references/process-smells.md` — workflow smells covered by the audit
- `references/repair-playbook.md` — repair targets and safe-versus-intent boundary
- `references/safe-stage-contracts.md` — stage contract definitions
- `references/review-contract.md` — evidence validation and non-taint rules for review findings
- `references/pr-review-workflow.md` — review-comment intake, validation, and routing workflow
- `references/four-report-templates.md` — required structure for the diagnosis-pack reports
