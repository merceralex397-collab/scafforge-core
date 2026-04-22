# Orchestration Wrapper Contract

Scafforge may be wrapped by an **adjacent orchestration service**, but that wrapper must stay outside package-owned generation and generated-repo canonical truth.

## Boundary

- The orchestration service wraps Scafforge; it does not replace `scaffold-kickoff`, `spec-pack-normalizer`, `scafforge-audit`, `scafforge-repair`, or `handoff-brief`.
- The orchestration service owns job progression, phase scheduling, PR automation, pause, retry, resume controls, and dashboard-facing event streams.
- The orchestration service is read-only with respect to generated `tickets/manifest.json` and `.opencode/state/workflow-state.json`.
- The orchestration service may read `docs/spec/CANONICAL-BRIEF.md`, `tickets/manifest.json`, `.opencode/state/workflow-state.json`, `START-HERE.md`, `.opencode/state/latest-handoff.md`, and `.opencode/meta/bootstrap-provenance.json`.
- Phase grouping, PR numbers, reviewer assignment, merge-mode state, retry tokens, and idempotency keys live in orchestration-owned storage, not in the generated repo.
- Operator and dashboard signaling for orchestration-owned states such as `package-change-pending` must also live in orchestration-owned storage or event streams, not in generated repo canonical truth.

## Job envelope

Every orchestration job should retain, at minimum:

- approved brief pointer or bundle address
- downstream repo identity and destination
- branch strategy for phase work
- execution mode
- model/router policy
- operator permission mode
- idempotency key for repo creation or scaffold invocation
- retry token for phase or PR retries
- retained evidence pointers for scaffold proof, PR review, audit, repair, and resume

Persistence format and substrate details remain blocked on plan `09`; this contract freezes the required fields and ownership boundary now.

## State model

The wrapper should converge on explicit job states such as:

`approved-brief-received -> scaffold-running -> scaffold-verified -> phase-ready -> phase-in-progress -> pr-open -> review-blocked|merge-ready -> merged -> next-phase`

The wrapper must keep the failure branches split:

- repo-local path: `blocked -> audit-requested -> repo-repair-pending -> revalidation-pending -> resume-ready`
- package-defect path: `blocked -> audit-requested -> package-change-pending -> downstream-revalidation-pending -> resume-ready`

State transitions the wrapper may write directly:

- intake and queue states such as `approved-brief-received`, `scaffold-running`, `phase-ready`, `phase-in-progress`, `pr-open`, `package-change-pending`, and `downstream-revalidation-pending`
- branch, PR, review assignment, pause, retry, and operator-override state

State transitions the wrapper must infer from Scafforge or GitHub evidence instead of inventing:

- `scaffold-verified`
- `review-blocked`
- `merge-ready`
- `repo-repair-pending`
- `revalidation-pending`
- `resume-ready`

Generated repos may expose derived helper fields such as a local `scaffoldVerified` boolean, but those helpers are implementation details and must stay semantically identical to the wrapper-owned `scaffold-verified` inference described here.

## Greenfield invocation boundary

- A persisted approved-brief bundle is the only legal upstream trigger into Scafforge greenfield generation.
- The wrapper invokes `scaffold-kickoff`; it does not bypass `spec-pack-normalizer` or call lower-level skills as public entrypoints.
- `scaffold-verified` means VERIFY009 persistence confirmation plus zero blocking VERIFY010 and VERIFY011 findings.
- No downstream phase, branch, or PR automation may begin until `scaffold-verified` is true and `handoff-brief` has published the restart surfaces from the verified final snapshot.
- If scaffold generation fails before `scaffold-verified`, the wrapper may retry only when the failure is transient and idempotent; otherwise it should route into audit or operator review instead of silently continuing.

## Phase-to-PR workflow

- The orchestration layer may group one or more ready tickets into a downstream phase, but that grouping remains orchestration-owned state.
- Every autonomous phase must end in an explicit PR or reviewable diff; the wrapper must not merge silent direct-to-main work.
- PR-open, review-blocked, merge-ready, or merge-complete bookkeeping must not be serialized as fabricated backlog tickets or pushed through repo-local ticket mutation tools.
- Branch names should stay job- and phase-scoped, for example `autonomy/<job-id>/phase-<nn>-<slug>`.
- Each PR should retain links to the owning ticket IDs, validation artifacts, canonical brief snapshot, and any required stack-specific evidence.
- Retry, split, pause, or escalation decisions belong to the wrapper, but they must leave the generated repo canonical state untouched until a repo-local tool or skill changes it lawfully.

## Review and merge gates

- Review must cross-check the PR against the canonical brief, the owning tickets, registered artifacts, and stack-specific validation expectations.
- `stage-gate-enforcer`, registered lifecycle artifacts, deterministic smoke evidence, and repo-family completion proof remain the repo-owned merge-gate inputs.
- Review rejection caused by source defects is fix-and-resubmit work on the same phase branch.
- Review rejection caused by workflow contradiction, missing legal-next-move guidance, or managed-surface drift routes into `scafforge-audit`.
- Merge policy may vary by operator mode (`fully-autonomous`, `merge-approval`, `strict`), but no mode may merge without the required repo-owned stage-gate and validation evidence.

## Failure routing and resume semantics

- Use simple retry only for clearly transient failures that did not leave contradictory repo state, duplicate PR spam, or disputed proof.
- Route into `scafforge-audit` when repeated retries fail, review evidence contradicts the lifecycle state, the repo no longer exposes one legal next move, or the failure might be a package defect.
- `repo-repair-pending` begins only after the authoritative diagnosis disposition says safe repo-local repair is the next step.
- `package-change-pending` begins only when the diagnosis disposition says Scafforge package work must land before downstream repair may resume.
- `resume-ready` requires current revalidation evidence plus freshly published restart surfaces from the verified final snapshot.
- Resume must preserve causality by retaining the job's triggering diagnosis pack, the related downstream PR or commit, any package-fix PR or commit, and the revalidation pack that cleared the blocker.
- At minimum, the retained evidence pointers for resume should include the diagnosis pack, audit disposition, downstream PR or commit, package-fix PR or commit when relevant, current revalidation proof, and the restart publication that re-established the legal next move.
- The package-defect wait state remains orchestration-owned state; do not encode `package-change-pending` inside generated repo canonical workflow state.

## Current implementation boundary

- This contract intentionally stops at wrapper behavior and proof semantics.
- Persistence substrate, model-router integration, and dry-run harness implementation remain blocked pending plans `05`, `06`, and `09`.
- Until those plans land, Scafforge should expose the boundary, restart semantics, and merge-gate inputs clearly enough that an adjacent service can implement the wrapper without inventing hidden repo truth.
