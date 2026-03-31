# Scafforge Remediation Gap-Closure Plan

This document is the evidence-backed completion plan for the remaining Scafforge remediation work.

It is a companion to:

- `scafforge-consolidated-remediation-plan.md`
- `scafforge-remediation-progress-review.md`

Those two documents capture target state and branch progress. This document answers a different question:

What still falls short of the remediation aims, what has drifted or become overcomplicated during implementation, and what exact work remains to finish the remediation without leaving stragglers behind.

Use this document as the remaining-work tracker after the committed branch milestones in `scafforge-remediation-progress-review.md`.

## Current Evidence Snapshot

This plan is based on the current workspace state, not only on branch claims.

Observed in this workspace:

- `python3 scripts/validate_scafforge_contract.py` passed
- `python3 scripts/smoke_test_scafforge.py` passed
- `python3 scripts/integration_test_scafforge.py` passed
- `git log --oneline -n 25` shows the committed branch tip is still `9123359`
- `git status --short` shows additional uncommitted work beyond that tip

Current structural measurements:

- `skills/scafforge-audit/scripts/audit_repo_process.py`: 1771 lines
- `scripts/validate_scafforge_contract.py`: 1457 lines
- `scripts/smoke_test_scafforge.py`: 5165 lines
- `scripts/integration_test_scafforge.py`: 340 lines
- `scripts/validate_scafforge_contract.py` currently contains 775 `require_contains(...)` checks
- `scripts/smoke_test_scafforge.py` currently contains 425 explicit `RuntimeError(...)` assertions

Current uncommitted workspace deltas:

- curated fixture corpus under `tests/fixtures/gpttalker/`
- dedicated integration coverage in `scripts/integration_test_scafforge.py`
- archive-plan preservation under `references/archived-diagnosis-plans/`
- bulk deletion of `out/scafforge audit archive/`
- bulk deletion of `scafforgechurnissue/`
- progress-review updates claiming Phase 0, 4, and 7 closure

That means the repo currently has three different truth layers that must not be conflated:

1. the branch tip already pushed to the PR
2. the current local workspace, which is ahead of that tip
3. the plan and progress docs, which are partly stale and partly ahead of the committed branch

## Executive Assessment

The remediation direction is still correct.

The package is materially stronger than `main` in the right areas:

- shared verifier architecture exists
- greenfield proof is stronger
- audit has been meaningfully modularized
- repair follow-on state is much more truthful
- generated next-action routing is materially better
- pivot is a real lifecycle instead of hidden improvisation
- package verification is broader and more execution-backed

But the implementation still falls short of the plan and the original aims in six ways:

1. branch truth, worktree truth, and plan/progress truth are currently out of sync
2. greenfield still lacks the earlier bootstrap-lane proof layer described in the plan
3. audit has been split, but not yet simplified enough to stop future bloat
4. repair is much safer, but it still exposes a transitional assertion input that the plan explicitly called non-final
5. verification has become stronger, but it is still too string-coupled and too concentrated in giant scripts
6. the plan is not complete until one real migrated repo, especially GPTTalker, validates the remediated lifecycle end to end

The largest remaining risk is no longer the original deadlock families alone.

It is that the package can now become hard to evolve because too much of the safety net lives in text-coupled validation and one very large smoke harness instead of smaller structural invariants and reusable execution fixtures.

## Prior Review Findings: Still Relevant vs Closed

`headreviewer.md` is still useful, but it is no longer fully current.

Closed since that review:

- host-sensitive `.venv` / `uv` handling is stronger now, and the current smoke suite passes on this host
- the greenfield verifier is now sequenced before `handoff-brief` in `skills/skill-flow-manifest.json`
- both `merge_start_here()` partial-marker bugs are fixed in repair and restart regeneration
- the stale-surface-map `human_decision` overclaim was removed from the public repair path

Still relevant:

- the package is still leaning too heavily on text-coupled verification
- the validator and smoke harness are still too large and too literal
- the branch still overstates completion in some places because uncommitted work and committed branch state are being described together

