---
name: scafforge-repair
description: Apply Scafforge's host-side managed repair flow for an existing repository. Use when diagnosis has already identified safe workflow repairs, managed-surface replacement, or contract-refresh work that should be applied with provenance and post-repair verification.
---

# Scafforge Repair

Use this skill to apply safe workflow-contract repairs to an existing repository.

This is the host-side repair surface. It consumes diagnosis outputs, especially Report 4 from `scafforge-audit`, applies deterministic managed-surface repairs, continues into any required project-specific regeneration passes, records provenance, and routes follow-up ticketing when workflow repair reveals additional work or current-machine prerequisites still block trusted verification.
Use [../../references/competence-contract.md](../../references/competence-contract.md) as the bar for whether the repaired workflow is actually competent.
Managed repair is non-destructive: the deterministic refresh engine must back up managed surfaces, record diff summaries, and escalate intent-changing changes instead of silently applying them.

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
python3 skills/scafforge-repair/scripts/run_managed_repair.py <repo-root>
```

Use this as the default repair entrypoint. It runs the deterministic managed-surface refresh, emits the machine-readable repair plan, stale-surface map, and execution record, reruns verification, and fails closed when required follow-on stages still have not been executed.
The canonical execution record lives at `.opencode/meta/repair-execution.json`, and the persistent follow-on tracking ledger lives at `.opencode/meta/repair-follow-on-state.json`.
If the selected diagnosis basis still records `package_work_required_first: true`, repair must stop and send the user back to one fresh post-package revalidation audit instead of mutating the subject repo.
Prefer explicit recorded completion when a downstream follow-on stage actually ran:

```sh
python3 skills/scafforge-repair/scripts/record_repair_stage_completion.py <repo-root> --stage <stage> --completed-by <skill> --summary "<what ran>"
```

Use that command to record real follow-on execution with evidence paths. Recorded execution must include at least one repo-relative evidence path. Recorded execution must include a non-empty `completed_by`, a non-empty summary, and current evidence; zero-evidence or blank-provenance recorded completion is invalid and must be rejected.
Recorded completion also requires repair-package provenance; a missing package commit must surface as `missing_provenance` and be rejected instead of silently degrading to `unknown`.
`record_repair_stage_completion.py` and canonical repair-completion artifacts are the normal public completion path inside the canonical repair follow-on stage catalog. A hidden legacy `--stage-complete` compatibility shim may still exist for older hosts, but it must stay outside the normal documented happy path and still obey the same stage-catalog and current-cycle rules.
The current allowed stage names are:

- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`
- `ticket-pack-builder`
- `handoff-brief`

Reject unknown stage names instead of silently recording arbitrary labels into repair state.
Known stage names are still not enough by themselves. Outside the special closeout case for `handoff-brief`, a stage that is not part of the current repair cycle must be rejected instead of being recorded into the current cycle. In practice that means the stage must also be present in the current repair cycle's `required_stages`.
When a downstream stage emits a canonical repair completion artifact for the current repair cycle, the public repair runner may auto-recognize that stage on the next run instead of requiring a separate recording command. The current bounded auto-recognition path is:

- `project-skill-bootstrap` via `.opencode/state/artifacts/history/repair/project-skill-bootstrap-completion.md`
- `opencode-team-bootstrap` via `.opencode/state/artifacts/history/repair/opencode-team-bootstrap-completion.md`
- `agent-prompt-engineering` via `.opencode/state/artifacts/history/repair/agent-prompt-engineering-completion.md`
- `ticket-pack-builder` via `.opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md`
- `handoff-brief` via `.opencode/state/artifacts/history/repair/handoff-brief-completion.md`

That artifact is only trusted for the current repair cycle when it includes both:

- `- completed_stage: <stage-name>`
- `- cycle_id: <current .opencode/meta/repair-follow-on-state.json cycle_id>`

If a follow-on stage does not yet emit a canonical completion artifact, use `record_repair_stage_completion.py`.
If recorded execution uses the canonical repair completion artifact path for a stage, that artifact must also match the current repair cycle before Scafforge accepts the recorded completion.

**After recording the last required follow-on stage**, the `repair_follow_on` nested object in `workflow-state.json` will still reflect the prior `managed_blocked` state because the recorder only writes the persistent ledger. Run the reconciler to update `workflow-state.json` and regenerate restart surfaces:

```sh
python3 skills/scafforge-repair/scripts/reconcile_repair_follow_on.py <repo-root>
```

