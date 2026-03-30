---
name: scafforge-repair
description: Apply Scafforge's host-side managed repair flow for an existing repository. Use when diagnosis has already identified safe workflow repairs, managed-surface replacement, or contract-refresh work that should be applied with provenance and post-repair verification.
---

# Scafforge Repair

Use this skill to apply safe workflow-contract repairs to an existing repository.

This is the host-side repair surface. It consumes diagnosis outputs, especially Report 4 from `scafforge-audit`, applies deterministic managed-surface repairs, continues into any required project-specific regeneration passes, records provenance, and routes follow-up ticketing when workflow repair reveals additional work or current-machine prerequisites still block trusted verification.
Use [../../references/competence-contract.md](../../references/competence-contract.md) as the bar for whether the repaired workflow is actually competent.

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
- Inspect `diagnosis/` and `.opencode/meta/bootstrap-provenance.json` to determine whether this is a repeat repair after a prior audit->repair attempt already failed
- Confirm which repairs are safe and which need escalation
- Confirm whether Report 4 depends on Scafforge package changes that have already landed
- Do not run repair from a stale package version against a repo whose diagnosis identified package defects first
- Use the fresh post-package revalidation diagnosis pack as the repair basis when the earlier diagnosis required package work first

Do not improvise intent-changing fixes under the label of repair.
If the required package changes are not available yet, stop and route back to Scafforge package work instead of repairing prematurely.
If the repo already went through audit->repair->resume->failure, explain why the previous cycle failed before starting another repair pass.

### 2. Choose the repair path

Use the narrowest repair that resolves the validated drift.

- Use deterministic managed-surface replacement when the workflow layer is outdated, mixed, or partially scaffold-managed
- Use targeted project-specific regeneration when skills, agents, model-profile surfaces, or prompt hardening drifted
- Route source-layer implementation bugs into ticketing instead of fixing product code here

### 3. Run the public managed-repair runner when needed

Public repair command:

```sh
python3 scripts/run_managed_repair.py <repo-root>
```

Use this as the default repair entrypoint. It runs the deterministic managed-surface refresh, emits the machine-readable repair plan, stale-surface map, and execution record, reruns verification, and fails closed when required follow-on stages still have not been executed.
If the selected diagnosis basis still records `package_work_required_first: true`, repair must stop and send the user back to one fresh post-package revalidation audit instead of mutating the subject repo.
The current `--stage-complete` path is transitional. Treat it as a host assertion recorded in the execution record, not as the final architecture for persistent follow-on stage tracking.
The public runner must also fail explicit repair-contract consistency checks. At minimum, do not allow it to report verification success when restart surfaces still drift, placeholder local skills survive refresh, or it somehow reports zero findings while still not being current-state clean.

### 4. Use the deterministic engine as the internal refresh phase

Deterministic engine command:

```sh
python3 scripts/apply_repo_process_repair.py <repo-root>
```

