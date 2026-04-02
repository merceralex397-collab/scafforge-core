---
name: review-audit-bridge
description: Keep code review, security review, and QA passes evidence-based and stage-aware for this repo. Use when a ticket already has an approved plan and implementation evidence and a review lane needs structured findings.
---

# Review Audit Bridge

Before starting a code review, security review, or QA pass, call `skill_ping` with `skill_id: "review-audit-bridge"` and `scope: "project"`.

Use this skill after implementation exists. It bridges the review and QA lanes so they return evidence-backed findings instead of vague commentary.
This is a generated repo-local skill. It may recommend remediation or reverification follow-up, but it does not become the canonical ticket owner by itself.

Prioritize findings in this order:

1. correctness bugs
2. behavior regressions
3. security or trust issues
4. missing tests or validation gaps
5. maintainability concerns

Return:

- For code review or security review:
  1. Findings ordered by severity
  2. Risks
  3. Validation gaps
  4. Blockers or approval signal
- For QA:
  1. Checks run
  2. Pass or fail
  3. Blockers
  4. Closeout readiness

Rules:

- findings come first; do not open with praise or a summary
- reference exact files, diffs, commands, or artifact paths
- if the approved plan, implementation artifact, or required validation context is missing, return a blocker instead of inferring correctness
- use `ticket-execution` for lifecycle order and `project-context` for canonical repo docs
- run the repo's build command, lint or type-check command, and reference-integrity checks when those quality gates exist for the active stack; include the raw command output in the review or QA artifact
- if any required build, lint, type-check, or reference-integrity command fails, the verdict must be FAIL and the artifact must name the failing command plus the concrete error
- when reviewing or validating a remediation ticket with `finding_source`, rerun the original finding-producing command first, confirm the specific failure is gone, then check that adjacent quality gates still pass
- write any workflow-failure explanation or review retrospective to the repo-local process-log path described in `references/review-contract.md`
- recommend follow-up tickets only when current evidence justifies them, and route canonical ticket creation through the repo's guarded ticket workflow
- do not claim that repo files changed

## References

- `references/review-contract.md`
