# Blender Support Matrix

This matrix documents the truthful Scafforge contract for Blender-derived workflows based on the current `blender-agent` repository. It describes what the adjacent repo can currently prove, not what a future Blender lane might support.

## Baseline reality

- The shipped default surface is still the legacy v1 Blender MCP server.
- Certified v1 tools today are `environment_probe`, `project_initialize`, `addon_configure`, `scene_query`, `scene_batch_edit`, `modifier_stack_edit`, `uv_workflow`, `material_pbr_build`, and `render_preview`.
- `mesh_edit_batch`, `export_asset`, and `quality_validate` are currently partial, so Scafforge must not describe them as guaranteed end-to-end proof lanes.
- V2 session tools and wrapper workflows exist, but they remain preview/control-plane surfaces rather than the certified default execution contract.

## Supported lanes

| Lane | Support level | What Scafforge may claim today | Required evidence before the asset is treated as usable |
| --- | --- | --- | --- |
| Hard-surface prop blocking and cleanup | **supported** | Repo-managed Blender work can assemble bounded props, apply transforms/modifiers, and save chained `.blend` state across mutating calls. | `workflow_ref`, `tool_chain`, `preview_path`, render or preview output, and command/audit proof that mutating calls chained non-null `input_blend` and `output_blend`. |
| Basic material/lookdev | **supported** | Material authoring for simple PBR-style surfaces is available through `material_pbr_build`, but the package must still judge readability and finish from preview evidence. | Material workflow record, preview render, and manifest/tool-chain evidence tied to the asset output. |
| UV and export prep | **supported with caution** | UV work is certified; export exists only as a partial tool, so export success must be proven in repo-local workflow and import QA rather than assumed from tool name alone. | UV workflow evidence, preview render, import proof, and asset manifest references. |
| Render preview / visual inspection | **supported** | Blender can emit preview renders suitable for proof surfaces. These are evidence for review, not automatic proof of artistic quality. | Saved render or preview path plus QA notes tied to the rubric. |
| Engine import / optimization QA | **supported through repo QA, not Blender alone** | Blender can contribute source evidence, but final usability still depends on repo-local import and optimization reports. | `import_report_ref`, preview evidence, and repo-local QA showing the exported asset loads cleanly. |
| Hero characters, complex rigs, advanced animation, baked production shading, simulation-heavy content | **unsupported or experimental** | Scafforge must not imply that the current Blender lane can reliably generate production-ready hero content or deep animation/simulation workflows without human intervention. | Route to sourced assets, simpler authored lanes, or explicit human-directed escalation instead of pretending automation is certified. |

## Supported stop points

Scafforge should stop the Blender lane and fall back when:

- the brief requires a hero character, complex rig, facial animation, or broad cinematic lookdev
- the proof surface depends on partial tools such as `quality_validate` or `export_asset` behaving like certified end-to-end guarantees
- the workflow cannot prove saved-blend chaining from the MCP audit log
- preview renders show blocker-level rubric failures even if the mesh technically exported

## Manifest-aligned evidence

For Blender-derived assets, keep the evidence on the canonical asset truth surfaces:

- `assets/manifest.json`
  - `source_route`
  - `source_type`
  - `workflow_ref`
  - `tool_chain`
  - `preview_path`
  - `import_report_ref`
  - `license_report_ref`
- `assets/workflows/`
  - chained Blender workflow record
  - saved-blend or workfile references when retained
- `assets/previews/`
  - render or screenshot evidence used in review
- `assets/qa/import-report.json`
  - engine import and optimization proof

## Truthfulness rules

- Do not document V2 session wrappers as the default shipped production contract.
- Do not describe `quality_validate`, `export_asset`, or broad session/control-plane surfaces as certified when the adjacent repo marks them partial or preview.
- Do not promise that Blender solves style direction by itself. Blender evidence proves a lane executed; the visual rubric still decides whether the output is acceptable.