The reconciler is the only path that transitions `repair_follow_on.outcome` from `managed_blocked` to `source_follow_up` outside of a full `run_managed_repair.py` cycle. It acts only when every blocking reason is stage-completion-based and all named stages are present in the persistent ledger. If any blocking reason is verification-derived (skipped verification, new critical findings, contract failures), it exits with a non-zero status and explains what must be resolved first. It does not modify `verification_passed`, `current_state_clean`, or `causal_regression_verified` — those fields are audit-derived and are preserved verbatim from the last repair run. When in doubt, use `--dry-run` to preview what would change before writing.
If you need a verification rerun after recording the required follow-on stages, run `run_managed_repair.py` with `--skip-deterministic-refresh` so the current cycle is verified without opening a fresh deterministic refresh cycle.
Do **not** rerun the full public repair runner after successful follow-on completion unless you are intentionally starting a brand-new repair cycle from new diagnosis evidence; a full rerun will regenerate scaffold-managed surfaces again and can recreate placeholder-skill drift.
Do **not** invoke `./scripts/run_agent.sh <repo> --repair` (or any equivalent nested repair wrapper) from inside an already-running repair pass. Once you are inside `scafforge-repair`, call the underlying repair scripts directly (`run_managed_repair.py`, `record_repair_stage_completion.py`, `reconcile_repair_follow_on.py`, and the required follow-on skill scripts) so the provider does not recurse back into the public runner.
If a previously recorded canonical repair completion artifact is later edited so its `completed_stage` or `cycle_id` no longer matches the current repair cycle, Scafforge must invalidate that recorded execution automatically instead of continuing to trust it.
If recorded execution evidence is later deleted, moved, or was never recorded at all, Scafforge must stop trusting that recorded completion automatically instead of silently continuing to reuse stale completion state.
The public runner must also fail explicit repair-contract consistency checks. At minimum, do not allow it to report verification success when restart surfaces still drift, placeholder local skills survive refresh, or it somehow reports zero findings while still not being current-state clean.

### 4. Use the deterministic engine as the internal refresh phase

Deterministic engine command:

```sh
python3 skills/scafforge-repair/scripts/apply_repo_process_repair.py <repo-root>
```

