# Scafforge Consolidated Remediation Plan

## Scope

This document replaces the split remediation planning in:

- `scafforge-blind-verification-pass.md`
- `scafforge-full-remediation-pass-v2.md`

It also incorporates verified live-repo evidence from the current Scafforge package and from GPTTalker, where the recurring deadlocks have been reproduced in practice.

For current branch implementation status, review triage, and closure verification against this plan, see:

- `scafforge-remediation-progress-review.md`
- `scafforge-remediation-gap-closure-plan.md`
- `pr8-head-review-resolution.md`

The goal is not to add more governance prose. The goal is to make generated repos continue cleanly after bugs, audits, repairs, and midstream design changes.

## Executive Verdict

The two prior plans are directionally correct on the main defect:

- Scafforge still measures surface agreement earlier than executable continuation.
- Audit and repair still carry too much lifecycle responsibility.
- Generated repos can still reach a state where the canonical next move exists in theory but is not obvious or legally runnable in practice.

They are incomplete in three important ways:

1. They lean too heavily toward routing more work through `scafforge-audit`, even though the audit surface is already too large and too overloaded.
2. They do not fully address the cyclic dependency between generation stages.
3. They do not turn pivoting into one clear operator-facing lifecycle path.

This remediation plan keeps the valid recommendations, rejects the parts that would further bloat audit, and adds a shared verifier architecture plus a thin pivot orchestrator.

## Verified Findings

### Confirmed from the live Scafforge repo

- Greenfield still ends at `handoff-brief` and explicitly forbids initial routing into audit or repair.
- The package still treats same-session contract conformance as the final greenfield gate.
- `project-skill-bootstrap` and `opencode-team-bootstrap` still form a conceptual cycle.
- `scafforge-repair` is intentionally multi-stage and can require regeneration after deterministic refresh.
- Provenance can still fall back to `"unknown"`.
- The repo still contains large archive and churn surfaces that contaminate retrieval.

### Confirmed from GPTTalker

- Bootstrap/tooling defects can leave agents with no legal recovery path even after audit and repair.
- Tool and permission mismatch can be misread as repo failure instead of host/tool-surface failure.
- Repeated lifecycle contradictions still push agents toward bypass behavior.
- Restart surfaces can still contradict canonical state after repair and present a false or confusing next move.
- Repair can still reintroduce stale generated assets such as placeholder skills.
- Historical ticket trust, split-scope follow-up, and reconciliation remain hard to reason about after process changes.

### Confirmed by direct package verification

- `python3 scripts/validate_scafforge_contract.py` passes.
- `python3 scripts/smoke_test_scafforge.py` passes on the current host.
- `python3 scripts/integration_test_scafforge.py` passes on the current host.

Those results are current-host proof, not yet universal cross-host proof. The package is still not fully hermetic, and host/path/runtime assumptions must still be treated as live verification risk until broader migration validation is complete.

## Evidence Basis

This plan is grounded in these live surfaces rather than only the prior planning documents:

- Greenfield lifecycle contract:
  - `skills/scaffold-kickoff/SKILL.md`
  - `skills/skill-flow-manifest.json`
  - `references/one-shot-generation-contract.md`
- Audit and repair behavior:
  - `skills/scafforge-audit/SKILL.md`
  - `skills/scafforge-audit/scripts/audit_repo_process.py`
  - `skills/scafforge-repair/SKILL.md`
  - `skills/scafforge-repair/scripts/run_managed_repair.py`
  - `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- Package validation expectations:
  - `scripts/validate_scafforge_contract.py`
  - `scripts/smoke_test_scafforge.py`
- Greenfield dependency surfaces:
  - `skills/project-skill-bootstrap/SKILL.md`
  - `skills/opencode-team-bootstrap/SKILL.md`
  - `skills/ticket-pack-builder/SKILL.md`
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/ticket-execution/SKILL.md`
- GPTTalker failure evidence:
  - `START-HERE.md`
  - `.opencode/state/context-snapshot.md`
  - diagnosis packs showing bootstrap deadlock, lifecycle workaround, restart drift, and repair follow-on behavior

## Corrections After Deep Verification

The first version of this plan needed correction in four places after deeper validation against the live package:

- Do not simply swap `project-skill-bootstrap` and `opencode-team-bootstrap`.
  The safer near-term move is to keep the current order and add a verification gate before handoff. A true simplification of “prove motion before orchestration” requires a later split between minimal-operable scaffold surfaces and project-specific specialization surfaces.

