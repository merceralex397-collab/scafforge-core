---
name: asset-pipeline
description: Design and configure the asset sourcing, generation, provenance, compliance, optimization, and import pipeline for game projects. Use after repo-scaffold-factory when a generated repo needs machine-checkable asset truth.
---

# Asset Pipeline

Use this skill to configure the asset operating framework for a game project.

## When to Use

- The project is a game or asset-heavy interactive repo.
- The canonical brief describes art, audio, UI, or content acquisition needs.
- The repo needs deterministic asset truth, provenance, compliance, optimization, and import QA.
- The repo may use curated sourcing, procedural generation, local/open AI, or Blender/DCC cleanup.

## Core contract

Scafforge now treats asset work as **source routes plus pipeline stages**, not as one flat route-family list.

Default policy order:

1. deterministic or procedural repo-authored routes first
2. curated open sources second
3. mixed-license sources only with explicit attribution and commercial-policy review
4. local/open AI generation only when deterministic and curated routes leave a real gap
5. DCC cleanup or assembly where the asset class needs it

Hosted commercial generation APIs remain denied by default in this package contract.

## Capability taxonomy

### Source routes

| Capability | What it owns | Typical inputs | Required proof |
| --- | --- | --- | --- |
| `source-open-curated` | Curated open sources with straightforward licenses | Kenney, Quaternius, Poly Haven, ambientCG, Google Fonts | manifest source URL, license, author/origin, license-report allowlist pass |
| `source-mixed-license` | Sources that need per-asset attribution or commercial review | OpenGameArt, Freesound, itch.io free assets, Game-icons | attribution-required manifest entry, attribution ledger, license review result |
| `procedural-2d` | Repo-authored 2D/UI/VFX/procedural audio content | shaders, particles, themes, icon composition, sprite cleanup, AudioStreamGenerator | workflow record, import proof, preview when needed |
| `procedural-layout` | Deterministic layout or tile assembly | TileMap, TileSet, WFC, room-layout generators | workflow record, preview/contact sheet, import proof |
| `procedural-world` | Noise-driven terrain or world generation | FastNoiseLite, Terrain3D, voxel/world generators | workflow record, optimization status, import proof |
| `local-ai-2d` | Local/open image generation and refinement | ComfyUI, InvokeAI, AUTOMATIC1111, Diffusers wrappers | tool chain, model/checkpoint, prompt/recipe, workflow record, preview, license pass |
| `local-ai-audio` | Local/open audio generation | open-weight local audio models | tool chain, model/checkpoint, prompt/recipe, license pass |
| `reconstruct-3d` | 3D reconstruction bootstrap lanes | image-to-3D or similar local reconstruction stacks | workflow record, preview, cleanup and import proof |
| `dcc-assembly` | Blender/DCC assembly, cleanup, UV, material, and export | Blender, Geometry Nodes, Material Maker-informed cleanup | workflow record, preview, optimization stage, import proof |

### Pipeline stages

- `optimize-import`
- `provenance-compliance`

These stages are not alternate source routes. Every asset category should record its selected source route separately from these required proof stages.

## Visual quality contract

Asset presence is not enough. For visually reviewable repos, the generated output must also satisfy the named visual rubric in [`references/visual-quality-rubric.md`](references/visual-quality-rubric.md).

Key rules:

- judge **screen fit, readability, hierarchy, silhouette, material readability, and motion feedback**
- treat blocker findings as proof that the asset or surface is not ready, even when the file technically exists
- keep style choice separate from failure: stylized, flat, low-poly, or minimalist output is acceptable when it is intentional and readable
- require screenshot or render evidence for reviewable surfaces instead of trusting prose like "looks good now"

## Canonical generated-repo surfaces

Generated repos should converge on:

- `assets/requirements.json`
- `assets/pipeline.json`
- `assets/manifest.json`
- `assets/ATTRIBUTION.md`
- `assets/PROVENANCE.md`
- `assets/workflows/`
- `assets/previews/`
- `assets/qa/import-report.json`
- `assets/qa/license-report.json`
- `.opencode/meta/asset-provenance-lock.json`

### Truth ownership