Use this when the repo needs one deliberate workflow-contract refresh rather than piecemeal edits.
This deterministic repair flow regenerates `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical state, then records the verification outcome before publishing the updated restart narrative.
It must also emit a machine-readable stale-surface map using the bounded categories `stable`, `replace`, `regenerate`, `ticket_follow_up`, and `human_decision`.
Treat this command as the internal refresh engine, not as the whole user-facing repair contract. A repair run is still incomplete if required regeneration, ticket follow-up, or post-repair verification did not happen afterward.

### 5. Continue into required project-specific regeneration

Deterministic replacement is not the whole repair when the audit shows `SKILL001`, `MODEL001`, prompt drift, or agent drift.

After the deterministic refresh:

1. run `../project-skill-bootstrap/SKILL.md` in repair/regeneration mode when scaffold-managed local skills were replaced or any local skill remains generic, missing, or model-profile-drifted
2. run `../opencode-team-bootstrap/SKILL.md` when `.opencode/agents/` or `docs/process/agent-catalog.md` still drift from the current contract
3. run `../agent-prompt-engineering/SKILL.md` whenever regenerated skills or agents changed prompt behavior, model defaults, or delegation rules

Treat the following as one contract family and refresh them together when the audit shows lifecycle confusion or bypass-seeking:
- `.opencode/lib/workflow.ts`
- `.opencode/tools/ticket_update.ts`
- `.opencode/tools/ticket_lookup.ts`
- `.opencode/tools/artifact_write.ts`
- `.opencode/tools/artifact_register.ts`
- `.opencode/tools/smoke_test.ts`
- `.opencode/plugins/stage-gate-enforcer.ts`
- `.opencode/skills/ticket-execution/SKILL.md`
- the team-leader prompt and any related workflow prompts

If the repair basis includes a transcript-backed `smoke_test` override failure, treat that as workflow-surface drift even when the later audit also reports `EXEC*` findings. Refresh the managed `smoke_test` tool so explicit overrides can launch the intended command before reclassifying anything as an environment or ticket failure.
If the repair basis includes transcript-backed smoke-scope drift, refresh the managed `smoke_test` tool and related prompts so ticket acceptance commands are treated as canonical smoke scope before any generic full-suite or heuristic pytest fallback.

Do not stop after tool replacement if the repo would still resume with placeholder local skills, stale model defaults, or older agent prompts.

If the current runtime only executed the deterministic engine, report that explicitly as an incomplete repair pass instead of implying the full repair contract already ran.

### 6. Apply remaining safe follow-up edits

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
- removing deprecated package-managed model defaults such as `MiniMax-M2.5` when the package guidance has already moved to a newer default
- regenerating model-profile, local-skill, and agent-team surfaces after a deterministic refresh replaced their scaffold-managed foundations
- repairing repos where the coordinator authored QA or smoke-test proof outside the owning specialist or tool boundary
- repairing repos where the docs-handoff lane was blocked by a plugin/prompt ownership conflict on optional `handoff` artifacts
- creating remediation tickets for source bugs discovered by audit rules

Intent-changing repair examples that must be escalated:
- project-scope changes
- runtime or stack changes
- provider/model changes when they reflect a newer human decision for this repo rather than removal of deprecated package-managed defaults
- rewriting curated human decisions

### 7. Record provenance and process-version state

Every repair pass must leave explicit state.

- update `.opencode/meta/bootstrap-provenance.json`
- update `.opencode/state/workflow-state.json`
- record what changed and why
- if the process layer materially changed, set `pending_process_verification: true`
- regenerate the derived restart surfaces and record why they were regenerated
- do not let repair alone publish a "ready for continued development" restart narrative before audit verification reruns

### 8. Route backlog follow-up

When repair reveals unfinished or source-layer follow-up work:

- route through `../ticket-pack-builder/SKILL.md`
- create explicit remediation or decision tickets
- use `ticket_create(source_mode=split_scope)` for open-parent decomposition instead of encoding that work as net-new or post-completion remediation
- use `ticket_reconcile` when the existing source/follow-up graph is stale or contradictory to the current evidence
- keep this ticket generation inside the same repair run when the diagnosis already proved it is needed
- keep repo-local review skills advisory only; they are not the canonical ticket owner

### 9. Re-run verification

After repairs, the public repair runner must own the verification pass and its diagnosis pack:

```sh
python3 scripts/run_managed_repair.py <repo-root>
```

`run_managed_repair.py` must automatically carry forward transcript-backed diagnosis evidence and emit the post-repair diagnosis pack itself. Only pass `--supporting-log <path>` manually when repairing from ad hoc transcript evidence that never existed in diagnosis history. Pass `--diagnosis-output-dir <writable-path>` only when the subject repo is outside the current host's writable roots.
When the repair is based on a specific older diagnosis pack rather than the repo's latest diagnosis, pass `--repair-basis-diagnosis <diagnosis-dir-or-manifest>` so verification inherits transcript evidence from the selected basis instead of from unrelated repo history.
Do not schedule another manual audit as the normal next step after repair. The public repair runner owns post-repair verification and emits the `post_repair_verification` diagnosis pack itself.

If the repair changed the managed workflow layer materially, note that verification was re-run and whether ticket re-verification remains pending.
If `BOOT001` or `BOOT002` was part of the repair basis, rerun the subject repo's `environment_bootstrap` flow before the final audit so bootstrap evidence is refreshed against the repaired tool surface.
If repeated bootstrap failures keep reproducing the same incompatible command trace after managed refresh, treat that as non-converged managed repair instead of downgrading it to operator-only rerun guidance.
If verification still reports `ENV*`, `EXEC*`, or `WFLOW008` findings, do not call the repo clean. Report that managed-surface repair completed but host prerequisites, runtime failures, or backlog process verification still remain.
If verification reports only source-layer `EXEC*` work or correctly surfaced backlog reverification state, do not leave `repair_follow_on` as the blocker for ordinary ticket lifecycle execution. Route that follow-up through the active ticket or guarded ticketing instead.
If the repair basis was transcript-backed, do not call the repo clean on current-state evidence alone. The verification result must distinguish current-state cleanliness from causal-regression verification and fail closed when the causal transcript basis was not replayed.
Use explicit `repair_follow_on.outcome` semantics:
- `managed_blocked` only when managed repair follow-on still blocks lifecycle execution
- `source_follow_up` when managed repair converged but source-layer ticket work still remains
- `clean` when managed repair itself no longer blocks ordinary execution

## How this differs from scafforge-audit

- `scafforge-audit` is non-mutating diagnosis and review validation
- `scafforge-repair` performs safe managed workflow repairs and any required same-run regeneration after the diagnosis-to-package-to-subject-repo handoff is complete

Keep the diagnosis decision and the repair action separated.

## After this step

- Continue to `../handoff-brief/SKILL.md` once repair, any required regeneration, ticket follow-up, and verification are complete

## Required outputs

- Validated repair basis
- Prior diagnosis/repair-cycle analysis when this is a repeat repair attempt
- Exact files changed
- Machine-readable stale-surface map
- Safe-versus-escalated repair boundary
- Whether deterministic managed-surface replacement occurred
- Whether project-skill, agent-team, and prompt-hardening follow-up ran
- Which follow-on stages were only host-asserted through the transitional `--stage-complete` path
- Provenance and workflow-state updates applied
- Ticket follow-up created or recommended
- Post-repair verification results

## Rules

- Do not repair without evidence
- Do not silently fold intent-changing decisions into safe repair
- Prefer deterministic managed-surface refresh over mixed old/new workflow layers
- Treat deprecated package-managed defaults as repair drift, not protected intent, unless newer explicit accepted-decision evidence says otherwise
- Do not stop at deterministic managed-surface replacement when the repaired repo still carries placeholder local skills, missing model-profile surfaces, or stale agent prompts
- Preserve durable project facts while replacing managed surfaces
- Leave explicit provenance and verification state after repair
- Do not treat source-layer remediation or correctly surfaced `pending_process_verification` as proof that managed repair itself failed
- If the prior repo history contains coordinator-authored PASS artifacts or bypass transitions, leave `pending_process_verification: true` and require backlog reverification before treating those historical closeouts as trusted
- If the prior repo history shows verification failed and then later recovered with real command evidence, do not treat the recovered run as fabricated PASS proof
- Treat missing host prerequisites and blocked verification commands as first-class post-repair outputs, not as clean verification

## References

- `references/process-smells.md` — workflow smells covered by audit
- `references/repair-playbook.md` — repair targets and escalation boundary
- `references/safe-stage-contracts.md` — stage contract definitions
