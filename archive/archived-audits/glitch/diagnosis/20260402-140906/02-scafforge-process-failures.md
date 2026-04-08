# Scafforge Process Failures

## Scope

- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.

## Failure Map

### REF-003

- linked_report_1_finding: REF-003
- implicated_surface: generated repo reference integrity and configuration surfaces
- ownership_class: generated repo source and configuration surfaces
- workflow_failure: Source imports reference missing local modules.

### SESSION001

- linked_report_1_finding: SESSION001
- implicated_surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- ownership_class: audit and lifecycle diagnosis surface
- workflow_failure: The supplied session transcript shows a later reasoning failure that current-state-only diagnosis would miss.

### SESSION003

- linked_report_1_finding: SESSION003
- implicated_surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- ownership_class: audit and lifecycle diagnosis surface
- workflow_failure: The supplied session transcript shows the agent searching for workflow bypasses or soft dependency overrides instead of following the lifecycle contract.

### WFLOW025

- linked_report_1_finding: WFLOW025
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: Declared Godot Android target lacks canonical backlog ownership for export surfaces and debug APK proof.

### WFLOW026

- linked_report_1_finding: WFLOW026
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: Current artifacts contain explicit markdown verdict labels, but the generated verdict extractor still reports them as unclear.

## Ownership Classification

### SESSION001

- ownership_class: audit and lifecycle diagnosis surface
- affected_surface: scafforge-audit transcript chronology and causal diagnosis surfaces

### SESSION003

- ownership_class: audit and lifecycle diagnosis surface
- affected_surface: scafforge-audit transcript chronology and causal diagnosis surfaces

### REF-003

- ownership_class: generated repo source and configuration surfaces
- affected_surface: generated repo reference integrity and configuration surfaces

### WFLOW025

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### WFLOW026

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

## Root Cause Analysis

### REF-003

- root_cause: At least one local import or require path no longer resolves to a file in the repo, so the runtime graph is internally inconsistent.
- safer_target_pattern: Audit local relative import paths and fail when the referenced module file is missing.
- how_the_workflow_allowed_it: Source imports reference missing local modules.

### SESSION001

- root_cause: The session began from stale resume state, later gathered new implementation or QA evidence, then still published an over-broad blocker summary without a later full-suite execution result.
- safer_target_pattern: When session logs are supplied, audit chronology first: separate stale resume state from later evidence, then explain any final summary that outruns the executed commands before reconciling current repo state.
- how_the_workflow_allowed_it: The supplied session transcript shows a later reasoning failure that current-state-only diagnosis would miss.

### SESSION003

- root_cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages, explicit workarounds, or softer 'close it anyway' / dependency-override reasoning instead of resolving the missing proof or contradictory contract.
- safer_target_pattern: Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.
- how_the_workflow_allowed_it: The supplied session transcript shows the agent searching for workflow bypasses or soft dependency overrides instead of following the lifecycle contract.

### WFLOW025

- root_cause: The repo declares Android delivery in canonical truth, but the backlog never created the dedicated `ANDROID-001` and `RELEASE-001` lanes. That lets presentation or validation tickets absorb Android work without a real export or release-proof path.
- safer_target_pattern: For Godot Android repos, always create `ANDROID-001` in lane `android-export` for repo-local export surfaces and `RELEASE-001` in lane `release-readiness` for debug APK proof. Do not let generic polish tickets stand in for release ownership.
- how_the_workflow_allowed_it: Declared Godot Android target lacks canonical backlog ownership for export surfaces and debug APK proof.

### WFLOW026

- root_cause: The repo-local workflow parser only matches plain `Verdict:` or `Approval Signal:` labels. Markdown-emphasized labels such as `**Verdict**: PASS` then look unparseable, which blocks review or QA transitions even though the artifact body is explicit.
- safer_target_pattern: Keep one shared artifact verdict extractor that accepts plain and markdown-emphasized verdict labels, then route ticket_lookup and ticket_update through that shared parser instead of treating explicit review or QA verdicts as unclear.
- how_the_workflow_allowed_it: Current artifacts contain explicit markdown verdict labels, but the generated verdict extractor still reports them as unclear.