| Surface | Authority |
| --- | --- |
| `assets/requirements.json` | requested asset intent, category needs, quality bar, and preferred routes |
| `assets/pipeline.json` | category-level route selection, fallback order, capability policy, and stage configuration |
| `assets/manifest.json` | authoritative per-asset provenance, compliance, workflow, and import truth |
| `.opencode/meta/asset-provenance-lock.json` | authoritative pipeline-contract revision and digest truth |
| `assets/ATTRIBUTION.md` | derived human attribution summary |
| `assets/PROVENANCE.md` | derived human provenance ledger |
| `assets/qa/import-report.json` | latest import and optimization verification report |
| `assets/qa/license-report.json` | latest license and compliance verification report |

If these surfaces disagree, `assets/manifest.json` wins on per-asset truth and `.opencode/meta/asset-provenance-lock.json` wins on process-contract truth.

## Research distillation defaults

This skill treats the cited research as route policy, not as passive bibliography.

| Capability | Default guidance | Non-default exception |
| --- | --- | --- |
| `source-open-curated` | Prefer Kenney, Quaternius, Poly Haven, ambientCG, and Google Fonts as the lowest-friction open defaults. | Move to `source-mixed-license` when attribution or per-asset commercial review is required. |
| `source-mixed-license` | Use OpenGameArt, Freesound, itch.io free assets, and similar sources only with explicit manifest fields and attribution coverage. | Deny by default when the license is unknown, non-commercial, no-derivatives, or otherwise unsupported. |
| `procedural-2d` | Prefer Godot shaders, particles, theme resources, SVG/icon composition, and lightweight 2D tooling. | Do not escalate to AI for routine UI chrome or simple iconography before deterministic composition is exhausted. |
| `procedural-layout` | Prefer TileMap or WFC-style layout generation for repeatable rooms, chunks, and tile-driven content. | Stop and ask for human direction when authored encounter quality and procedural coverage still conflict. |
| `procedural-world` | Prefer noise-driven terrain, chunk generation, and bounded world-building systems. | Do not imply autonomous AAA-world generation. |
| `local-ai-2d` | Treat ComfyUI, InvokeAI, AUTOMATIC1111, and Diffusers wrappers as implementation options, not hard-coded package dependencies. | Hosted commercial image APIs remain denied by default in this baseline. |
| `local-ai-audio` | Use only local/open tooling plus open-weight models by default, and only after procedural or sourced audio routes leave a genuine gap. | Commercial or non-commercially restricted audio models remain denied by default. |
| `reconstruct-3d` | Treat image-to-3D or similar reconstruction as a bootstrap lane that still needs cleanup and QA. | Do not present raw reconstruction output as final truth without cleanup, optimization, and import proof. |
| `dcc-assembly` | Use Blender-driven assembly, cleanup, UV, material, and export flows for 3D content that needs it. | Blender-MCP is an execution surface, not a semantic guarantee of final asset quality. |

## Old-to-new migration rules

- `third-party-open-licensed` maps to `source-open-curated` by default and to `source-mixed-license` when the selected source needs attribution or commercial review.
- `procedural-repo-authored` maps to `procedural-2d`, `procedural-layout`, or `procedural-world` depending on the asset class.
- `godot-native-authored` maps to the same procedural split above; engine-specific wording is no longer the canonical route label.
- `blender-mcp-generated` maps to `dcc-assembly` by default and may map to `reconstruct-3d` when reconstruction is the real operating mode.

## Procedure

### 1. Seed the deterministic asset scaffold first

Run:

```sh
python3 skills/asset-pipeline/scripts/init_asset_pipeline.py <repo-root>
```

That initializer reads `.opencode/meta/bootstrap-provenance.json` when present, then seeds:

- `assets/requirements.json`
- `assets/pipeline.json`
- `assets/manifest.json`
- `assets/ATTRIBUTION.md`
- `assets/PROVENANCE.md`
- `assets/workflows/`
- `assets/previews/`
- `assets/qa/import-report.json`
- `assets/qa/license-report.json`
- `.opencode/meta/asset-pipeline-bootstrap.json`
- `.opencode/meta/asset-provenance-lock.json`

`assets/import-reports/` is deprecated. Use `assets/qa/import-report.json`.

### 2. Classify asset requirements

Read the canonical brief and align it to `assets/requirements.json`:

- asset categories and expected outputs
- quality bar and import constraints
- route preferences and fallback routes
- license policy
- whether tool-license and model-license policy must be tracked separately

### 3. Select source routes per category

Update `assets/pipeline.json` rather than inventing new files.

Rules:

- keep one explicit `primary` source route per category
- keep fallback routes ordered
- keep `optimize-import` and `provenance-compliance` as separate required stages
- prefer deterministic and curated routes before local AI or DCC escalation

