# Scafforge Process Failures

## Scope

- Subject repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-25T07:26:08Z`
- Mapping scope: explain why the agent wrote the final blocker summary in the observed session

## Failure Map

### PF-01

- linked Report 1 finding id: `R1-F2`
- implicated surface:
  - repo-local agent workflow / stage reasoning
  - handoff publication behavior
- ownership classification: generated-repo managed-surface drift
- explanation:
  - the session correctly advanced from stale resume state into implementation, review, and QA
  - once `smoke_test` blocked closeout, the agent reasoned from ticket-local acceptance only
  - no process guard forced execution of the downstream full-suite check before publishing the restart summary
  - the result was a derived handoff that treated `EXEC-002` as blocked only by dependency status rather than by still-unverified full-suite results

### PF-02

- linked Report 1 finding ids: `R1-F1`, `R1-F3`
- implicated surface:
  - managed smoke-test tool
- ownership classification: generated-repo managed-surface drift
- explanation:
  - the smoke-test tool selected system `python3 -m pytest` instead of the repo-managed environment
  - this created a real closeout deadlock for `EXEC-001`
  - the deadlock then dominated the agent's reasoning and pushed it toward an over-narrow blocker explanation

### PF-03

- linked Report 1 finding id: `R1-F4`
- implicated surface:
  - bundled Scafforge audit script
- ownership classification: Scafforge package defect
- explanation:
  - the packaged audit script returns no findings even when the session log and live checks show a reasoning/verification failure with active execution fallout
  - the current package surface is not catching "published handoff overstates verified status" cases

### PF-04

- linked Report 1 finding ids: `R1-F5`, `R1-F6`
- implicated surface:
  - team-leader prompting / workflow contract
  - host-side audit method
- ownership classification: Scafforge package defect
- explanation:
  - the workflow surface did not make the distinction between plan review and implementation review operationally unambiguous to the agent
  - the audit method did not parse the transcript as a reasoning timeline, so the first audit pass missed the agent-confusion pattern and initially answered the wrong question

## Ownership Classification

- `R1-F1`: generated-repo managed-surface drift
- `R1-F2`: generated-repo managed-surface drift
- `R1-F3`: generated-repo managed-surface drift
- `R1-F4`: subject-repo source bug, exposed by inadequate verification flow
- `R1-F5`: Scafforge package defect
- `R1-F6`: Scafforge package defect

## Root Cause Analysis

### Root Cause A

- the agent had two different truths in one session:
  - stale historical resume state from the top of the log
  - newer implementation/QA evidence gathered later
- that alone did not cause the bad final summary; the real failure came later when the agent stopped short of the full-suite step

### Root Cause B

- the smoke-test deadlock created a misleading local optimum:
  - import passed
  - collection passed
  - closeout tool failed for environment reasons
- the agent then inferred "tool/env mismatch is the blocker" and generalized that to the repo state without the missing full-suite evidence

### Root Cause C

- handoff publication accepted an inference-heavy next-action summary instead of forcing evidence-backed wording tied to executed commands

### Root Cause D

- workflow terms that are clear to a human reader were not sufficiently operationalized for the agent:
  - "plan review" existed in docs and skill guidance
  - "review" in the actual tool path behaved like post-implementation review
  - that ambiguity produced a real confusion loop in the transcript

### Root Cause E

- the audit path had its own bias:
  - inspect canonical current state
  - reproduce current failures
  - only secondarily inspect session chronology
- for this class of issue, that order is insufficient because the core defect is a reasoning mistake visible only in transcript sequencing
