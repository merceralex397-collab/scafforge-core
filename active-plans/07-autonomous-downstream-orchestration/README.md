# Autonomous Downstream Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Build the orchestration layer that accepts an approved brief, runs the standard Scafforge greenfield flow, drives downstream work through PR-based phases, and resumes safely after repair without breaking the package’s one-shot contract.

**Architecture:** The orchestration layer wraps Scafforge; it does not replace it. An adjacent service should own job intake, state transitions, PR/review automation, pause/retry/resume controls, and evidence aggregation. Scafforge remains responsible for scaffold generation, repo contract surfaces, audit, repair, and handoff publication.

**Tech Stack / Surfaces:** adjacent orchestration service or repo, Scafforge skills, generated repo templates, GitHub PR/review workflows, package restart/handoff surfaces.
**Depends On:** `06-spec-factory-and-intake-mcp`, `09-sdk-model-router-and-provider-strategy`, `05-completion-validation-matrix`.
**Unblocks:** `10-viewer-control-plane-winui` and parts of the autonomous factory vision.
**Primary Sources:** `_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`, `_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`, current package workflow contracts in `AGENTS.md`, `references/one-shot-generation-contract.md`, and generated template plugins/docs.

---

## Problem statement

The current autonomous vision mixes together:

- spec approval
- Scafforge generation
- downstream execution
- review/merge gates
- recovery and resume

Without a clear wrapper contract, autonomy will either dissolve package boundaries or recreate them badly in a second hidden workflow engine.

## Required deliverables

- a state model for orchestration jobs
- a trigger contract from approved brief to scaffold kickoff
- phase-to-PR rules for downstream work
- reviewer and merge-gate rules
- failure routing into audit and repair
- safe resume semantics after repo repair or package improvement

## Proposed orchestration state model

The service should converge on explicit states such as:

`approved-brief-received -> scaffold-running -> scaffold-verified -> phase-ready -> phase-in-progress -> pr-open -> review-blocked|merge-ready -> merged -> next-phase`

Failure and recovery branches:

`blocked -> audit-requested -> repair-pending -> revalidation-pending -> resume-ready`

The key rule is that orchestration state is derived from package truth and review results, not invented independently in the UI.

## Package and adjacent surfaces likely to change during implementation

### Scafforge package surfaces

- `skills/scaffold-kickoff/SKILL.md`
- `skills/repo-scaffold-factory/`
- `skills/ticket-pack-builder/SKILL.md`
- `skills/scafforge-audit/`
- `skills/scafforge-repair/`
- `skills/handoff-brief/assets/templates/START-HERE.template.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- generated process docs and ticket docs under the project template

### Adjacent orchestration surfaces

- orchestration service/repo
- job queue and state persistence
- GitHub PR/review integration
- worker runners that invoke Scafforge and downstream agents
- event stream for dashboards and operator controls

## Ownership boundaries this plan must preserve

- The spec factory owns idea-to-approved-brief workflow.
- Scafforge owns generation, audit, repair, ticket pack structure, and restart publication.
- The orchestration service owns job progression, phase scheduling, PR automation, and resumption.
- The control plane app is only a client of orchestration truth, not the owner of it.

## Phase plan

### Phase 1: Freeze the orchestration job contract

- [ ] Define the job envelope: approved brief pointer, repo identity, branch strategy, execution mode, model/router policy, and operator permissions.
- [ ] Define the state transitions the orchestration layer is allowed to perform directly versus those it must infer from Scafforge or GitHub outputs.
- [ ] Decide where idempotency keys and retry tokens live so retries do not duplicate repo creation or PR spam.
- [ ] Specify the evidence each state must retain for later audit or operator review.

### Phase 2: Define the greenfield invocation boundary

- [ ] Specify exactly how an approved brief triggers `scaffold-kickoff`.
- [ ] Define what counts as a successful scaffold result before downstream work begins.
- [ ] Record which generated artifacts the orchestration service must read to continue: tickets, restart surface, workflow state, and any package provenance.
- [ ] Define failure handling when the scaffold step fails before downstream repo execution even begins.

### Phase 3: Define phase-to-PR workflow rules

- [ ] Decide how downstream work is broken into phases and how those phases map to ticket bundles or ticket groups.
- [ ] Require every autonomous phase to end in an explicit PR or reviewable diff rather than a silent merge to main.
- [ ] Define branch naming, reviewer assignment, and evidence attachment rules for those PRs.
- [ ] Specify when a phase may be retried, split, paused, or escalated to a human reviewer.

### Phase 4: Define review and merge gating

- [ ] Write reviewer rules that cross-check PRs against the original spec, ticket requirements, validation artifacts, and stack-specific expectations.
- [ ] Decide which failures are fix-and-resubmit, which require audit, and which require human approval.
- [ ] Define merge policy for fully autonomous, merge-approval, and strict/human-in-the-loop operating modes.
- [ ] Ensure no PR can merge without the required stage-gate and validation evidence.

### Phase 5: Define failure routing and resume semantics

- [ ] Define the trigger matrix for when downstream failure routes into `scafforge-audit` rather than simple task retry.
- [ ] Define how `scafforge-repair` output is fed back into the orchestration state machine.
- [ ] Specify what must be revalidated before the orchestration service marks a repo `resume-ready`.
- [ ] Prevent the orchestration layer from losing causality when a repo-level fix and a package-level fix interact.

### Phase 6: Dry-run the whole wrapper path

- [ ] Run a small approved brief through greenfield generation and the first downstream phase.
- [ ] Force at least one PR review rejection and verify the repo does not merge prematurely.
- [ ] Force a repair-and-resume case and confirm the state model remains truthful.
- [ ] Confirm the wrapper never violates the one-shot Scafforge generation contract by mutating package-owned truth itself.

## Validation and proof requirements

- an approved brief can trigger generation without bypassing Scafforge contracts
- every downstream phase has an explicit PR/review boundary
- failure and resume paths are visible and attributable
- the orchestration layer can be paused, retried, or resumed without corrupting package or repo truth

## Risks and guardrails

- Do not let the orchestration service become a second scaffold engine.
- Do not hide state in the control plane UI or chat transcripts.
- Do not merge phase work directly to main just because the service “thinks” it is safe.
- Preserve a strict distinction between package defects and repo-local bugs.

## Documentation updates required when this plan is implemented

- package references describing how external orchestration calls Scafforge
- generated process docs and restart guidance where PR-phase rules surface in repos
- orchestration service docs in its own repo/workspace
- operator docs for pause/retry/resume semantics

## Completion criteria

- an approved brief can move through scaffold, PR-based phase execution, review, and resume truthfully
- the orchestration wrapper preserves Scafforge’s authority boundaries
- review and merge gates are explicit and testable
- downstream recovery after audit/repair is part of the design, not an afterthought
