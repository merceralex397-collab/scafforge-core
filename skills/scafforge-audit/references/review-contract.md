# Scafforge Audit Review Contract

## Inputs

- current repo workflow and source-of-truth docs
- current repo ticket contract
- pull request diff, commits, and review comments when review evidence exists
- supplied session logs or transcript exports when the user is asking a causal question
- diagnosis-pack scope when the audit needs to emit four reports into `diagnosis/`

## Output contract

- separate `valid`, `partially_valid`, `outdated`, and `invalid` findings
- assign each surviving finding a severity: `critical`, `major`, or `minor`
- assign each surviving finding an evidence grade: `observed`, `reproduced`, `inferred`, `external-only`, or `missing`
- assign each surviving finding an ownership classification:
  - `Scafforge package defect`
  - `generated-repo managed-surface drift`
  - `repo-specific customization drift`
  - `subject-repo source bug`
- explain why each accepted finding survives review
- cite the concrete file, hunk, comment, or commit that supports the decision
- include a rejection rationale for every non-accepted finding
- list any human blockers with a clear owner and reason
- keep diagnosis output read-only apart from the intentional `diagnosis/` report folder
- preserve the distinction between historical session truth and current repo truth when both are relevant

When review evidence is present, follow `pr-review-workflow.md` before the finding enters the diagnosis pack.

## Canonical ticket proposal contract

Unless the repo explicitly exposes a safe non-migration intake tool for review work, return ticket **proposals** instead of mutating the repo backlog directly.

For generated-repo v2 ticket contracts, each proposed ticket should include:

- `id`
- `title`
- `wave`
- `lane`
- `parallel_safe`
- `overlap_risk`
- `stage`
- `status`
- `depends_on`
- `summary`
- `acceptance`
- `decision_blockers`
- `artifacts`

Defaults for ordinary PR-review follow-up:

- `stage: planning`
- `status: todo` unless blocked by an unresolved decision
- `artifacts: []`

For diagnosis-pack routing, attach each ticket proposal to the relevant Report 4 item instead of creating a parallel review-only backlog surface.

## Ticket quality rules

- one clear issue per ticket
- actionable summary
- explicit acceptance criteria
- link back to the originating PR evidence
- no duplicate tickets for already-tracked work
- do not route ordinary PR-review findings through migration-only backlog-verifier / `ticket_create` flows
- when a diagnosis pack exists, link ticket proposals back to Report 4 or its machine-readable payload rather than inventing a parallel review-only state surface
