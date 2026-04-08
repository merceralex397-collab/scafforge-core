# Scafforge Process Failures

## Scope

- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.

## Failure Map

### EXEC001

- linked_report_1_finding: EXEC001
- implicated_surface: generated repo implementation and validation surfaces
- ownership_class: generated repo execution surface
- workflow_failure: One or more Python packages fail to import — the service cannot start.

### REF-003

- linked_report_1_finding: REF-003
- implicated_surface: generated repo reference integrity and configuration surfaces
- ownership_class: generated repo source and configuration surfaces
- workflow_failure: Source imports reference missing local modules.

### SKILL001

- linked_report_1_finding: SKILL001
- implicated_surface: project-skill-bootstrap and agent-prompt-engineering surfaces
- ownership_class: project skill or prompt surface
- workflow_failure: One or more repo-local skills still contain generic placeholder text instead of project-specific guidance.

## Ownership Classification

### EXEC001

- ownership_class: generated repo execution surface
- affected_surface: generated repo implementation and validation surfaces

### REF-003

- ownership_class: generated repo source and configuration surfaces
- affected_surface: generated repo reference integrity and configuration surfaces

### SKILL001

- ownership_class: project skill or prompt surface
- affected_surface: project-skill-bootstrap and agent-prompt-engineering surfaces

## Root Cause Analysis

### EXEC001

- root_cause: Runtime errors (NameError, FastAPIError, missing dependency, broken DI pattern, etc.) that are invisible to static analysis prevent module load. Common causes: TYPE_CHECKING-guarded names used in runtime annotations, FastAPI dependency functions with non-Pydantic parameter types, circular imports.
- safer_target_pattern: Verify every import succeeds: `python -c 'from src.<pkg>.main import app'`. Use string annotations (`-> "TypeName"`) for TYPE_CHECKING-only imports. Use `request: Request` (not `app: FastAPI`) in FastAPI dependency functions.
- how_the_workflow_allowed_it: One or more Python packages fail to import — the service cannot start.

### REF-003

- root_cause: At least one local import or require path no longer resolves to a file in the repo, so the runtime graph is internally inconsistent.
- safer_target_pattern: Audit local relative import paths and fail when the referenced module file is missing.
- how_the_workflow_allowed_it: Source imports reference missing local modules.

### SKILL001

- root_cause: project-skill-bootstrap or later managed-surface repair left baseline local skills in a scaffold placeholder state, so agents lose concrete stack and validation guidance.
- safer_target_pattern: Populate every baseline local skill with concrete repo-specific rules and validation commands; generated `.opencode/skills/` files must not retain template filler.
- how_the_workflow_allowed_it: One or more repo-local skills still contain generic placeholder text instead of project-specific guidance.