- Do not introduce a new public `scafforge-verify` lifecycle skill in phase 1.
  The verifier logic already lives inside the audit engine and is already imported by repair. The evidence supports extracting a shared internal verifier module, not adding a third public diagnosis/repair-adjacent skill immediately.

- Do not promise fully atomic repair in one command while project-specific regeneration is still non-deterministic.
  The deterministic refresh can be atomic and fail-closed now. The broader repair lifecycle still needs orchestrated follow-on for repo-local skills, agents, and prompts until those stages become deterministic.

- Archive cleanup is still correct, but it needs a small documentation migration.
  Current scripts and tests do not depend on `out/scafforge audit archive/` or `scafforgechurnissue/`, but a few planning/debugging docs do.

## Assessment Of The Two Prior Plans

### Keep

- Add a proof-first greenfield verification gate before handoff.
- Add a first explicit bootstrap lane / first legal move invariant.
- Simplify repair and make its outcomes fail-closed.
- Treat placeholder local skills as generation failure, not later warning.
- Remove archive and churn exhaust from the main product tree.
- Add a first-class pivot lifecycle path.
- Add direct tests for one legal next move and restart-surface truthfulness.

### Keep, but change the implementation

- Post-generation verification is required, but it should not be implemented by making `scafforge-audit` the normal greenfield gate.
  Use a shared internal verifier engine for greenfield, post-repair, and post-pivot checks, and keep public audit focused on diagnosis.

- Wider-reaching repair is required, but not by endlessly expanding prose references.
  Use a stale-surface map, machine-readable repair plan, and deterministic regeneration groups.

- Repair should become externally atomic only for deterministic managed-surface refresh plus fail-closed verification state.
  Do not claim one-command full repair convergence until project-specific regeneration is either deterministic or explicitly orchestrated by the public repair contract.

### Drop or downgrade

- Do not keep adding issue-specific prose into audit references as the main response to every new failure.
- Do not make greenfield completion depend on a full diagnosis pack.
- Do not preserve the current cyclic stage semantics just because the happy-path sequence looks linear.

## Target State

Scafforge is remediated when all of the following are true:

- A fresh generated repo exposes one foreground legal next move, one owner, one proof path, and one blocker path.
- Greenfield completion requires executable continuation proof, not only surface alignment.
- Audit is diagnosis-only again.
- Repair is a bounded lifecycle with explicit stale-surface classification and explicit convergence outcomes.
- Deterministic verification is shared across kickoff, audit, repair, and pivot without becoming a third sprawling public lifecycle surface.
- Restart surfaces are regenerated atomically from canonical state and cannot overclaim readiness.
- Pivoting is a first-class lifecycle path with its own contract.
- Archive evidence is preserved as curated fixtures, not as retrieval clutter in the product tree.

## Remediation Principles

1. Prefer smaller lifecycle surfaces with exact scope.
2. Separate generation verification from diagnosis.
3. Separate diagnosis from repair.
4. Make stale-surface classification machine-readable.
5. Make restart surfaces derived and recomputed, never hand-curated.
6. Add new rules as tested invariants and fixtures before adding them as more prose.
7. Treat operator confusion as package failure evidence.

## High-Risk Caveats

These are the plan decisions most likely to go wrong if implemented casually.

### Do not solve the skill/team cycle with a simple reorder

The live package still expects `project-skill-bootstrap` to create finalized local skills before `opencode-team-bootstrap` finalizes project-specific agents, commands, and allowlists. Reordering those two steps without a deeper contract split would move drift, not remove it.

### Do not let verifier extraction create duplicated logic

Repair already imports audit-side verification logic. Any verifier split that produces parallel codepaths for finding extraction will create code drift, finding drift, and contract drift.

### Do not overpromise repair convergence

The current public repair runner can fail closed and expose required follow-on stages, but it does not execute project-specific regeneration itself. The plan must preserve that truth until the package actually changes the underlying implementation model.

### Do not let pivot become a second repair engine

`scafforge-pivot` is justified only as a thin lifecycle orchestrator. It should classify the change, update canonical truth, choose affected surfaces, and reuse repair/ticket machinery where needed.

## Phase 0: Contract Freeze And Evidence Cleanup

### Objective

Stop further semantic drift while remediation is underway.

### Changes

