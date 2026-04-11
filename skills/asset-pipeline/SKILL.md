---
name: asset-pipeline
description: Design and configure the asset acquisition, generation, and import pipeline for game projects. Covers free/open asset sourcing, Blender-MCP generation, Godot import validation, and provenance tracking. Use after repo-scaffold-factory when the project type is a game with asset requirements.
---

# Asset Pipeline

Use this skill to configure the asset acquisition and generation pipeline for a game project.

## When to Use

- The project is a game (Godot, Unity, or similar) that requires visual/audio assets
- The canonical brief specifies asset sources (free/open, AI-generated, Blender-MCP, manual)
- The project needs provenance tracking for asset licensing
- The project uses blender-agent MCP for 3D asset generation

## Pipeline Routes

There are four supported asset acquisition routes. A project may use one or more:

### Route A: Codex-Derived Ideas
Adapt game design patterns from the Codex game-studio plugin material. This route focuses on
gameplay mechanics, UI patterns, and architectural decisions rather than raw assets. Assets
are simple/procedural (colored shapes, programmatic sprites, basic particles).

**Best for**: Prototypes, mechanic-focused games, jam-style projects.

**Assets produced**: GDScript procedural generation, simple `.tres` resources, placeholder sprites.

### Route B: Free/Open Source Assets
Source assets from curated open repositories with compatible licenses.

**Verified sources (prioritized)**:
1. **Kenney.nl** — CC0 game assets (sprites, 3D models, audio, UI). Godot-ready.
2. **OpenGameArt.org** — CC0/CC-BY/CC-BY-SA game assets. Verify license per asset.
3. **itch.io free assets** — Mixed licenses. Verify per asset.
4. **Quaternius** — CC0 low-poly 3D models. `.glb` format, Godot-importable.
5. **Freesound.org** — CC0/CC-BY audio. OGG preferred for Godot.
6. **Google Fonts** — OFL fonts for UI text.

**Provenance requirements**:
- Every sourced asset MUST have an entry in `assets/PROVENANCE.md`
- Entry format: `| asset_path | source_url | license | author | date_acquired |`
- CC-BY assets require attribution in the game credits scene

### Route C: Blender-MCP Generation
Use the blender-agent MCP server to generate 3D assets via AI-orchestrated Blender operations.

**Prerequisites**:
- blender-agent MCP server running (stdio or HTTP transport)
- Blender 4.x installed and accessible
- Asset description brief prepared (see asset-description skill)

**Pipeline**:
1. Agent reads asset brief from `assets/briefs/<asset-name>.md`
2. Agent calls blender-agent tools in sequence.
   - **Critical persistence contract**: Blender mutating calls are stateless. Every mutating call must provide `output_blend`, must inspect the returned `persistence.saved_blend`, and must pass that exact saved path back as `input_blend` on the next mutating call.
   - Never pass `input_blend: null` or `output_blend: null` on a mutating call.
   - If a response says the work was ephemeral, `output_blend` was omitted, or `persistence.saved_blend` is missing, stop and retry that step correctly before continuing.
   - Recommended chain:
     - `project_initialize(output_blend=tmp/<asset>-01.blend)` → set up Blender project
     - `mesh_edit_batch(input_blend=<saved>, output_blend=tmp/<asset>-02.blend)` or `scene_batch_edit(...)` → create geometry
     - `material_pbr_build(input_blend=<saved>, output_blend=tmp/<asset>-03.blend)` → apply materials
     - `uv_workflow(input_blend=<saved>, output_blend=tmp/<asset>-04.blend)` → UV unwrap
     - `render_preview(input_blend=<saved>, output_blend=tmp/<asset>-05.blend)` → generate preview for QA
     - `quality_validate(input_blend=<saved>)` → validate the persisted asset state
     - `export_asset(input_blend=<saved>)` → export as `.glb` for Godot
3. Exported `.glb` placed in `assets/models/`
4. Agent runs `quality_validate` for mesh quality checks
5. Godot re-import validation: `godot4 --headless --path . --quit` (checks import)

**Limitations**:
- blender-agent provides execution, NOT generation. The AI agent must know what to build.
- Complex organic models require skilled prompt engineering via asset-description skill.
- Best for: hard-surface models, simple props, architectural elements, basic characters.

### Route D: Godot Built-in Tools
Use Godot's native capabilities for asset creation.

