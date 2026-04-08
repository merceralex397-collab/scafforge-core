# Scafforge Prevention Actions

## Package Changes Required

### PA-01

- change target: managed smoke-test tool for Python repos
- why it prevents recurrence:
  - a repo with `uv.lock` or `.venv` should not default to system `python3 -m pytest`
  - eliminating the false smoke-test deadlock removes the main trigger for the bad inference
- safe or intent-changing: safe
- validation:
  - rerun `EXEC-001`-style smoke tests and confirm the tool chooses repo-managed Python execution

### PA-02

- change target: handoff publication / closeout prompt contract
- why it prevents recurrence:
  - restart summaries should distinguish:
    - ticket-local acceptance proved
    - downstream dependent ticket still unverified
  - require a direct citation of which commands actually ran before allowing statements like "unblocked" or "not a code defect"
- safe or intent-changing: safe
- validation:
  - create a regression case where collection passes, closeout deadlocks, and the full suite was never run; the handoff must not claim the full problem space is only tooling

### PA-03

- change target: Scafforge audit package
- why it prevents recurrence:
  - the audit should detect when a published handoff summary outruns the executed evidence in the session/artifact trail
- safe or intent-changing: safe
- validation:
  - feed the package a fixture with:
    - smoke-test deadlock
    - no full-suite run
    - final handoff saying only tooling blocks progress
  - expect a finding

## Validation and Test Updates

### PA-04

- change target: workflow validation rules
- why it prevents recurrence:
  - when a ticket explicitly references a dependent full-suite follow-up like `EXEC-002`, the system should not allow "unblocked" language unless the dependency ticket is actually claimable or the suite step has run
- safe or intent-changing: safe
- validation:
  - add a rule-based test around dependency gating plus handoff publication

## Documentation or Prompt Updates

### PA-05

- change target: team-leader / QA / closeout guidance
- why it prevents recurrence:
  - agents need explicit wording that missing execution evidence is not neutral
  - "not a code defect" is too broad unless the relevant downstream verification step was actually executed
- safe or intent-changing: safe
- validation:
  - session simulation should refuse the over-broad wording when the full suite has not run

### PA-06

- change target: workflow terminology and tool contract around review stages
- why it prevents recurrence:
  - the transcript shows sustained confusion over whether `review` means plan review or implementation review
  - the system should either expose distinct states or make the approval path tool-driven and non-ambiguous
- safe or intent-changing: safe
- validation:
  - an agent starting from planning must be able to reach implementation without inventing `_workflow_*` bypasses or reasoning around conflicting stage meanings

### PA-07

- change target: host-side `scafforge-audit` skill behavior
- why it prevents recurrence:
  - this audit skill initially missed the actual question because it did not front-load transcript chronology analysis when a session log was supplied
  - session logs should be treated as first-class temporal evidence, not just candidate claims to compare against current state
- safe or intent-changing: safe
- validation:
  - add a regression case where:
    - current repo state differs from earlier session state
    - the user asks why the agent wrote a later incorrect summary
  - expected audit output must identify both the historical truths and the later reasoning failure

## Open Decisions

- whether handoff publication should be blocked outright when required downstream verification for the next dependent ticket has not run
- whether audit should parse session transcripts directly or rely on canonical artifacts plus selected transcripts when available
- whether stage names should be expanded to separate plan review from implementation review instead of relying on one overloaded `review` label