- Declare one canonical contract set:
  - `README.md`
  - `references/competence-contract.md`
  - `references/one-shot-generation-contract.md`
  - `skills/skill-flow-manifest.json`
- Move `out/scafforge audit archive/` and `scafforgechurnissue/` out of the main product tree.
- Preserve only minimal regression fixtures under a new curated path such as `tests/fixtures/`.
- Add a validator rule that checks contract consistency across manifest, kickoff, audit, repair, and handoff language.
- Update or archive the small set of prose/debugging docs that currently reference those archive paths directly.

### Primary files

- `README.md`
- `references/competence-contract.md`
- `references/one-shot-generation-contract.md`
- `scripts/validate_scafforge_contract.py`
- repo structure and fixture locations

### Done when

- The main repo is product code plus curated fixtures only.
- No live skill contradicts the published lifecycle contract.

## Phase 1: Rebuild The Lifecycle Architecture

### Objective

Remove lifecycle ambiguity and stop overloading audit without adding unnecessary public lifecycle surfaces.

### Changes

- Extract the deterministic candidate-finding logic out of `audit_repo_process.py` into a shared internal verifier module with one stable `Finding` schema.
- Keep the public lifecycle surfaces to:
  - `scaffold-kickoff`
  - `scafforge-audit`
  - `scafforge-repair`
  - `scafforge-pivot`
- Add a kickoff-owned post-generation verification gate that uses the shared verifier engine.
- Keep `scafforge-audit` for diagnosis, transcript analysis, evidence validation, package-work gating, and four-report output only.
- Keep `scafforge-repair` as the public owner of repair orchestration and post-repair verification, but make it consume the shared verifier engine.
- Add a new first-class run type in `skills/skill-flow-manifest.json` for pivoting.
- Add flow-graph sanity checks and explicitly record the current skill/team dependency cycle as a contract smell.
- Keep the current greenfield order for `project-skill-bootstrap` and `opencode-team-bootstrap` in the near term; do not replace the cycle with a simple reorder.

### New lifecycle model

Greenfield:

```text
scaffold-kickoff
  -> spec-pack-normalizer
  -> repo-scaffold-factory
  -> project-skill-bootstrap
  -> opencode-team-bootstrap
  -> agent-prompt-engineering
  -> ticket-pack-builder:bootstrap
  -> kickoff-owned post-generation verification gate
  -> handoff-brief
```

Managed repair:

```text
scaffold-kickoff
  -> scafforge-repair
      -> deterministic refresh
      -> required follow-on stage declaration
      -> shared-verifier post-repair verification
  -> handoff-brief
```

Pivot update:

```text
scaffold-kickoff
  -> scafforge-pivot
      -> shared-verifier post-pivot verification gate
  -> handoff-brief
```

Diagnosis / review:

```text
scaffold-kickoff
  -> scafforge-audit
  -> handoff-brief
```

### Primary files

- `skills/skill-flow-manifest.json`
- `skills/scaffold-kickoff/SKILL.md`
- new shared verifier module and stable finding schema
- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-repair/SKILL.md`
- `scripts/validate_scafforge_contract.py`

### Done when

- Greenfield no longer relies on a full audit pass for completion.
- Audit no longer acts as the catch-all lifecycle answer.
- Verifier logic is shared instead of duplicated.
- The flow graph either becomes acyclic or records the remaining cycle as an explicit temporary design debt with a removal plan.

## Phase 2: Make Greenfield Proof-First

### Objective

A generated repo must prove it can move before it is handed off.

### Changes

- Add a T0 bootstrap lane invariant to the scaffold.
- Require one bounded first active ticket whose purpose is environment/bootstrap proof and first deterministic smoke readiness.
- Add two verification layers:
  - an early scaffold-structure proof after `repo-scaffold-factory`, limited to T0 bootstrap lane and managed-surface sanity
  - a final post-generation verification gate before handoff
- Keep `project-skill-bootstrap -> opencode-team-bootstrap` ordering unless and until the package introduces a real minimal-operable-versus-specialization split.
- Make the final post-generation verification gate check:
  - one legal first move
  - bootstrap route correctness
  - placeholder-free local skills
  - aligned prompts, tools, workflow docs, and restart surfaces
  - one canonical next action
- Change greenfield completion language from "contract-conformant" to "immediately continuable."

### Primary files

- `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`
- `skills/ticket-pack-builder/SKILL.md`
- `skills/handoff-brief/SKILL.md`
- shared verifier module
- `scripts/validate_scafforge_contract.py`
- `scripts/smoke_test_scafforge.py`

### Done when

- A fresh scaffold cannot be marked complete while `bootstrap.status` is only `"missing"` and no proof exists.
- Handoff cannot publish “ready” unless the first legal move has been verified on the generated repo surface.

## Phase 3: Shrink And Refocus Audit

### Objective

Solve the audit-bloat problem directly.

### Changes

- Reduce `skills/scafforge-audit/SKILL.md` to procedure, evidence rules, and output contract.
- Make `scafforge-audit` consume the shared verifier engine rather than owning all finding extraction itself.
- Move issue-specific smell growth out of prose-heavy references and into machine-readable rule definitions plus regression fixtures.
- Refactor `audit_repo_process.py` into smaller rule modules grouped by invariant family:
  - next-move clarity
  - canonical truth drift
  - bootstrap and execution-surface defects
  - ticket graph and reconciliation defects
  - restart-surface contradictions
- Keep a small fixed set of audit invariants tied to the competence contract.
- Require every new smell code to land with:
  - rule implementation
  - fixture
  - smoke/integration coverage
  - target repair or verifier expectation
  - ownership of whether it belongs in verifier-only logic or audit-only policy

### Primary files

- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-audit/scripts/audit_repo_process.py`
- shared verifier module
- `skills/scafforge-audit/references/*`
- new audit rule data/modules
- `scripts/smoke_test_scafforge.py`