### 4. Record machine truth in the manifest

Every committed asset belongs in `assets/manifest.json`.

Minimum manifest truth per asset:

- asset path and category
- selected source route and source type
- QA status
- license and author/origin
- workflow reference
- import report reference
- license report reference
- attribution requirement

Generated assets must also record tool chain, workflow, and model or prompt provenance when applicable.

For visually reviewable outputs, QA should also leave visual-proof evidence that maps the current surface back to the rubric. Use screenshot, render, or short capture artifacts rather than free-form taste claims.

### 5. Keep workflows, previews, and QA structured

- Store repeatable workflow definitions or run records in `assets/workflows/`.
- Store previews or contact-sheet-style evidence in `assets/previews/` when the asset is not trivially inspectable.
- Record optimization and import status in `assets/qa/import-report.json`.
- Record allowlist, denylist, attribution, and source-policy outcomes in `assets/qa/license-report.json`.
- For visually reviewable repos, store the review screenshots or renders that support the QA artifact's visual-proof block under `assets/previews/` or another repo-local path named by the brief.

### 6. Configure Blender-MCP only when `dcc-assembly` is active

Treat `.opencode/meta/asset-pipeline-bootstrap.json` as the machine-readable handoff for `project-skill-bootstrap` and `opencode-team-bootstrap`.

When `dcc-assembly` is selected:

- `required_agents` includes `blender-asset-creator`
- `required_skills` includes `asset-description` and `blender-mcp-workflow`
- `required_mcp_servers` includes `blender_agent`

When `dcc-assembly` is **not** selected, keep `blender_agent` disabled even if Blender exists on the host.

### Blender evidence rules

Blender is a bounded execution lane, not a magic quality button. Follow the truthful support matrix in [`../project-skill-bootstrap/references/blender-support-matrix.md`](../project-skill-bootstrap/references/blender-support-matrix.md).

For Blender-derived assets:

- require `workflow_ref`, `tool_chain`, and `preview_path` in the manifest entry
- keep render or preview evidence that shows silhouette, material read, and finish at review distance
- keep repo-local import proof as the final usability gate; a Blender render alone does not prove the asset is engine-ready
- stop and fall back when the brief asks for hero-character complexity, deep rigging, or other unsupported lanes

## Fallback ladders

Use these defaults unless the canonical brief says otherwise:

1. **Fonts:** curated open families first; mixed-license only with explicit review; stop and ask before inventing a custom brand font route.
2. **Icons and UI symbols:** procedural/vector composition first, curated open second, mixed-license third, local AI only after the deterministic routes leave a real gap.
3. **UI kits:** procedural/theme composition first, curated open second, local AI only for bespoke art direction gaps.
4. **Sprites and tiles:** curated open plus deterministic layout first, mixed-license next, local AI only for gap-filling or style-match cleanup.
5. **VFX:** Godot-native procedural routes first, sourced flipbooks second, local AI only when the native route is inadequate.
6. **SFX:** procedural SFX first, sourced audio second, local AI only under explicit open-weight policy.
7. **Props:** curated open low-poly content first, DCC assembly second, reconstruction only as a bootstrap lane.
8. **Terrain:** procedural-world first, curated materials second, DCC only for bounded landmarks.
9. **Environments:** procedural layout/world generation first, curated open packs second, DCC cleanup only where the brief truly needs it.
10. **Characters:** curated bases first, DCC assembly second, reconstruction only as a bootstrap aid; stop and ask for hero-character ambiguity instead of hallucinating.

## Outputs

- canonical asset requirements, pipeline, manifest, attribution, provenance, QA, and lock surfaces
- route-aware bootstrap metadata for later team or skill generation
- category-level fallback policy
- machine-readable provenance and compliance rules
- structured workflow and preview surfaces

## Validation

- run `python3 skills/asset-pipeline/scripts/validate_provenance.py <repo-root>`
- ensure `assets/manifest.json` carries every committed asset file outside the support directories
- ensure denied or unsupported licenses fail cleanly
- ensure `assets/qa/import-report.json` and `assets/qa/license-report.json` exist and stay current
- ensure the manifest and lock agree on digests
- ensure `assets/ATTRIBUTION.md` and `assets/PROVENANCE.md` reflect the manifest instead of competing with it
- when the repo claims visually reviewable output, ensure QA artifacts cite structured visual-proof evidence rather than relying on taste language alone
