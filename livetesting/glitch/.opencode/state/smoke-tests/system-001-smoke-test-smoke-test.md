# Smoke Test

## Ticket

- SYSTEM-001

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `godot --headless --path . --quit`
- exit_code: 0
- duration_ms: 280
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
Godot Engine v4.6.2.stable.official.71f334935 - https://godotengine.org

[PlayerState] Initialized - Health: 3
[GlitchState] Initialized - Corruption level: 0
[GameState] Initialized - Current level: 
[LevelManager] Initialized
~~~~

#### stderr

~~~~text
<no output>
~~~~