### Done when

- Audit documentation gets shorter as capability improves.
- Adding a new failure class requires a testable rule, not just more narrative documentation.

## Phase 4: Make Repair Convergent And Bounded

### Objective

Repair must stop leaving repos in half-repaired interpretive states.

### Changes

- Add a machine-readable stale-surface map to repair output with categories:
  - `stable`
  - `replace`
  - `regenerate`
  - `ticket_follow_up`
  - `human_decision`
- Keep `run_managed_repair.py` as the public owner of repair orchestration.
- Define two explicit repair layers:
  - deterministic managed-surface refresh plus fail-closed verification record
  - project-specific follow-on regeneration owned by the public repair contract
- Do not claim near-term one-command repair atomicity for repo-local skills, agents, or prompt hardening while those stages are still non-deterministic.
- Reduce repair outcomes to:
  - `clean`
  - `source_follow_up`
  - `managed_blocked`
- Group deterministic regeneration by contract family so related surfaces refresh together:
  - workflow tools and prompts
  - repo-local skills
  - restart surfaces
  - ticket graph and follow-up routing
- Replace assertion-only follow-on completion with recorded execution state over time; treat the current `--stage-complete` model as transitional, not final architecture.
- Fail repair verification if:
  - zero findings are reported but `current_state_clean` is false
  - restart surfaces disagree with canonical state
  - placeholder local skills survive refresh

### Primary files

- `skills/scafforge-repair/SKILL.md`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- new stale-surface map format

### Done when

- Repair can no longer silently finish with contradictory “clean but not clean” semantics.
- Every required follow-on stage is explicit and machine-readable.
- The plan is honest about which parts are deterministic and which still require orchestrated regeneration.

## Phase 5: Harden Generated Repo Execution Surfaces

### Objective

Eliminate the recurring deadlock families seen in GPTTalker.

### Changes

- Make `environment_bootstrap.ts` dependency-layout-aware by default and treat repeated same-trace failures as managed defects.
- Add explicit host/tool-surface classification for missing executables and permission restrictions.
- Make `smoke_test.ts` use the ticket acceptance command as canonical smoke scope when present.
- Parse shell-style env-prefix commands correctly.
- Reject heuristic smoke fallback when an explicit acceptance command exists.
- Keep helper internals private so agents only see executable tool surfaces.
- Make `ticket_reverify` the legal closed-ticket trust-restoration path without ordinary write-lease deadlock.
- Make `ticket_reconcile` first-class for split-scope and stale lineage correction.
- Compute restart-surface next action from canonical state instead of summary prose.

### Primary files

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_reverify.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_reconcile.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- prompt and restart templates

### Done when

- GPTTalker-class bootstrap and smoke deadlocks are covered by deterministic regression tests.
- Restart surfaces stop telling agents to “continue lifecycle” on already-closed work.

## Phase 6: Add A First-Class Pivot Skill

### Objective

