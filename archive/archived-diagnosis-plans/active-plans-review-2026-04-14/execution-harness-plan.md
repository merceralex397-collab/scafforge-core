# Execution Harness Plan

## Architecture

```
Host Agent (this session)
  ├── opencode run (ticket work) → downstream repo
  ├── codex exec (audit/repair, medium reasoning) → downstream repo via Scafforge skills
  ├── kilo run (audit/repair fallback) → parent workspace when downstream state interferes
  ├── copilot -p (audit/repair final fallback) → parent workspace
  └── monitoring (log tailing, state inspection)
```

## Scripts

### scripts/run_agent.sh
Main execution harness with three modes:
- `./run_agent.sh <repo>` — opencode headless ticket work
- `./run_agent.sh <repo> --audit` — provider-aware scafforge-audit (`codex -> kilo -> copilot`)
- `./run_agent.sh <repo> --repair` — provider-aware scafforge-repair (`codex -> kilo -> copilot`)
- `./run_agent.sh <repo> --continue` — resume last opencode session
- `./run_agent.sh <repo> --prompt "x"` — custom opencode prompt
- `./run_agent.sh <repo> --dry-run` — print command only
- `./run_agent.sh <repo> --provider <host>` — force `codex`, `kilo`, or `copilot`

### Stdin Handling
All modes use `< /dev/null` to prevent EBADF errors from closed stdin in headless mode.

### Log Collection
Logs written to `active-plans/agent-logs/<repo>-<timestamp>.log`

## Resume Semantics

### opencode
- `--continue` flag resumes the last session
- Team leader agent reads workflow-state.json on startup
- Agent prompt includes current ticket state and remaining work

### audit/repair hosts
- Codex is the primary host and must run with `model_reasoning_effort="medium"`
- Kilo is the second-choice host; prefer `kilo/x-ai/grok-code-fast-1:optimized:free` and then `kilo/nvidia/nemotron-3-super-120b-a12b:free`
- Copilot CLI is the last-resort fallback when both Codex and Kilo are unavailable or exhausted
- Host validation depends on fresh skill copies under `~/.codex/skills/`, `~/.copilot/skills/`, and `~/.config/kilo/skills/`

## Monitoring Strategy

1. Tail agent logs periodically to check progress
2. Check workflow-state.json for state changes
3. Check ticket manifest for completion status
4. If agent exits/fails:
    a. Analyze log for failure pattern
    b. Distinguish provider failure (quota/auth/tool outage) from repo/process failure
    c. Check if it's a Scafforge issue (fix Scafforge) or downstream issue (re-run)
    d. Run repair if needed, then re-launch agent

## Known Issues

### Glob Tool Scoping
The glob/grep tools in opencode are project-scoped. Agents trying to discover external paths (Godot templates, JDK, Android SDK) must use bash instead.

### managed_blocked Self-Resolution
Agents must use repair_follow_on_refresh to self-unblock when repair leaves managed_blocked state. The improved error message (commit 9460cc63) guides them to do this.

### Team Leader Delegation
Team leader agents delegate to implementers, which adds a sub-agent layer. If the implementer also hits blockers, the chain can fail. The team leader sometimes needs to be told explicitly to work on specific tickets.
