# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## WFLOW016

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The generated `smoke_test` tool passes `command_override` directly into `spawn()` argv and does not separate shell-style environment assignments like `UV_CACHE_DIR=...` from the executable. Valid repo-standard override commands can therefore misfire as `ENOENT` instead of running the intended smoke check.
- Safer target pattern: Parse one-item shell-style overrides into argv, treat leading `KEY=VALUE` tokens as environment overrides, and report malformed overrides as configuration errors instead of misclassifying them as runtime environment failures.

## WFLOW016

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The generated `smoke_test` tool treated a shell-style environment assignment like `UV_CACHE_DIR=...` as the executable name for `spawn()`. That turns a valid explicit override command into an `ENOENT` tool failure and misclassifies the result as a runtime environment problem.
- Safer target pattern: Parse shell-style smoke-test overrides before execution, strip leading `KEY=VALUE` env assignments into the spawn environment, and report malformed overrides as configuration errors rather than environment failures.

## EXEC003

- Surface: generated repo implementation and validation surfaces
- Root cause: Tests were marked done in QA artifacts without verifying the full suite passes. Failing tests indicate incomplete implementations, broken contracts, or regressions.
- Safer target pattern: Run `pytest tests/ -v` and fix all failures before marking a ticket done. QA artifacts must include pytest output showing 0 failures.

## WFLOW008

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The workflow contract changed, but the repo still contains completed tickets whose trust predates the current process window or lacks current backlog-verification evidence. Declaring the repo clean before that reverification finishes hides unresolved process risk.
- Safer target pattern: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, and do not call verification clean until `ticket_reverify` or current backlog-verification evidence clears those tickets.

