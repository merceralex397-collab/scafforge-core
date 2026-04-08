# Live Repo Repair Plan

## Preconditions

- this diagnosis is read-only except for the diagnosis pack itself
- the question answered here is causal: why the agent wrote the blocker summary, not whether the smoke-test mismatch existed

## Package Changes Required First

### RP-01

- linked finding ids: `R1-F2`, `R1-F3`, `R1-F5`, `R1-F6`, `PF-02`, `PF-03`, `PF-04`
- action type: safe Scafforge package change
- target repo: Scafforge package repo
- should `scafforge-repair` run: yes, but only after package-side fixes exist
- must the user manually carry the diagnosis pack first: yes
- action:
  - carry this pack into the Scafforge dev repo
  - fix the smoke-test tool, review-stage ambiguity, handoff evidence contract, and audit detection described in Report 3

## Post-Update Repair Actions

### RP-02

- linked finding ids: `R1-F3`
- action type: generated-repo remediation ticket/process repair
- target repo: subject repo
- should `scafforge-repair` run: yes
- must the user manually carry the diagnosis pack first: yes
- action:
  - refresh the managed workflow surfaces after Scafforge package fixes land
  - rerun `EXEC-001` smoke-test with the refreshed tool

### RP-03

- linked finding ids: `R1-F4`
- action type: generated-repo remediation ticket/process repair
- target repo: subject repo
- should `scafforge-repair` run: no
- must the user manually carry the diagnosis pack first: no
- action:
  - continue source-layer remediation for the still-failing full suite after the managed smoke-test deadlock is removed

## Ticket Follow-Up

- preserve the existing understanding:
  - `EXEC-001` was locally fixed but is blocked by managed-surface smoke-test behavior
  - `EXEC-002` still needs real full-suite work and should not be treated as merely dependency-blocked
- recommended follow-up ticket focus:
  - one workflow-layer ticket for smoke-test/handoff evidence integrity
  - one workflow-layer ticket for plan-review vs implementation-review stage clarity
  - one Scafforge-audit ticket for transcript-first chronology analysis when session logs are supplied
  - one or more source-layer tickets for the reproduced full-suite failures

## Reverification Plan

1. After package-side fixes land, rerun `scafforge-repair` in this repo.
2. Re-run:
   - `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app"`
   - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ --collect-only -q --tb=no`
   - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=no`
3. Regenerate handoff surfaces and verify they do not claim only a tooling blocker unless the full downstream verification scope is actually complete.
