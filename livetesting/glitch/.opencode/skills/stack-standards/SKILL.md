---
name: stack-standards
description: Hold the repo-local Godot, GDScript, Android, and validation conventions for Glitch.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

Current stack mode: `godot-android-2d`

## Engine And Language

- Use Godot as the primary runtime and scene system.
- Default to GDScript unless canonical truth later changes the implementation language.
- Prefer small, focused scripts attached to scenes or autoload services with clear responsibilities.
- Keep node names, scene boundaries, and autoload singletons explicit and stable; avoid hidden cross-scene coupling.

## Gameplay Standards

- Movement feel is foundational. Changes to acceleration, jump arcs, wall interaction, dash timing, coyote time, and input buffering require explicit validation notes.
- Glitch mechanics must be telegraphed. If a change affects physics, hazards, or controls, include the warning surface in the implementation plan.
- Prefer hand-authored rooms with constrained glitch pools over fully procedural layout generation.
- Mobile readability outranks ornamental visual noise. Keep collision-critical surfaces visually distinct.

## Validation

- Prefer executable Godot checks over narrative claims.
- When the project files exist, validate with commands in this family:
  - `godot --headless --path . --quit`
  - `godot --headless --path . --import`
  - ticket-specific smoke commands tied to scenes, systems, or test harnesses
- If a ticket changes input, checkpointing, hazards, or glitch behavior, validation should mention the affected scene or test surface explicitly.
- If Godot or Android prerequisites are missing, return a blocker instead of faking validation.

## Process

- Use ticket tools for stage transitions and queue state.
- Artifacts produced by each stage must be registered.
- Smoke tests run through the managed `smoke_test` tool, not via ad hoc summary claims.
- Keep scope vertical-slice-first until the Startup Sector proves the core loop.
