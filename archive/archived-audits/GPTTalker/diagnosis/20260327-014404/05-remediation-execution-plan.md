# GPTTalker Remediation Execution Plan

## Summary

Stop the audit/repair loop. The repo is no longer blocked by `repair_follow_on`; `uv run pytest` works on this WSL environment, so the blocker is not a missing global `pytest` install.

The repo is stuck because:

- `EXEC-008` is still open and its own acceptance requires `tests/hub/test_security.py` to pass.
- `EXEC-012` was created from stale evidence, now describes the wrong failing cases, and is blocked behind `EXEC-008`.
- The remaining source failures are already bucketed cleanly:
  - `EXEC-008`: 1 failing security test expectation
  - `EXEC-009`: 2 node-agent failures
  - `EXEC-010`: 3 logging failures

Chosen resolution: collapse `EXEC-012` into `EXEC-008`, retire `EXEC-012` as stale/duplicate, and make the project surfaces say that explicitly so the OpenCode agent cannot misroute again.

## Immediate Canonical-State Fixes

Start by clearing or re-owning the current `EXEC-008` lease.

- Use `lease_cleanup` if the current session cannot prove it owns the existing `gpttalker-team-leader` lease.
- Claim `EXEC-008` explicitly before any write-capable work.

Collapse `EXEC-012` into `EXEC-008` in the canonical ticket surfaces.

Set `EXEC-012` to:

- `stage: closeout`
- `status: done`
- `resolution_state: superseded`
- `verification_state: invalidated`
- top-of-ticket note: `Superseded on 2026-03-27. This ticket captured stale path-test cases and was merged back into EXEC-008. Do not resume separately.`

Remove the live dependency confusion everywhere it is canonical.

- Remove `EXEC-012` from `EXEC-008` follow-up references.
- Update `EXEC-008` summary/notes so they state the only remaining blocker is the in-bounds path expectation in `test_path_traversal_dotdot_rejected`.
- Keep historical artifacts intact; do not rewrite old review/QA bodies.
- Regenerate all derived restart surfaces after the ticket edits so `START-HERE`, context snapshot, latest handoff, and board no longer imply `EXEC-012` is the thing blocking `EXEC-008`.

Do not run another audit or repair pass before source progress.

- The next meaningful work is ticket execution, not more diagnosis.

## Execution Order

### 1. Finish `EXEC-008`

In `tests/hub/test_security.py`:

- remove `foo/bar/../../secrets` from the traversal-rejection list
- add an explicit positive assertion that `foo/bar/../../secrets` normalizes to an in-bounds repo path

Do not change `PathNormalizer` for this ticket unless a fresh failing case proves a real code bug; current direct execution shows the implementation is behaving correctly for the live cases.

Validate with the exact acceptance command:

```sh
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no
```

Then run the repo workflow closeout path for the ticket:

- `smoke_test` for `EXEC-008`
- move `EXEC-008` to `closeout/done`

### 2. Execute `EXEC-009`

Fix `OperationExecutor.list_directory()` to use a Python 3.11-compatible UTC timestamp path.

Default implementation choice:

- import `UTC` directly from `datetime`
- use `tz=UTC`

Verify `git_status()` still satisfies the ticket acceptance around `recent_commits`; keep the existing ticket scope unless the acceptance command still fails after the timestamp fix.

Validate with:

```sh
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/node_agent/test_executor.py -q --tb=no
```

Then run ticket-local smoke/closeout and mark `EXEC-009` done.

### 3. Execute `EXEC-010`

Tighten `redact_sensitive()` so container keys like `credentials` and `tokens` do not trigger whole-container redaction just because they contain a sensitive substring.

Implementation targets:

- preserve dict/list shape
- redact only sensitive leaves or explicitly sensitive string values
- return the max-depth sentinel string at the cutoff itself
- keep long-string truncation and fail-closed secret coverage unchanged

Validate with:

```sh
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/shared/test_logging.py -q --tb=no
```

Then run ticket-local smoke/closeout and mark `EXEC-010` done.

### 4. Re-establish the repo baseline

Run:

```sh
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=no
```

If that passes, the repo is moving again and the next queued ticket is `EXEC-011` for lint cleanup.

Leave `EXEC-011` as a separate follow-on; do not fold lint work into the unblock path.

## Test Plan

Ticket-local validation:

- `EXEC-008`: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no`
- `EXEC-009`: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/node_agent/test_executor.py -q --tb=no`
- `EXEC-010`: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/shared/test_logging.py -q --tb=no`

Full-suite checkpoint after `EXEC-010`:

- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=no`

Workflow-state acceptance:

- `EXEC-012` no longer appears as a live blocker in manifest/board/restart surfaces
- `EXEC-008`, then `EXEC-009`, then `EXEC-010` progress through normal smoke-test closeout without inventing follow-up tickets for still-open tickets
- no new audit is run until source execution has actually changed the failing test set

## Assumptions

- Use the repo-managed Python environment only. `pytest` is not expected as a global WSL binary; `uv run pytest ...` is the supported path and is already working.
- Preserve history instead of deleting tickets. `EXEC-012` should remain in the repo as a superseded record, not be removed.
- Keep execution sequential. Even though `EXEC-009` and `EXEC-010` are separate lanes, the repo is currently in sequential mode and this plan keeps one active foreground ticket at a time.
