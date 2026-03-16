---
name: repo-process-doctor
description: Audit existing repositories for agent-workflow drift and repair opportunities. Use when a repo has custom OpenCode agents, commands, process docs, or ticket systems and you need to diagnose contradictory status semantics, raw-file stage control, missing workflow-state tools, unsafe read-only delegation, or other workflow smells.
---

# Repo Process Doctor

Use this skill to inspect and repair agent-workflow issues in an existing repository.

## Procedure

### 1. Run the audit script

The audit script runs 21 automated checks for workflow smells. Run it:

```
python scripts/audit_repo_process.py <repo-root> --format both
```

The script is at `scripts/audit_repo_process.py` relative to this skill's directory.

The script produces:
- A markdown report with findings (problem, root cause, affected files, safer pattern)
- A JSON report with structured findings (code, severity, problem, files, evidence)

The script ONLY diagnoses — it does not modify any files.

### 2. Interpret findings

Map each finding to `references/process-smells.md` to understand:
- What the smell is
- Why it fails (especially with weaker models)
- What the safer pattern looks like

### 3. Choose a mode

**audit** — Report findings only. Use for initial inspection or post-scaffold verification.

**propose-repair** — Write a repair plan listing exact files to change and what to change. Present to the user for approval before making changes. Use when you're unsure whether repairs would change project intent.

**apply-repair** — Apply repairs directly. Use when findings are clearly safe to fix. You (the agent) make the changes, not the script.

### Safe vs intent-changing repairs

Read `references/repair-playbook.md` for the boundary.

**Safe repairs (apply directly):**
- Regenerating derived docs from canonical state
- Aligning queue/workflow-state/artifact contracts to scaffold model
- Removing raw-file stage control where tool-backed alternatives exist
- Normalizing contradictory status semantics into the coarse queue contract
- Fixing read-only agents that have mutating shell commands

**Intent-changing repairs (escalate to user):**
- Changes that affect project scope or product intent
- Choosing between unresolved stack/runtime options
- Changing provider or model choices
- Deleting or rewriting curated human decisions
- Collapsing repo-specific patterns that aren't clearly broken

### 4. Apply repairs (if in apply-repair mode)

For each safe repair:
1. Read the finding
2. Read the safer pattern from `references/repair-playbook.md`
3. Read `references/safe-stage-contracts.md` for the target contract
4. Make the change
5. Verify the change resolves the finding
6. Leave an obvious repair trail (document what was changed and why)

For each intent-changing repair:
1. Present the finding and proposed repair to the user
2. Explain why this might change project intent
3. Wait for user decision before proceeding

### 5. Post-repair verification

Re-run the audit script to confirm findings are resolved:
```
python scripts/audit_repo_process.py <repo-root> --format both --fail-on warning
```

## How this differs from scaffold-kickoff

- `scaffold-kickoff` generates a fresh repo from templates
- `repo-process-doctor` diagnoses and fixes DRIFT in existing repos
- They are complementary: kickoff creates, doctor maintains

## After this step

Continue to `../handoff-brief/SKILL.md` as directed by `../scaffold-kickoff/SKILL.md`.

## Required outputs

- Concise diagnosis of each finding
- Root cause for each finding
- Chosen mode (audit / propose-repair / apply-repair)
- Exact files patched (if apply-repair)
- Target safer pattern for each repair
- Post-repair verification results

## Rules

- Do not preserve contradictory status semantics just because they already exist
- Do not keep multi-surface workflow state if one surface can become derived
- Prefer deterministic migration to the current scaffold contract
- Treat read-only mutation paths as blockers
- Default to apply-repair for safe repairs, escalate intent-changing repairs
- Always leave an obvious repair trail — never silently fix without evidence

## References

- `references/process-smells.md` — the 21 workflow smells
- `references/repair-playbook.md` — repair targets and safe/intent-changing boundary
- `references/safe-stage-contracts.md` — stage contract definitions
