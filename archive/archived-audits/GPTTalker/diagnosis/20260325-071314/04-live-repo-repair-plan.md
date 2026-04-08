# Live Repo Repair Plan

## Preconditions

- this diagnosis is read-only with respect to product code; only the diagnosis pack was updated
- `EXEC-001` remains open in `smoke_test`
- `EXEC-002` remains open in `planning`
- current reproduced execution state:
  - collection passes in the repo environment
  - full suite fails (`40 failed, 86 passed`)

## Package Changes Required First

### RP-01

- linked finding ids: `R1-F1`, `PF-01`, `PF-02`
- action type: safe Scafforge package change
- target repo: Scafforge package repo
- should `scafforge-repair` run: yes, but only after package-side fixes exist
- must the user manually carry the diagnosis pack first: yes
- action:
  - carry this diagnosis pack into the Scafforge dev repo
  - fix the managed smoke-test tool and audit script/package surfaces identified in Report 3

## Post-Update Repair Actions

### RP-02

- linked finding ids: `R1-F1`
- action type: generated-repo remediation ticket/process repair
- target repo: subject repo
- should `scafforge-repair` run: yes
- must the user manually carry the diagnosis pack first: yes, because package work is required first
- action:
  - after the package fixes exist, return to this repo and run `scafforge-repair` to refresh the managed workflow surfaces
  - rerun `smoke_test` for `EXEC-001` using the refreshed managed tool

### RP-03

- linked finding ids: `R1-F2`, `R1-F3`, `R1-F4`, `R1-F5`, `R1-F6`
- action type: generated-repo remediation ticket/process repair
- target repo: subject repo
- should `scafforge-repair` run: no, these are source-layer fixes
- must the user manually carry the diagnosis pack first: no for the source fixes themselves, but `EXEC-001` closeout still depends on `RP-02`
- action:
  - once the managed smoke-test path is repaired, continue with source-layer remediation for the failing full suite

## Ticket Follow-Up

- existing tickets:
  - keep `EXEC-001` open until the managed smoke-test surface is repaired and a passing managed smoke-test artifact is recorded
  - keep `EXEC-002` as the umbrella for full-suite execution recovery unless the user prefers it split
- recommended ticket proposals:
  - `EXEC-003` — Fix node-agent executor path validation so absolute paths inside `allowed_paths` are accepted and bounded operations work again
  - `EXEC-004` — Fix hub repo-path normalization so valid repo-relative inspection/read paths do not fail boundary checks
  - `EXEC-005` — Align hub tool/transport contracts (`write_markdown` parameter shape and MCP response payload shape) with the test contract
  - `EXEC-006` — Fix structured logging redaction semantics for nested objects, lists, truncation, and max-depth handling

## Reverification Plan

1. After Scafforge package work lands, rerun `scafforge-repair` in this repo and repeat the managed smoke-test stage for `EXEC-001`.
2. Re-run:
   - `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app"`
   - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ --collect-only -q --tb=no`
   - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=no`
3. Only treat the repo as clear when:
   - `EXEC-001` is `done`
   - `EXEC-002` acceptance is fully satisfied
   - the derived handoff surfaces no longer overstate downstream readiness
