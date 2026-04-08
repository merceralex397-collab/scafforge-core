# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages, explicit workarounds, or softer 'close it anyway' / dependency-override reasoning instead of resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION005

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- Safer target pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

## WFLOW016

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The generated `smoke_test` tool treated a shell-style environment assignment like `UV_CACHE_DIR=...` as the executable name for `spawn()`. That turns a valid explicit override command into an `ENOENT` tool failure and misclassifies the result as a runtime environment problem.
- Safer target pattern: Parse shell-style smoke-test overrides before execution, strip leading `KEY=VALUE` env assignments into the spawn environment, and report malformed overrides as configuration errors rather than environment failures.

## WFLOW017

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The generated `smoke_test` tool fell back to repo-level pytest detection or caller-supplied `test_paths` instead of binding itself to the ticket's canonical smoke acceptance command. That can widen smoke scope to unrelated failures or narrow it away from the actual closeout requirement.
- Safer target pattern: Treat acceptance-backed smoke commands as canonical, let `smoke_test` infer them automatically, and reject heuristic scope changes unless the caller provides an intentional exact command override.

