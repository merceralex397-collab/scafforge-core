---
name: android-build-and-test
description: Keep Android-facing build, input, and validation work explicit for the Glitch vertical slice.
---

# Android Build And Test

Before using this skill, call `skill_ping` with `skill_id: "android-build-and-test"` and `scope: "project"`.

Use this skill when a ticket touches:

- Android export setup
- touch controls
- HUD layout on small screens
- device-facing performance or readability concerns

Rules:

- prefer validation that can run locally in headless or editor-friendly form before relying on device-only checks
- record missing Android SDK, export template, or signing prerequisites as blockers
- treat touch target clarity and screen readability as correctness concerns, not optional polish
