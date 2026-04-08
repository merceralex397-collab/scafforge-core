# Scafforge Process Failures

## Scope

- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.

## Failure Map

### EXEC-GODOT-004

- linked_report_1_finding: EXEC-GODOT-004
- implicated_surface: generated repo implementation and validation surfaces
- ownership_class: generated repo execution surface
- workflow_failure: Godot headless validation fails.

### EXEC-GODOT-005

- linked_report_1_finding: EXEC-GODOT-005
- implicated_surface: generated repo implementation and validation surfaces
- ownership_class: generated repo execution surface
- workflow_failure: Android-targeted Godot repo still lacks export surfaces or debug APK proof while the repo claims release progress or completion.

### REF-003

- linked_report_1_finding: REF-003
- implicated_surface: generated repo reference integrity and configuration surfaces
- ownership_class: generated repo source and configuration surfaces
- workflow_failure: Source imports reference missing local modules.

### WFLOW025

- linked_report_1_finding: WFLOW025
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: Declared Godot Android target lacks canonical backlog ownership for export surfaces and debug APK proof.

## Ownership Classification

### EXEC-GODOT-004

- ownership_class: generated repo execution surface
- affected_surface: generated repo implementation and validation surfaces

### EXEC-GODOT-005

- ownership_class: generated repo execution surface
- affected_surface: generated repo implementation and validation surfaces

### REF-003

- ownership_class: generated repo source and configuration surfaces
- affected_surface: generated repo reference integrity and configuration surfaces

### WFLOW025

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

## Root Cause Analysis

### EXEC-GODOT-004

- root_cause: The project cannot complete a deterministic headless Godot load pass on the current host, indicating broken project configuration or scripts.
- safer_target_pattern: Run a deterministic `godot --headless --path . --quit` validation during audit and keep the repo blocked until it succeeds or returns an explicit environment blocker instead.
- how_the_workflow_allowed_it: Godot headless validation fails.

### EXEC-GODOT-005

- root_cause: The repo treats Android delivery as complete enough to close or advance release-facing work, but the canonical export preset, repo-local Android support surfaces, or debug APK artifact proof are still missing.
- safer_target_pattern: Keep Godot Android repos blocked on explicit export surfaces plus debug APK proof. Once release work starts or the repo claims completion, require `export_presets.cfg`, non-placeholder `android/` support surfaces, and a debug APK at the canonical build path.
- how_the_workflow_allowed_it: Android-targeted Godot repo still lacks export surfaces or debug APK proof while the repo claims release progress or completion.

### REF-003

- root_cause: At least one local import or require path no longer resolves to a file in the repo, so the runtime graph is internally inconsistent.
- safer_target_pattern: Audit local relative import paths and fail when the referenced module file is missing.
- how_the_workflow_allowed_it: Source imports reference missing local modules.

### WFLOW025

- root_cause: The repo declares Android delivery in canonical truth, but the backlog never created the dedicated `ANDROID-001` and `RELEASE-001` lanes. That lets presentation or validation tickets absorb Android work without a real export or release-proof path.
- safer_target_pattern: For Godot Android repos, always create `ANDROID-001` in lane `android-export` for repo-local export surfaces and `RELEASE-001` in lane `release-readiness` for debug APK proof. Do not let generic polish tickets stand in for release ownership.
- how_the_workflow_allowed_it: Declared Godot Android target lacks canonical backlog ownership for export surfaces and debug APK proof.

