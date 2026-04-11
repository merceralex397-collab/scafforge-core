---
name: asset-description
description: Guide an agent through writing a precise, actionable asset description brief that can be executed by a Blender-MCP subagent or used to source matching free assets. Use when a game project needs a specific visual asset defined before creation.
---

# Asset Description Skill

Use this skill to produce a structured asset brief that is actionable by either:
- A Blender-MCP subagent (route C) — the brief becomes tool call parameters
- A human or agent sourcing free assets (route B) — the brief becomes search criteria

## Brief Format

Create one file per asset in `assets/briefs/<asset-name>.md`:

```markdown
# Asset Brief: <Name>

## Identity
- **Name**: horse-enemy-base
- **Category**: character
- **Art Style**: low-poly stylized
- **Target Engine**: Godot 4.x
- **Export Format**: .glb (GLTF Binary)

## Visual Description
<2-4 sentences describing exactly what this looks like. Be specific about
proportions, colors, distinctive features. Avoid subjective terms like
"cool" or "nice". Use measurable terms.>

## Technical Constraints
- **Triangle budget**: 2000-5000 tris
- **Texture size**: 512x512 max
- **Material slots**: 1-2 (body, accent)
- **UV mapping**: Auto-unwrap acceptable
- **Rigging**: None (static prop) / Basic (animated)
- **Animation**: None / Idle loop / Walk cycle
- **Scale reference**: 2m tall in Godot units

## Color Palette
- Primary: #8B4513 (brown body)
- Secondary: #2F2F2F (dark mane/tail)
- Accent: #FF4444 (glowing eyes, if enemy variant)

## Blender-MCP Tool Sequence (Route C only)
1. project_initialize — new file, metric units, `output_blend=tmp/<asset>-01.blend`
2. mesh_edit_batch — create body from cube, extrude legs/neck/head, `input_blend=<saved>`, `output_blend=tmp/<asset>-02.blend`
3. mesh_edit_batch — loop cuts for joints, edge flow cleanup, `input_blend=<saved>`, `output_blend=tmp/<asset>-03.blend`
4. material_pbr_build — base color from palette, roughness 0.7, `input_blend=<saved>`, `output_blend=tmp/<asset>-04.blend`
5. uv_workflow — smart UV project, pack islands, `input_blend=<saved>`, `output_blend=tmp/<asset>-05.blend`
6. render_preview — front + side orthographic from the latest saved blend
7. quality_validate — check tri count, manifold, scale against the latest saved blend
8. export_asset — .glb, apply modifiers, Godot preset, from the latest saved blend

Critical rule: every mutating Blender-MCP call is stateless. Never continue after a mutating call unless it returned `persistence.saved_blend`, and never send `input_blend: null` or `output_blend: null` on a mutating call.

## Acceptance Criteria
- [ ] Triangle count within budget
- [ ] No inverted normals
- [ ] Manifold mesh (watertight)
- [ ] UV islands non-overlapping
- [ ] Correct scale (matches reference)
- [ ] Preview renders reviewed
- [ ] Imports cleanly into Godot (no errors in Output panel)
- [ ] PROVENANCE.md entry created
```

## Procedure

### 1. Gather Requirements
Read the canonical brief and `assets/pipeline.json` to understand:
- Overall art style
- Platform constraints (mobile = lower budgets)
- Which route this asset will use

### 2. Write the Brief
Follow the format above. Key principles:
- **Be specific**: "A brown horse standing on four legs" not "a horse"
- **Be measurable**: Triangle counts, texture sizes, material counts
- **Be actionable**: The Blender-MCP sequence should be executable as-is
- **Match the style**: Low-poly characters don't need 4K textures

### 3. Validate the Brief
Before creation begins:
- Check triangle budget is reasonable for target platform
- Check texture size is appropriate
- Check export format matches engine import capabilities
- Check color palette has enough contrast for gameplay readability

### 4. Route to Creation
- If Route C (Blender-MCP): Hand brief to blender-asset-creator subagent
- If Route B (free/open): Use brief as search criteria on asset sources
- If Route D (Godot built-in): Use brief as reference for CSG/particle/shader work

## Output
- `assets/briefs/<asset-name>.md` — One complete asset brief per asset needed
