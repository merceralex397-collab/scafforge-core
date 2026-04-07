# Scafforge Process Failures

## Scope

- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.

## Failure Map

### SESSION005

- linked_report_1_finding: SESSION005
- implicated_surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- ownership_class: audit and lifecycle diagnosis surface
- workflow_failure: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool.

## Ownership Classification

### SESSION005

- ownership_class: audit and lifecycle diagnosis surface
- affected_surface: scafforge-audit transcript chronology and causal diagnosis surfaces

## Root Cause Analysis

### SESSION005

- root_cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- safer_target_pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.
- how_the_workflow_allowed_it: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool.

