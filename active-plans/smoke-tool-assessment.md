# Smoke Tool Assessment

## Current State

The smoke test tool (`smoke_test` in opencode tools) is used during the `qa` → `smoke-test` ticket lifecycle transition.

### How It Works
1. Team leader or QA agent calls `smoke_test` with a command and ticket_id
2. Tool runs the command and captures output
3. Creates a smoke-test artifact in .opencode/state/artifacts/history/

### Strengths
- Integrated into ticket lifecycle
- Creates audit trail via artifacts
- Supports command override for different project types

### Weaknesses (RC-007)
- Single monolithic implementation
- Python-centric validation assumptions
- No built-in Godot export validation
- No APK content validation
- No MCP server health check
- No structured pass/fail criteria

### Godot-Specific Gaps (RC-008)
- `godot4 --headless --export-debug` not in SAFE_BASH regex
- Export template discovery requires external path access
- APK validation (unzip check) not automated
- No keystore/signing validation

### Recommendations
1. Add Godot commands to SAFE_BASH regex in stage-gate-enforcer
2. Add smoke test profiles (Python, Godot, Node.js, etc.)
3. Add APK content validation as post-export check
4. Separate structural validation from functional validation

### Priority
LOW — current manual smoke test approach works; agents can use bash for custom validation. Automating would improve reliability but isn't blocking.
