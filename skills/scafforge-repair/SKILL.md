---
name: scafforge-repair
description: Apply Scafforge's host-side managed repair flow for an existing repository. Use when diagnosis has already identified safe workflow repairs, managed-surface replacement, or contract-refresh work that should be applied with provenance and post-repair verification.
---

# Scafforge Repair

Use this skill to apply safe workflow-contract repairs to an existing repository.

This is the host-side repair surface. It consumes diagnosis outputs, especially Report 4 from `scafforge-audit`, applies deterministic managed-surface repairs, records provenance, and routes follow-up ticketing when workflow repair reveals additional work.

## When to use this skill

- `scaffold-kickoff` classifies the repo as managed repair / update
- `scafforge-audit` recommends workflow repair in Report 4
- The user explicitly asks to repair, refresh, or upgrade the managed workflow layer

If the user wants diagnosis only, route to `../scafforge-audit/SKILL.md` instead.

## Inputs

Prefer to enter this skill with:
- audit findings from `scafforge-audit`
- the diagnosis four-report pack when available
- a clear safe-versus-intent-changing boundary
- confirmation that any required Scafforge package changes have already been implemented before this repair run

If those inputs do not exist, run or request an audit first unless the requested repair is trivially local and already evidenced.
If the diagnosis pack lives in a generated repo and package work is required, the user should manually copy that pack into the Scafforge dev repo first, complete the package changes there, then return to the subject repo for repair.

## Procedure

### 1. Confirm the repair basis and package state

Before editing, gather the current repair basis.

- Read the validated audit findings
- Read Report 4 and any machine-readable ticket recommendations
- Confirm which repairs are safe and which need escalation
- Confirm whether Report 4 depends on Scafforge package changes that have already landed
- Do not run repair from a stale package version against a repo whose diagnosis identified package defects first

Do not improvise intent-changing fixes under the label of repair.
If the required package changes are not available yet, stop and route back to Scafforge package work instead of repairing prematurely.

### 2. Choose the repair path

Use the narrowest repair that resolves the validated drift.

- Use deterministic managed-surface replacement when the workflow layer is outdated, mixed, or partially scaffold-managed
- Use targeted follow-up edits when the drift is narrow and project-specific
- Route source-layer implementation bugs into ticketing instead of fixing product code here

### 3. Run deterministic managed-surface repair when needed

Preferred command:

```sh
python3 scripts/apply_repo_process_repair.py <repo-root>
```

Use this when the repo needs one deliberate workflow-contract refresh rather than piecemeal edits.

### 4. Apply remaining safe follow-up edits

For each safe repair:

1. read the finding and target pattern
2. update the managed workflow surface or related docs
3. preserve durable project facts and intentional local customizations
4. leave an obvious repair trail

Safe repair examples:
- regenerating derived workflow docs from canonical state
- aligning queue, workflow-state, and artifact contracts
- removing raw-file stage control where tool-backed state exists
- fixing read-only agents that still mutate state
- syncing execution-enforcement rules into prompts
- creating remediation tickets for source bugs discovered by audit rules

Intent-changing repair examples that must be escalated:
- project-scope changes
- runtime or stack changes
- provider/model changes
- rewriting curated human decisions

### 5. Record provenance and process-version state

Every repair pass must leave explicit state.

- update `.opencode/meta/bootstrap-provenance.json`
- update `.opencode/state/workflow-state.json`
- record what changed and why
- if the process layer materially changed, set `pending_process_verification: true`

### 6. Route backlog follow-up

When repair reveals unfinished or source-layer follow-up work:

- route through `../ticket-pack-builder/SKILL.md`
- create explicit remediation or decision tickets
- keep repo-local review skills advisory only; they are not the canonical ticket owner

### 7. Re-run verification

After repairs, run:

```sh
python3 scripts/audit_repo_process.py <repo-root> --format both --fail-on warning
```

If the repair changed the managed workflow layer materially, note that verification was re-run and whether ticket re-verification remains pending.

## How this differs from scafforge-audit

- `scafforge-audit` is read-only diagnosis and review validation
- `scafforge-repair` performs safe managed workflow repairs after the diagnosis-to-package-to-subject-repo handoff is complete

Keep the diagnosis decision and the repair action separated.

## After this step

- Continue to `../ticket-pack-builder/SKILL.md` when repair generates follow-up work
- Continue to `../handoff-brief/SKILL.md` once repair and verification are complete

## Required outputs

- Validated repair basis
- Exact files changed
- Safe-versus-escalated repair boundary
- Whether deterministic managed-surface replacement occurred
- Provenance and workflow-state updates applied
- Ticket follow-up created or recommended
- Post-repair verification results

## Rules

- Do not repair without evidence
- Do not silently fold intent-changing decisions into safe repair
- Prefer deterministic managed-surface refresh over mixed old/new workflow layers
- Preserve durable project facts while replacing managed surfaces
- Leave explicit provenance and verification state after repair

## References

- `references/process-smells.md` — workflow smells covered by audit
- `references/repair-playbook.md` — repair targets and escalation boundary
- `references/safe-stage-contracts.md` — stage contract definitions
