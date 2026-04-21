# Blender-MCP Workflow Reference

Use this reference when synthesizing a repo-local `blender-mcp-workflow` skill for a project that routes asset creation through `blender-agent`.

For current support levels and stop points, pair this workflow note with [`blender-support-matrix.md`](blender-support-matrix.md). This file stays procedural; the matrix owns capability claims.

## Required contract

- Treat mutating Blender-MCP calls as **stateless** unless current repo evidence proves otherwise.
- Every mutating call must provide an `output_blend`.
- After each mutating call, read `persistence.saved_blend` from the response and feed that exact path back as `input_blend` on the next mutating call.
- If a mutating response says the work was ephemeral, omits `output_blend`, or returns no `persistence.saved_blend`, stop and retry that same step correctly before continuing.
- Before claiming a bridge defect, prove one successful chain explicitly: `project_initialize(output_blend=...)` must save a file, the next mutating call must reuse that path as `input_blend`, and `.blender-mcp/audit/*.jsonl` must record non-null `input_blend` / `output_blend` on the corresponding `job_start`.
- Do not claim the bridge is broken just because a call was made with `input_blend: null` or `output_blend: null`. First verify the call honored the stateless chaining contract.

## Default tool sequence

1. `project_initialize(output_blend=...)`
2. `mesh_edit_batch(...)` or `scene_batch_edit(...)` with chained `input_blend` / `output_blend`
3. `material_pbr_build(...)` with chained `input_blend` / `output_blend`
4. `uv_workflow(...)` with chained `input_blend` / `output_blend`
5. `render_preview(...)` with chained `input_blend` / `output_blend`
6. `quality_validate(input_blend=...)`
7. `export_asset(input_blend=...)`

Treat steps 6 and 7 as **partial lanes** in the current adjacent `blender-agent` baseline. They still require repo-local QA and import proof before a generated repo can claim the asset is usable.

## Blocker handling

- If `environment_probe` or config evidence shows inline Python is disabled, treat that as a blocker rather than inventing a Python fallback.
- If `.blender-mcp/audit/*.jsonl` shows a mutating `job_start` with `input_blend: null` or `output_blend: null`, treat that as invocation evidence first. Re-run the step with explicit chained paths before escalating a system-level MCP defect.
- Do not describe `blender_session_*` tools, persistent in-memory sessions, or checkpoint workflows unless the repo actually exposes and documents those tools.
- Tell agents to use the repo's managed `blender_agent` MCP entry from `opencode.jsonc` when it exists instead of inventing a separate launch command.
- Use the repo's seeded asset surfaces (`assets/briefs/`, `assets/models/`, `assets/PROVENANCE.md`, `assets/pipeline.json`) instead of generic imaginary paths.

## Required asset evidence

Before a Blender-derived asset is treated as usable in a generated repo, keep these surfaces aligned:

- `assets/workflows/<asset>.json` with the chained Blender workflow record
- `assets/previews/<asset>.*` render or preview evidence
- `assets/manifest.json` with `source_route`, `source_type`, `workflow_ref`, `tool_chain`, `preview_path`, `import_report_ref`, and `license_report_ref`
- repo-local import QA proving the exported asset survives the target engine path
