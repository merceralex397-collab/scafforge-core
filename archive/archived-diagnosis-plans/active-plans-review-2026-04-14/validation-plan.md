# Validation Plan

## Downstream Repo Validation

### GPTTalker — MCP Server Functional
**Criteria**: Server starts, MCP tools exposed, core logic works
**Method**:
1. opencode agent fixes migration bug (CREATE_INDEXES ordering)
2. Server startup test: `python -m src.mcp_server` (no crash)
3. MCP tool listing: verify tools are registered
4. Core operation test: basic knowledge graph operation succeeds
**Status**: Agent running — identified bug, delegating to implementer

### Spinner — APK Compilation + Tickets Complete
**Criteria**: Successful APK compilation, all tickets done, code review passes
**Method**:
1. opencode agent completes remaining 5 tickets
2. Godot headless export: `godot4 --headless --path . --export-debug "Android Debug" build/android/spinner-debug.apk`
3. APK validation: `unzip -l spinner-debug.apk` shows Android manifest + classes
4. Code review via code-review sub-agent
**Status**: Agent running — attempting Godot export for RELEASE-001

### Glitch — APK Compilation + Tickets Complete
**Criteria**: Successful APK compilation, all tickets done, code review passes
**Method**:
1. opencode agent completes remaining 13 tickets
2. Godot headless export
3. APK validation
4. Code review
**Status**: Agent running — working on REMED-004

## Scafforge Internal Validation

### Stage-Gate Enforcer
**Criteria**: Plugin doesn't crash, correctly blocks/allows tools
**Method**: Downstream agents can use all tools after unblocking
**Status**: VALIDATED — all 3 agents making tool calls successfully

### Repair Idempotency
**Criteria**: Running repair twice doesn't crash or corrupt state
**Method**: Ran repair multiple times on all 3 repos
**Status**: VALIDATED — ticket creation idempotency fixed (commit c8bb368f)

### Managed Blocked Resolution
**Criteria**: Agents can self-unblock using repair_follow_on_refresh
**Method**: Improved error message guides agents
**Status**: VALIDATED — glitch agent immediately self-unblocked

### Config Audit
**Criteria**: CONFIG001-005 detect missing/invalid config fields
**Method**: Audit runs on repos with known issues
**Status**: VALIDATED — integrated into audit pipeline

## Future Validation (Phase 7)

### Asset Pipeline Repos (womanvshorse VA-VD)
**Criteria**: Each repo scaffolded, tickets created, agents complete work
**Method**: Scafforge greenfield → headless agent execution → code review
**Status**: NOT STARTED

### Blender-Agent Integration
**Criteria**: MCP server starts, basic operations work
**Method**: Inspect blender-agent, assess readiness, fix if needed
**Status**: NOT STARTED
