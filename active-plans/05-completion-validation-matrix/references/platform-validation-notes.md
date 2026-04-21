# Platform Validation Notes

## Current Inputs

- `../../_source-material/validation/completionqualityvalidation/toolstoimplement.md`
- `../../_source-material/validation/completionqualityvalidation/test-android-apps/`

## Recommended Platform Families

- web apps
- Godot and browser games
- CLI tools and scripts
- backend services and APIs
- desktop apps on Windows/Linux
- Android apps

No iOS work is in scope for this cycle.

## Tooling Themes To Carry Forward

- process launch and health checks
- UI automation where appropriate
- screenshot and log capture
- network and API verification
- artifact summarization for audit and handoff

## Candidate Tool Bundles To Evaluate During Implementation

- web: Playwright, browser screenshots, network assertions
- Godot/game: headless project validation, scene/import checks, screenshot capture, controller/input sanity checks
- services: process supervision, HTTP health checks, contract tests, structured log capture
- CLI/scripts: fixture inputs, exit-code assertions, stdout/stderr capture
- desktop: launch checks, window detection, screenshot capture, crash-log capture
- Android: ADB, logcat, emulator automation, UI-tree capture

## Important Principle

Validation should be layered. Cheap proof comes first, but visual or runtime proof becomes mandatory once the repo type requires it.

## Planning Consequence

This plan should define the proof ladder before the autonomous loop is allowed to trust PR review or self-declared completion.