The remaining plan should treat that last point as a release-blocking process issue, not just a documentation nit.

## Gap Analysis By Plan Phase

### Phase 0: Contract Freeze And Evidence Cleanup

Status: partially complete on the committed branch, closer to complete in the current workspace

Evidence:

- `.rgignore` already reduced search contamination
- the current workspace now contains curated fixtures and archived-plan preservation
- the current workspace also deletes the bulk archive/churn trees
- `scripts/validate_scafforge_contract.py` now contains `validate_curated_fixtures(...)`, but that change is not yet committed

What still falls short:

- branch truth and workspace truth are not yet unified
- `scafforge-consolidated-remediation-plan.md` still records an older `uv`-missing smoke failure that is no longer current workspace truth
- `scafforge-remediation-progress-review.md` is currently ahead of the committed branch
- the curated fixtures are still evidence notes plus index metadata, not yet executable fixture bundles

Conclusion:

Phase 0 should not be treated as fully closed until the cleanup, fixture preservation, validator updates, and document rebasing are committed and reviewed together.

### Phase 1: Rebuild The Lifecycle Architecture

Status: mostly implemented, but not fully settled

Evidence:

- shared verifier extraction exists under `skills/scafforge-audit/scripts/shared_verifier.py`
- repair consumes that verifier through the shim under `skills/scafforge-repair/scripts/shared_verifier.py`
- pivot exists in `skills/skill-flow-manifest.json`
- the cycle smell is explicitly recorded as `CYCLE001`

What still falls short:

- the core cycle between `project-skill-bootstrap` and `opencode-team-bootstrap` is only documented, not resolved
- repair and verifier sharing still rely on dynamic import shims:
  - `skills/scafforge-repair/scripts/audit_repo_process.py`
  - `skills/scafforge-repair/scripts/shared_verifier.py`
- the package does not yet have the minimal-operable-versus-specialization split the plan identified as the real fix

Conclusion:

Phase 1 is good enough for safe continuation, but not for calling the lifecycle architecture complete.

### Phase 2: Make Greenfield Proof-First

Status: partially implemented

Evidence:

- `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py` exists
- `skills/scaffold-kickoff/SKILL.md` requires a pre-handoff verification gate
- `skills/skill-flow-manifest.json` places `repo-scaffold-factory:verify-generated-scaffold` before `handoff-brief`

What still falls short:

- the plan explicitly called for two verification layers:
  - an early post-`repo-scaffold-factory` managed-surface proof
  - a final pre-handoff proof
- only the later final gate exists as a real packaged surface
- the stronger T0 bootstrap-lane architecture is still not implemented as an earlier enforced scaffold checkpoint

Evidence for the gap:

- `skills/scaffold-kickoff/SKILL.md` drives the verifier only after project skills, team customization, prompt hardening, and ticket bootstrap
- there is no separate early verifier entrypoint wired directly after base scaffold generation

Conclusion:

Phase 2 is not complete. It solved false-ready handoff much better, but it did not yet deliver the earlier bootstrap-lane proof the consolidated plan called for.

### Phase 3: Shrink And Refocus Audit

Status: materially advanced, not complete

Evidence:

- audit rule families have been extracted into:
  - `audit_execution_surfaces.py`
  - `audit_restart_surfaces.py`
  - `audit_ticket_graph.py`
  - `audit_lifecycle_contracts.py`
  - `audit_repair_cycles.py`
  - `audit_contract_surfaces.py`
  - `audit_session_transcripts.py`
- `skills/scafforge-audit/scripts/audit_repo_process.py` is still 1771 lines
- `skills/scafforge-audit/SKILL.md` is still large and reference-heavy

What still falls short:

- report assembly, helper parsing, normalization, and a large amount of invariant logic remain centralized in `audit_repo_process.py`
- the audit surface is more modular, but still not small
- new smell onboarding still depends too much on prose plus validator literal checks instead of data-driven rule registration

Straggler concern:

