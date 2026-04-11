# Blender-MCP Workflow Reference

Use this reference when synthesizing a repo-local `blender-mcp-workflow` skill for a project that routes asset creation through `blender-agent`.

## Required contract

- Treat mutating Blender-MCP calls as **stateless** unless current repo evidence proves otherwise.
- Every mutating call must provide an `output_blend`.
- After each mutating call, read `persistence.saved_blend` from the response and feed that exact path back as `input_blend` on the next mutating call.
- If a mutating response says the work was ephemeral, omits `output_blend`, or returns no `persistence.saved_blend`, stop and retry that same step correctly before continuing.
- Do not claim the bridge is broken just because a call was made with `input_blend: null` or `output_blend: null`. First verify the call honored the stateless chaining contract.

## Default tool sequence

1. `project_initialize(output_blend=...)`
2. `mesh_edit_batch(...)` or `scene_batch_edit(...)` with chained `input_blend` / `output_blend`
3. `material_pbr_build(...)` with chained `input_blend` / `output_blend`
4. `uv_workflow(...)` with chained `input_blend` / `output_blend`
5. `render_preview(...)` with chained `input_blend` / `output_blend`
6. `quality_validate(input_blend=...)`
7. `export_asset(input_blend=...)`

## Blocker handling

- If `environment_probe` or config evidence shows inline Python is disabled, treat that as a blocker rather than inventing a Python fallback.
- Do not describe `blender_session_*` tools, persistent in-memory sessions, or checkpoint workflows unless the repo actually exposes and documents those tools.
- Use the repo's seeded asset surfaces (`assets/briefs/`, `assets/models/`, `assets/PROVENANCE.md`, `assets/pipeline.json`) instead of generic imaginary paths.
