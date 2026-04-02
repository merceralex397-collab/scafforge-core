# Smoke Test

## Ticket

- SETUP-001

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `godot --version`
- exit_code: 0
- duration_ms: 33
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
4.6.2.stable.official.71f334935
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. command override 2

- reason: Explicit smoke-test command override supplied by the caller.
- command: `echo Bootstrap status check: && cat .opencode/state/workflow-state.json | grep -A3 "bootstrap"`
- exit_code: 0
- duration_ms: 4
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
Bootstrap status check: && cat .opencode/state/workflow-state.json | grep -A3 "bootstrap"
~~~~

#### stderr

~~~~text
<no output>
~~~~
