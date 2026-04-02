# Review Contract

Use this reference when a generated repo needs slightly heavier guidance for review, QA, or remediation follow-up than should fit in the main skill body.

## Purpose

- keep review output evidence-backed
- explain workflow failures without mutating canonical queue state by hand
- recommend remediation or reverification follow-up only when current proof supports it

## Output shape

For code review or security review:
1. findings ordered by severity
2. risks
3. validation gaps
4. blocker or approval signal

For QA:
1. checks run
2. pass or fail
3. blockers
4. closeout readiness

## Process-log guidance

- if the repo tracks diagnosis or review retrospectives under `diagnosis/`, write the process log there
- otherwise use the repo-local review-log or handoff path defined by project docs
- process logs explain what went wrong and what proof was missing; they do not replace canonical ticket, artifact, or workflow-state updates

## Ticket recommendation rules

- recommend a new follow-up ticket when the issue is net-new, scoped, and supported by current evidence
- recommend reopening or reverification when the historical ticket already owns the issue and current evidence links back cleanly
- do not create or mutate canonical tickets directly from this skill unless the repo's guarded ticket tools explicitly own that action