Make midstream feature and design change a clear lifecycle path instead of an improvised combination of refine, audit, and repair.

### New skill

Add `skills/scafforge-pivot/` as a host-side lifecycle skill.

### Why a new skill is justified

- Pivot is a real lifecycle stage, not just backlog refinement.
- It crosses brief truth, managed workflow, prompts, skills, ticket graph, and restart surfaces.
- Hiding it across existing skills is exactly what currently makes midstream change confusing.

### Responsibilities of `scafforge-pivot`

- classify the pivot
- update canonical truth first
- emit a stale-surface map
- decide which downstream surfaces must refresh
- route ticket supersede/reopen/follow-up behavior
- require post-pivot verification before handoff

It must not become a second scaffold engine or a second repair engine.

### Pivot classes

- `feature-add`
- `feature-expand`
- `design-change`
- `architecture-change`
- `workflow-change`

### Pivot flow

```text
scaffold-kickoff
  -> scafforge-pivot
      -> update CANONICAL-BRIEF and Pivot History
      -> classify pivot and emit stale-surface map
      -> run safe managed refresh through scafforge-repair only if workflow surfaces drifted
      -> regenerate affected skills, agents, and prompts only where needed
      -> refine, reopen, supersede, or reconcile affected tickets
      -> run shared-verifier post-pivot gate
  -> handoff-brief
```

### Required pivot outputs

- `docs/spec/CANONICAL-BRIEF.md` updated with a `Pivot History` section
- machine-readable stale-surface map
- ticket graph changes with clean lineage
- restart surfaces showing pivot state truthfully
- post-pivot verification result

### Primary files

- new `skills/scafforge-pivot/SKILL.md`
- `skills/skill-flow-manifest.json`
- `skills/scaffold-kickoff/SKILL.md`
- `skills/ticket-pack-builder/SKILL.md`
- shared verifier module
- brief templates and restart templates
- verification and smoke tests

### Done when

- The user can say “add this feature” or “change this design” and Scafforge routes one explicit pivot flow.
- Pivots cannot silently leave old tickets pretending to fit the new design.

## Phase 7: Rebuild Verification Around Curated Regression Fixtures

### Objective

Convert churn evidence into repeatable package protection.

### Changes

- Create curated fixtures from GPTTalker for:
  - bootstrap dependency-layout drift
  - missing-tool / permission blockage
  - repeated lifecycle contradiction
  - restart-surface drift after repair
  - stale placeholder skill after refresh
  - split-scope and historical trust reconciliation
- Add an end-to-end greenfield integration test.
- Add a post-repair integration test.
- Add a pivot integration test.
- Make smoke tests hermetic where possible and prerequisite-gated where not.

### Primary files

- `scripts/smoke_test_scafforge.py`
- new integration test fixtures
- `scripts/validate_scafforge_contract.py`

### Done when

- Known failure families can be reproduced without dragging the entire historical archive into the product repo.
- Verification failures tell us which invariant regressed, not just that “something broke.”

## Phase 8: Rollout And Migration

### Objective

Ship the remediated contract without leaving generated repos stranded.

### Changes

- Bump the process version once the new lifecycle is stable.
- Publish a managed migration path for existing generated repos.
- Use GPTTalker as the first full revalidation subject.
- Run exactly one fresh post-package revalidation on migrated repos before any repair pass.
- Regenerate managed surfaces, then verify, then publish handoff.

### Done when

- Existing repos can migrate without another audit-repair spiral.
- GPTTalker validates the new contract end to end.

## Order Of Implementation

1. Phase 0: contract freeze and archive cleanup
2. Phase 1: lifecycle architecture and shared verifier extraction
3. Phase 2: proof-first greenfield
4. Phase 3: audit shrink/refactor
5. Phase 4: bounded repair and stale-surface map
6. Phase 5: tool and restart-surface hardening
7. Phase 6: pivot skill
8. Phase 7: regression fixtures and integration tests
9. Phase 8: rollout and GPTTalker revalidation

## Definition Of Done

This remediation is done only when:

- greenfield, repair, and pivot each have one explicit completion gate
- audit is diagnosis-only again
- the package proves one legal next move on a fresh generated repo
- restart surfaces are derived, atomic, and truthful
- placeholder local skills cannot survive generation or repair
- the product repo no longer contains bulk audit exhaust
- GPTTalker no longer reproduces the historical post-repair deadlock pattern
