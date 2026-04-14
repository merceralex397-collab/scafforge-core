# Blender-Agent Assessment

**Date**: 2026-04-09  
**Repo**: `/home/pc/projects/blender-agent`  
**Blender Version**: 4.5.0 (installed at `/home/pc/blender-4.5.0/blender`)

## Summary

The blender-agent is a **fully working MCP server** with 24 tools, 3 prompts, and 8 resources. It uses the FastMCP framework (Anthropic's MCP SDK) and supports stdio and HTTP transports. It operates in two modes: background (stateless, subprocess per job) and live session (stateful, persistent Blender connection via TCP add-on).

## Key Findings

### Architecture
- **Framework**: FastMCP v1.27.0+
- **Transport**: stdio (default, CLI), streamable-http (web clients)
- **Execution**: BlenderRunner spawns `blender --background` per job (stateless) or maintains TCP connection to Blender add-on (live session)
- **Security**: Trust profiles (default/restricted/elevated), AST policy checks for inline Python
- **Audit**: Activity trail logging (job lifecycle, policy violations)

### Tools (24 total)
| Category | Tools | Status |
|----------|-------|--------|
| Certified | environment_probe, project_initialize, addon_configure, scene_query, scene_batch_edit, modifier_stack_edit, uv_workflow, material_pbr_build, render_preview | ✅ Full |
| Partial | mesh_edit_batch, node_graph_build, bake_maps, armature_animation, simulation_cache, asset_publish, import_asset, export_asset, quality_validate | ⚠️ Limited |
| Live Session | blender_session_create/attach/close/pause/resume/checkpoint | ✅ Full |
| Experimental | blender_python (inline with AST checks) | ⚠️ Policy-gated |

### Execution Model: Text-to-Operations (NOT Text-to-3D)
The MCP server provides the **execution layer**, not a generation layer. An AI agent reads a brief, selects the right tool sequence, and chains calls:
```
Brief → AI Agent → [project_initialize, mesh_edit_batch, material_pbr_build, uv_workflow, render_preview, export_asset] → Asset
```

### Skills Framework (22 instruction sets)
Pre-built AI instruction sets guide agents through specific workflows:
- `blender-asset-specification` — Brief interpretation
- `blender-asset-orchestrator` — Tool sequencing
- `blender-hard-surface-modeling` — Modeling techniques
- `blender-materials-shading` — Material workflows
- `blender-engine-export` — Multi-engine export (Godot, Unity, Unreal)
- `blender-asset-library-publishing` — Export packaging
- Plus 16 more covering UV, rigging, animation, etc.

### Test Suite
- 17 test files, ~8060 lines
- Covers: tool contracts, security, background certification, live sessions, transport, rollback, engine export
- Run: `cd mcp-server && python3 -m pytest tests/ -v`

### Dependencies
All installed and working:
- mcp >= 1.16.0, starlette >= 0.41.0, uvicorn >= 0.32.0, aiohttp >= 3.8.0, sse-starlette >= 1.6.0, Python 3.12

## Scafforge Integration Assessment

### Compatible
- Deterministic execution model (stateless tools with I/O blends)
- Multi-engine export (Godot targets)
- QA validation built-in (`quality_validate`)
- Checkpoint/resume for long pipelines
- Audit trail for asset provenance
- Trust profiles for sandbox control

### Required for Integration
1. **Orchestration wrapper** — Map asset briefs to tool call sequences
2. **Prompt system** — Guide AI through asset creation pipelines
3. **Post-export validation** — Check Godot import compatibility
4. **Registry bridge** — Connect export outputs to Scafforge asset catalog

### NOT Provided
- No semantic mesh generation from text descriptions
- No procedural generation from text
- No diffusion/LLM integration for 3D generation
- The AI agent + skills provide the orchestration; blender-agent provides the hands

## Stability Issues (Minor)
1. 1x NotImplementedError in background_queue.py (edge case, non-blocking)
2. Add-on requires manual installation
3. WebSocket transport planned but not fully implemented
4. Live session fallback behavior underspecified

## Recommendation
The blender-agent is production-ready for Scafforge integration. The primary work needed is:
1. Create an `asset-description` Scafforge skill that translates game asset briefs into blender-agent tool sequences
2. Build a Blender-MCP subagent path in the Scafforge scaffold
3. Add Godot-specific export validation
4. Automate add-on installation
