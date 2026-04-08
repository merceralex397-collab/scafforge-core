# Scafforge Process Failures

## Scope

- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.

## Failure Map

### REF-003

- linked_report_1_finding: REF-003
- implicated_surface: generated repo reference integrity and configuration surfaces
- ownership_class: generated repo source and configuration surfaces
- workflow_failure: Source imports reference missing local modules.

## Ownership Classification

### REF-003

- ownership_class: generated repo source and configuration surfaces
- affected_surface: generated repo reference integrity and configuration surfaces

## Root Cause Analysis

### REF-003

- root_cause: At least one local import or require path no longer resolves to a file in the repo, so the runtime graph is internally inconsistent.
- safer_target_pattern: Audit local relative import paths and fail when the referenced module file is missing.
- how_the_workflow_allowed_it: Source imports reference missing local modules.