**Capabilities**:
- CSG nodes for prototyping 3D geometry
- Particle systems (GPUParticles2D/3D)
- Shader-based procedural textures
- AnimationPlayer for sprite animations
- TileMap/TileSet for 2D level design
- Theme resources for UI styling

**Best for**: Particle effects, procedural backgrounds, UI themes, tilemaps.

## Procedure

### 1. Seed the deterministic asset scaffold first

Before writing custom docs or tickets, run the initializer so the repo already contains the canonical asset surfaces:

```sh
python3 skills/asset-pipeline/scripts/init_asset_pipeline.py <repo-root>
```

That script reads `.opencode/meta/bootstrap-provenance.json` when present, then seeds:
- `assets/pipeline.json`
- `assets/PROVENANCE.md`
- `assets/briefs/`, `assets/models/`, `assets/sprites/`, `assets/audio/`, `assets/fonts/`, `assets/themes/`
- `.opencode/meta/asset-pipeline-bootstrap.json`

Treat `.opencode/meta/asset-pipeline-bootstrap.json` as the machine-readable handoff for `project-skill-bootstrap` and `opencode-team-bootstrap`.

### 2. Classify Asset Requirements

Read the canonical brief and extract:
- Art style (pixel, low-poly, stylized, realistic)
- Required asset categories (characters, environments, props, UI, audio, VFX)
- Target platform constraints (mobile = smaller textures, fewer polygons)
- License requirements (commercial? attribution-ok? copyleft-ok?)

### 3. Select Routes Per Asset Category

Map each asset category to the best route:

```
characters:
  primary: route_b (Kenney/OpenGameArt) or route_c (Blender-MCP)
  fallback: route_d (CSG prototypes)
environments:
  primary: route_d (Godot tilemaps/CSG) or route_b
  fallback: route_a (procedural)
props:
  primary: route_b or route_c
  fallback: route_d (CSG)
ui:
  primary: route_d (Godot Theme) or route_b (Kenney UI pack)
  fallback: route_a (programmatic)
audio:
  primary: route_b (Freesound)
  fallback: none (silence is acceptable for prototypes)
vfx:
  primary: route_d (Godot particles/shaders)
  fallback: route_a (procedural)
```

### 4. Refine the seeded asset pipeline configuration

Update the seeded `assets/pipeline.json` instead of inventing a new layout:
```json
{
  "art_style": "low-poly",
  "target_platform": "android",
  "routes": {
    "characters": { "primary": "blender-mcp", "fallback": "free-open" },
    "environments": { "primary": "godot-builtin", "fallback": "free-open" },
    "props": { "primary": "free-open", "fallback": "godot-builtin" },
    "ui": { "primary": "godot-builtin" },
    "audio": { "primary": "free-open" },
    "vfx": { "primary": "godot-builtin" }
  },
  "provenance_tracking": true,
  "license_filter": ["CC0", "CC-BY", "MIT", "OFL"],
  "texture_max_size": 1024,
  "model_max_tris": 5000
}
```

### 5. Generate Tickets for Asset Work

For each asset category with `primary: "blender-mcp"`:
- Create an asset brief in `assets/briefs/`
- Create a ticket for the Blender-MCP generation pipeline

For each asset category with `primary: "free-open"`:
- Create a ticket for asset sourcing and import
- Include license verification in acceptance criteria

For all assets:
- Create a ticket for Godot import validation
- Create a ticket for provenance audit

### 6. Configure Blender-MCP Subagent (if Route C used)

Add to the team's agent configuration:
- A dedicated `blender-asset-creator` subagent
- Scoped to blender-agent MCP tools only
- Uses the asset-description skill for brief interpretation
- Has access to `assets/briefs/` for input and `assets/models/` for output
- Mirror that choice into `.opencode/meta/asset-pipeline-bootstrap.json` if you refine the route map after initialization.

## Outputs

- `assets/pipeline.json` — Pipeline configuration
- `assets/PROVENANCE.md` — Asset provenance tracking (initialized)
- `assets/briefs/*.md` — Asset description documents (if route C)
- Asset directory structure created
- `.opencode/meta/asset-pipeline-bootstrap.json` — machine-readable route + agent/skill hints for later bootstrap stages
- Tickets created for asset acquisition work
- Blender-MCP subagent configured (if route C)

## Validation

- `pipeline.json` is valid JSON with all required fields
- Asset directories exist
- PROVENANCE.md template is valid
- If route C: blender-agent MCP server is reachable
- All generated tickets have acceptance criteria that include asset import verification
