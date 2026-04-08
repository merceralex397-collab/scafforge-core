# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## BOOT001

- Surface: repo-scaffold-factory managed template surfaces
- Root cause: The managed `environment_bootstrap` surface still relies on bare `python3 -m pip` or otherwise ignores repo-local uv/.venv signals. When global pip is absent, bootstrap fails even if the repo has a usable project virtual environment or uv lockfile.
- Safer target pattern: Prefer repo-native bootstrap (`uv sync --locked` for uv repos; otherwise repo-local `.venv` plus `.venv/bin/python -m pip`), record missing prerequisites accurately, and keep bootstrap readiness separate from source import/test failures.

## EXEC001

- Surface: generated repo implementation and validation surfaces
- Root cause: Runtime errors (NameError, FastAPIError, missing dependency, broken DI pattern, etc.) that are invisible to static analysis prevent module load. Common causes: TYPE_CHECKING-guarded names used in runtime annotations, FastAPI dependency functions with non-Pydantic parameter types, circular imports.
- Safer target pattern: Verify every import succeeds: `python -c 'from src.<pkg>.main import app'`. Use string annotations (`-> "TypeName"`) for TYPE_CHECKING-only imports. Use `request: Request` (not `app: FastAPI`) in FastAPI dependency functions.

## EXEC002

- Surface: generated repo implementation and validation surfaces
- Root cause: A test file imports a broken module (e.g. the node agent with a broken DI pattern), preventing the entire test suite from running. This means QA was never actually executed against these tests.
- Safer target pattern: Run `pytest tests/ --collect-only` and fix all collection errors before marking QA done. A QA artifact that claims tests passed when pytest cannot even collect is invalid.

## SKILL001

- Surface: project-skill-bootstrap and agent-prompt-engineering surfaces
- Root cause: project-skill-bootstrap or later managed-surface repair left baseline local skills in a scaffold placeholder state, so agents lose concrete stack and validation guidance.
- Safer target pattern: Populate every baseline local skill with concrete repo-specific rules and validation commands; generated `.opencode/skills/` files must not retain template filler.