- the package has reduced audit bloat in code structure without yet reducing the overall cognitive surface enough

Conclusion:

Phase 3 should only be considered complete when:

- `audit_repo_process.py` becomes orchestration plus shared helpers, not another large rule file
- `skills/scafforge-audit/SKILL.md` becomes shorter
- adding a finding code becomes module-plus-fixture work, not prose-plus-snippet maintenance

### Phase 4: Make Repair Convergent And Bounded

Status: substantially implemented, but not yet finished in the stricter sense of the plan

Evidence:

- stale-surface maps exist
- recorded follow-on execution exists
- current-cycle evidence validation exists
- stage catalogs and auto-detection artifacts exist
- `record_repair_stage_completion.py` exists
- the current workspace now adds dedicated repair integration coverage

What still falls short:

- the public repair surface still exposes `--stage-complete`
- both docs and code still label that path transitional:
  - `skills/scafforge-repair/SKILL.md`
  - `skills/scafforge-repair/scripts/run_managed_repair.py`
  - `skills/scafforge-repair/scripts/follow_on_tracking.py`
  - `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- a transitional mechanism cannot be the final architecture

Important distinction:

- the current implementation may be good enough to merge safely
- it is not the same thing as satisfying the plan’s end-state for Phase 4

Conclusion:

Phase 4 should only be treated as truly complete when one of two things is true:

1. `--stage-complete` is removed from the public repair contract, or
2. it is retained only as a narrow compatibility shim outside the normal documented happy path

Until then, Phase 4 is operationally strong but architecturally not final.

### Phase 5: Harden Generated Repo Execution Surfaces

Status: largely complete for the main toolchain, with verification follow-through still open

Evidence:

- generated-tool execution coverage now includes most primary workflow tools
- stage-gate plugin coverage exists
- host-surface classification exists in generated bootstrap and smoke tools
- restart-surface next-action routing is stronger

What still falls short:

- plugin coverage remains lighter than tool coverage
- the generated execution harness still lives mostly inside one giant script:
  - `scripts/smoke_test_scafforge.py` at 5165 lines
- the harness is effective, but it is becoming too costly to maintain and review

Conclusion:

The remaining Phase 5 work is less about new workflow behavior and more about stabilizing the verification architecture around that behavior.

### Phase 6: Add A First-Class Pivot Skill

Status: broadly implemented, but still needs final consolidation and real-world proof

Evidence:

- `plan_pivot.py`, `record_pivot_stage_completion.py`, `publish_pivot_surfaces.py`, and `apply_pivot_lineage.py` now exist
- generated restart publication consumes pivot state
- explicit pivot lineage execution exists

What still falls short:

- unresolved follow-up creation still routes through `ticket-pack-builder` unless the pivot plan is already runtime-ready
- the current pivot lifecycle is well-bounded, but still less battle-tested than repair
- the only meaningful proof left for pivot is real migration use, not more internal ceremony

Conclusion:

Phase 6 is close enough to stop adding architecture and move to validation and simplification.

### Phase 7: Rebuild Verification Around Curated Regression Fixtures

Status: partially complete on branch, closer to complete in current workspace, but not finished in the stronger sense

Evidence:

- current workspace adds:
  - `tests/fixtures/gpttalker/index.json`
  - family README notes
  - `scripts/integration_test_scafforge.py`
  - archived-plan preservation
  - bulk archive deletions

What still falls short:

- the curated fixtures are currently notes and metadata, not executable subject-repo state bundles
- `scripts/integration_test_scafforge.py` imports `smoke_test_scafforge` directly and depends on that monolith as a helper library
- fixture protection is real, but still more synthetic than replayable

Conclusion:

Phase 7 should not stop at deleting archive clutter. It needs reusable fixture builders and smaller shared test helpers so the curated evidence becomes maintainable package protection.

### Phase 8: Rollout And Migration

Status: not started

Evidence:

- no committed GPTTalker migration procedure exists
- no real migrated subject-repo validation record exists
- progress review still marks Phase 8 as not started

Conclusion:

The remediation is not done until GPTTalker or another equivalent subject repo survives the full remediated flow without recreating the historical post-repair deadlock pattern.

## Cross-Cutting Stragglers Outside Any Single Phase

These are the issues most likely to keep causing pain if the repo stops at “phase mostly done”.

### 1. Documentation and truth drift

Evidence:

- `scafforge-consolidated-remediation-plan.md` still includes an older missing-`uv` smoke note
- `scafforge-remediation-progress-review.md` currently mixes committed and uncommitted truth
- the current workspace is ahead of the pushed branch

Required correction:

- establish one branch-truth review pass after each major phase closeout

### 2. Validator brittleness

Evidence:

- 775 `require_contains(...)` checks in `scripts/validate_scafforge_contract.py`

Risk:

- wording changes can fail the contract even when behavior stays correct
- safety logic becomes governance-string maintenance

Required correction:

- replace literal text-lock checks with parsed structural checks wherever possible

### 3. Smoke harness monolith

Evidence:

- `scripts/smoke_test_scafforge.py` is 5165 lines and contains 425 explicit `RuntimeError(...)` assertions
- `scripts/integration_test_scafforge.py` imports it as a library

Risk:

- review fatigue
- brittle helper reuse
- hard-to-localize failures

Required correction:

- split reusable test helpers from scenario definitions

### 4. Transitional repair API still public

Evidence:

- `--stage-complete` remains documented and supported

Risk:

- the package may quietly stop at “better transitional architecture” instead of actually reaching the planned end state

Required correction:

- narrow or retire the transitional path

### 5. Provenance fallback still degrades to `"unknown"`

Evidence:

- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`
- `skills/scafforge-audit/scripts/audit_repo_process.py`

