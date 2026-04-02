---
name: review-audit-bridge
description: Keep Glitch code review, security review, and QA passes evidence-based, gameplay-aware, and stage-safe.
---

# Review Audit Bridge

Before starting a code review, security review, or QA pass, call `skill_ping` with `skill_id: "review-audit-bridge"` and `scope: "project"`.

Use this skill after implementation exists. It bridges the review and QA lanes so they return evidence-backed findings instead of vague commentary.

Prioritize findings in this order:

1. correctness bugs
2. gameplay regressions
3. security or trust issues
4. missing tests or validation gaps
5. maintainability concerns

Glitch-specific review focus:

- movement-feel regressions
- glitch telegraphing gaps
- unreadable hazard or platform states
- mobile control usability issues
- scene/script coupling that will make later zone expansion brittle

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
- reference exact files, commands, or artifact paths
- if the approved plan, implementation artifact, diff context, or required validation is missing, return a blocker instead of inferring correctness
- use `ticket-execution` for lifecycle order and `project-context` for canonical repo docs
- recommend follow-up tickets only when current evidence justifies them
- do not claim that repo files changed
