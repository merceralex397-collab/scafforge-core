---
name: scafforge-audit
description: Run Scafforge's host-side diagnosis flow for an existing repository. Use when a repo needs workflow diagnosis, contract verification, professional codebase review, or a four-report diagnosis pack with evidence-backed ticket recommendations and no repair edits.
---

# Scafforge Audit

Use this skill to inspect an existing repository without mutating it.

This is the host-side diagnosis surface. It replaces the old mixed doctor-plus-bridge behavior by keeping diagnosis, review evidence intake, and report generation together in one read-only skill.

## When to use this skill

- The user asks for diagnosis, review, audit, or report generation
- `scaffold-kickoff` reaches the final verification pass in a greenfield or retrofit flow
- A managed repo needs a current-state diagnosis before any repair work
- A PR or review thread has findings that need evidence validation and ticket recommendations
- A generated repo needs a diagnosis pack that the user will manually carry into the Scafforge dev repo for package work

If the user explicitly asks to repair or refresh the managed workflow layer, route to `../scafforge-repair/SKILL.md` instead.

## Operating modes

Choose the narrowest mode that matches the request.

- `audit` — run the workflow/process audit and summarize findings
- `review` — validate implementation or review findings against the actual repo state
- `diagnosis-pack` — produce the four-report diagnosis pack in full

You can combine these when needed. The common full path is `audit` + `review` + `diagnosis-pack`.

## Procedure

### 1. Establish scope and evidence

Read the repo state first.

- Inspect workflow surfaces, docs, ticketing, and managed state
- If review comments, PR notes, or external findings were provided, treat them as candidate evidence only
- Apply the evidence and non-taint rules from `references/review-contract.md`

Do not convert an unverified claim into a canonical finding.

### 2. Run the audit script

Run:

```sh
python3 scripts/audit_repo_process.py <repo-root> --format both
```

The script is at `scripts/audit_repo_process.py` relative to this skill.

When the mode includes `diagnosis-pack`, add `--emit-diagnosis-pack` so the script writes the four-report pack into `<repo-root>/diagnosis/<YYYYMMDD-HHMMSS>/`.

It produces:
- a markdown audit report
- a JSON audit report
- the timestamped diagnosis pack when requested

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

### 4. Validate review findings when present

If the request includes PR comments, review notes, or claimed bugs:

1. inspect the cited implementation directly
2. compare the claim against the current repo contract and actual code
3. reject unsupported, outdated, or tainted findings
4. keep validated findings with tight file evidence

This skill owns professional review validation and ticket recommendation generation at the host layer. Do not route to a separate PR-bridge skill.

### 5. Generate the four-report diagnosis pack

When the user asks for the diagnosis plan flow, produce the report pack described by the diagnosis docs.

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
- ownership classification for each issue: package defect, managed-surface drift, repo customization drift, or source bug
- rejected or outdated external claims when review evidence was supplied
- Scafforge prevention actions needed in the package repo
- live-repo repair actions that can happen only after the package changes are available

Report 4 must:
- distinguish safe repairs from intent-changing repairs
- identify whether `scafforge-repair` should run
- state whether Scafforge package work must happen first
- include ticket recommendations for post-repair or source-layer follow-up
- optionally emit a machine-readable recommended-ticket payload when useful

### 6. Decide the next workspace, then stop

This skill is read-only.

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

- Chosen audit scope and mode
- Evidence-backed findings only
- Root cause for each validated finding
- Four-report diagnosis pack when requested
- Clear repair recommendation boundary
- Ticket recommendations for post-audit follow-up where needed
- Explicit statement that no repo edits were made

## Rules

- Keep diagnosis read-only
- Do not preserve contradictory workflow semantics because they already exist
- Do not accept review claims without repo evidence
- Do not let PR comments taint canonical state
- Keep workflow-layer findings separate from source-layer implementation findings
- Fold review validation into this skill instead of reviving a separate bridge

## References

- `references/process-smells.md` — workflow smells covered by the audit
- `references/repair-playbook.md` — repair targets and safe-versus-intent boundary
- `references/safe-stage-contracts.md` — stage contract definitions
- `references/review-contract.md` — evidence validation and non-taint rules for review findings
- `references/pr-review-workflow.md` — review-comment intake, validation, and routing workflow
- `references/four-report-templates.md` — required structure for the diagnosis-pack reports