Risk:

- package work can still lose attribution or source certainty in exactly the workflows that most need historical traceability

Required correction:

- move from `"unknown"` fallback toward explicit `missing_provenance` state with caller-visible remediation guidance

### 6. Dynamic import shims and compatibility surfaces

Evidence:

- `skills/scafforge-repair/scripts/audit_repo_process.py`
- `skills/scafforge-repair/scripts/shared_verifier.py`

Risk:

- hidden import fragility
- hard-to-test boundary behavior

Required correction:

- replace shim imports with a small shared package module or a common internal library path once phase churn settles

## Remaining Implementation Program

The remaining work should be done in this order.

### Workstream A: Reconcile Branch Truth Before More Architecture

Objective:

- stop describing the repo as more complete than the committed branch actually is

Tasks:

1. split the current uncommitted Phase 4 and 7 work into reviewable commits
2. update `scafforge-consolidated-remediation-plan.md` to remove stale `uv`-failure language
3. rebaseline `scafforge-remediation-progress-review.md` so it distinguishes:
   - committed branch state
   - current workspace state
   - remaining work
4. make the validator reject future progress-doc claims that outrun committed branch truth where that can be detected cheaply

Acceptance:

- working tree clean
- branch truth and progress review agree
- no stale verification-health claim remains in the plan set

### Workstream B: Finish Phase 2 Properly

Objective:

- implement the earlier scaffold-structure proof layer the plan still calls for

Tasks:

1. add an early verifier mode immediately after `repo-scaffold-factory`
2. make that early mode check only:
   - bootstrap lane existence
   - canonical bootstrap ticket presence
   - managed-surface sanity
   - one legal first move before deeper specialization
3. keep the final existing verifier as the pre-handoff continuation gate
4. update kickoff, manifest, validator, and smoke/integration coverage accordingly

Acceptance:

- greenfield has two distinct proof layers
- a repo cannot continue into later specialization with a broken bootstrap lane
- a repo cannot hand off without final immediate-continuation proof

### Workstream C: Finish Phase 3 Properly

Objective:

- make audit smaller in practice, not only more distributed

Tasks:

