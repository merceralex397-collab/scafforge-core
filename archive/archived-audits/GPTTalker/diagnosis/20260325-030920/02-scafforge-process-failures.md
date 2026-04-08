# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## EXEC001

- Surface: generated repo implementation and validation surfaces
- Root cause: Runtime errors (NameError, FastAPIError, missing dependency, broken DI pattern, etc.) that are invisible to static analysis prevent module load. Common causes: TYPE_CHECKING-guarded names used in runtime annotations, FastAPI dependency functions with non-Pydantic parameter types, circular imports.
- Safer target pattern: Verify every import succeeds: `python -c 'from src.<pkg>.main import app'`. Use string annotations (`-> "TypeName"`) for TYPE_CHECKING-only imports. Use `request: Request` (not `app: FastAPI`) in FastAPI dependency functions.

## EXEC002

- Surface: generated repo implementation and validation surfaces
- Root cause: A test file imports a broken module (e.g. the node agent with a broken DI pattern), preventing the entire test suite from running. This means QA was never actually executed against these tests.
- Safer target pattern: Run `pytest tests/ --collect-only` and fix all collection errors before marking QA done. A QA artifact that claims tests passed when pytest cannot even collect is invalid.

## MODEL001

- Surface: repo-scaffold-factory managed template surfaces
- Root cause: Managed repair or retrofit preserved older model/profile surfaces instead of regenerating the repo-local model profile, agent prompts, and model matrix together.
- Safer target pattern: Regenerate `.opencode/skills/model-operating-profile/SKILL.md`, align provenance/model-matrix/agent frontmatter on the current runtime model choices, and remove deprecated `MiniMax-M2.7` surfaces before implementation continues.

