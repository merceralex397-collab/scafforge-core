# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## ENV002

- Surface: scafforge-audit and scafforge-repair host verification plus prerequisite-classification surfaces
- Root cause: This repo is uv-managed and the host already provides `uv`, so the missing pytest command is not primarily a host-prerequisite absence. The repo-local test environment was never successfully bootstrapped, or the recorded bootstrap state is stale after workflow changes.
- Safer target pattern: Rerun `environment_bootstrap` to restore the repo-local test environment before audit or repair verification. For uv repos with dev extras, bootstrap should sync with `uv sync --locked --extra dev`, then verify pytest from the repo-local environment.