1. move remaining rule logic out of `audit_repo_process.py`
2. split shared helpers into a dedicated audit support module
3. split diagnosis-pack/report assembly into a dedicated reporting module
4. shrink `skills/scafforge-audit/SKILL.md` to procedure plus output contract
5. replace prose-heavy smell additions with:
   - rule module
   - fixture or synthetic builder
   - smoke/integration coverage
   - repair/verifier ownership mapping

Acceptance:

- `audit_repo_process.py` becomes orchestration-first
- audit skill docs get shorter
- new finding codes no longer require broad prose growth

### Workstream D: Finish Phase 4 Properly

Objective:

- remove the remaining gap between “bounded repair” and “transitional repair”

Tasks:

1. decide the final fate of `--stage-complete`
2. if compatibility must remain, mark it legacy and remove it from the normal public contract path
3. keep canonical completion artifacts as the primary completion model
4. enforce explicit missing-provenance state instead of `"unknown"` fallback in repair history
5. add one integration scenario where recorded completion is rejected for provenance failure, not only evidence failure

Acceptance:

- the public repair contract no longer depends on a transitional assertion path
- repair provenance never silently degrades to `"unknown"`

### Workstream E: Finish Phase 5 Follow-Through

Objective:

- preserve current execution coverage without keeping all of it in one giant smoke file

Tasks:

1. extract a reusable generated-tool harness module from `scripts/smoke_test_scafforge.py`
2. extract plugin harness helpers separately
3. move scenario seeding helpers into fixture-builder modules
4. cover the remaining plugin and stage-gate behavior through the smaller harness

Acceptance:

- smoke script becomes materially smaller
- integration no longer imports the smoke monolith as its main helper library
- plugin enforcement coverage is closer in depth to tool coverage

### Workstream F: Finish Phase 7 Properly

Objective:

- turn curated evidence into reusable package protection instead of only indexed notes

Tasks:

1. commit the current fixture/index/archive-cleanup workspace changes
2. keep the README notes, but add executable synthetic fixture builders for each GPTTalker family
3. wire those builders into smoke or integration coverage by family slug
4. keep archive-origin references for provenance without restoring raw dumps

Acceptance:

- each GPTTalker family has:
  - an indexed note
  - a synthetic setup path
  - explicit coverage ownership
- archive clutter stays out of the product tree

### Workstream G: Complete Phase 8

Objective:

- prove the remediation on a real migrated repo

Tasks:

1. define a GPTTalker-first migration checklist
2. capture pre-migration baseline:
   - historical deadlock families
   - current process version
   - existing restart-surface contradictions
3. migrate GPTTalker through the remediated lifecycle
4. run:
   - one fresh diagnosis
   - repair if needed
   - pivot if needed
   - restart and continuation validation
5. record the outcome as a repo-local migration validation pack

Acceptance:

- GPTTalker no longer reproduces the historical post-repair deadlock families
- Scafforge can point to one real migrated subject repo as proof, not only synthetic fixtures

## Merge And Review Strategy

Do not attempt to land all remaining work as one branch-ending lump.

Use this review order:

1. truth-reconciliation and uncommitted Phase 4 and 7 landing
2. Phase 2 early proof layer
3. Phase 3 audit simplification
4. Phase 4 transitional repair retirement
5. Phase 5 harness decomposition
6. Phase 7 executable fixture builders
7. Phase 8 GPTTalker migration validation

Each slice should leave behind:

- updated plan/progress truth
- validator coverage where appropriate
- smoke or integration proof
- explicit note about whether it reduced code size, doc size, or verification brittleness

## Final Completion Definition

The remediation should only be considered complete when all of the following are true at once:

- the branch and docs agree on current truth
- greenfield has both the early bootstrap-lane proof and the final continuation proof
- audit is smaller in both code and docs, not just more fragmented
- repair no longer relies on a transitional public assertion path
- package verification relies less on literal text locks and giant monolithic harnesses
- curated GPTTalker evidence is executable as package protection
- GPTTalker validates the remediated lifecycle in real use

Until then, the remediation is substantial and directionally correct, but still incomplete.