Use this when the repo needs one deliberate workflow-contract refresh rather than piecemeal edits.
This deterministic repair flow regenerates `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical state, then records the verification outcome before publishing the updated restart narrative.
It must also emit a machine-readable stale-surface map using the bounded categories `stable`, `replace`, `regenerate`, and `ticket_follow_up`.
It must replace managed surfaces non-destructively: compute a file-level diff summary first, back up every target surface before replacement, restore from backup on failure, and record the diff summary plus verification results in repair provenance.
Intent-changing drift is out of scope for routine public repair and must route back through kickoff or pivot instead of being reported as a repair-emitted stale-surface category.
Treat this command as the internal refresh engine, not as the whole user-facing repair contract. A repair run is still incomplete if required regeneration, ticket follow-up, or post-repair verification did not happen afterward.
If repair runs after a pivot, preserve the pivot-owned stale-surface and restart-state truth instead of republishing generic ready-state restart surfaces. Managed repair can refresh workflow surfaces, but it must not erase active pivot blockers or pending pivot lineage work from `START-HERE.md`, `.opencode/state/latest-handoff.md`, or `.opencode/state/context-snapshot.md`.
The canonical Scafforge host-side runner executes from the package root. Keep the `skills/scafforge-repair/scripts/...` prefix when copying commands into that context; only shorten the path to `scripts/...` if your shell cwd is the skill directory itself.

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

When the diagnosis includes source-layer `EXEC*` or `REF*` findings, create the recommended remediation tickets through the repo's canonical ticket flow or ticket-pack-builder follow-up mode. Do not fix product code inside `scafforge-repair`; repair owns workflow and ticket-routing surfaces only.

When the diagnosis includes a finish-contract audit finding (missing finish ownership, premature ready-state narrative with unresolved finish bar, or missing Product Finish Contract section in canonical truth), repair may:
- regenerate managed workflow surfaces that encode finish truth (restart narrative, `START-HERE.md`, workflow state)
- create or normalize finish follow-up tickets when audit proved finish-owning work is missing
- update `START-HERE.md` and `context-snapshot.md` so they stop claiming ready-state when the finish contract requires unfinished content work

Repair may not generate art assets, audio content, or creative material. Do not treat an empty asset folder as a repair target when the brief still owns the finish direction decision. Route that through a decision ticket instead of auto-populating content.

Intent-changing repair examples that must be escalated:
- project-scope changes
- runtime or stack changes
- provider/model changes when they reflect a newer human decision for this repo rather than removal of deprecated package-managed defaults
- rewriting curated human decisions

Intent-changing workflow contract changes that must also be escalated instead of auto-applied:
- adding or removing an agent from the team
- changing the bootstrap command contract
- altering the truth hierarchy or canonical ownership between files
- changing the ticket lifecycle stages
- adding or removing workflow tools
- changing agent skill or task allowlists

Escalation mechanism:
- stop the public repair flow without applying the intent-changing change
- write `.opencode/state/repair-escalation.json` describing what repair attempted, why it is intent-changing, the diff summary, and the user decision now required
- surface that escalation in the repair execution record and restart narrative instead of pretending the repo is ready

### 7. Record provenance and process-version state

Every repair pass must leave explicit state.

- update `.opencode/meta/bootstrap-provenance.json`
- update `.opencode/state/workflow-state.json`
- record what changed and why
- include the file-level diff summary, addressed audit codes, verification results, and any remediation ticket ids in repair provenance
- if the process layer materially changed, set `pending_process_verification: true`
- regenerate the derived restart surfaces and record why they were regenerated
- do not let repair alone publish a "ready for continued development" restart narrative before audit verification reruns

### 8. Route backlog follow-up

When repair reveals unfinished or source-layer follow-up work:

- route through `../ticket-pack-builder/SKILL.md`
- use `python3 skills/ticket-pack-builder/scripts/apply_remediation_follow_up.py <repo-root> --diagnosis <diagnosis-dir-or-manifest>` when the diagnosis pack already contains `ticket_recommendations` for source-layer remediation
- create explicit remediation or decision tickets
- use `ticket_create(source_mode=split_scope)` for open-parent decomposition instead of encoding that work as net-new or post-completion remediation
- use `ticket_reconcile` when the existing source/follow-up graph is stale or contradictory to the current evidence
- keep this ticket generation inside the same repair run when the diagnosis already proved it is needed
- keep repo-local review skills advisory only; they are not the canonical ticket owner
- when the follow-up ticket carries `finding_source`, the downstream review artifact must rerun the original failing command or the canonical acceptance command for the repaired surface and record the exact command, raw command output, and explicit PASS/FAIL result before that review counts as trustworthy closure

**Backlog-truth regeneration**: if the audit or diagnosis identified features in the canonical brief that have no corresponding tickets (spec coverage gaps), run `../ticket-pack-builder/SKILL.md` in remediation mode to generate the missing tickets before declaring repair complete. A repair run that leaves spec features without ticket coverage has not fully repaired the backlog. Specifically:
1. Cross-reference the canonical brief's Goals and Required Outputs against the current manifest
2. For any spec feature with no matching ticket, create a ticket with spec-derived acceptance criteria
3. Document the gap and the new ticket(s) in the repair summary
4. Do not mark repair complete until all identified spec-coverage gaps have corresponding tickets

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
- Which follow-on stages were only host-asserted through the legacy compatibility assertion path
- Which follow-on stages were explicitly recorded as completed through `record_repair_stage_completion.py`
- The persistent follow-on state path and recorded stage state for the current repair cycle
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

## Emergency: lifecycle corruption deadlock

If `ticket_claim` or `ticket_reconcile` fails with **"Unsupported ticket status: \<value\>"**, the repo has lifecycle corruption: a lifecycle stage name (e.g. `planning`, `implementation`) was written into a ticket's `status` field instead of a valid coarse status (`todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`).

This creates a circular deadlock: the TypeScript runtime rejects every manifest save, so `ticket_claim` and `ticket_reconcile` both fail, and neither can be used to fix the state through normal tools.

**Escape path:** run the managed repair runner. It applies a lifecycle-corruption preflight before any validation:

```sh
python3 scripts/run_managed_repair.py <repo-root>
```

The repair runner's `_repair_lifecycle_corruption` preflight:
- Coerces any invalid status to `blocked` (when the stage allows it) — the conservative choice that signals operator review
- Falls back to the stage's default valid status only for stages that do not allow `blocked` (e.g. `closeout` → `done`)
- Runs **before** graph-contradiction repair and before any save-path validation, so the runtime deadlock cannot block it

After the repair runner completes, derived surfaces are refreshed and the ticket is in a valid state for normal lifecycle operations.

## References

- `references/process-smells.md` — workflow smells covered by audit
- `references/repair-playbook.md` — repair targets and escalation boundary
- `references/safe-stage-contracts.md` — stage contract definitions
