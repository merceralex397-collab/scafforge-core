# Execution Harness Plan

## Architecture

```
Host Agent (this session)
  ├── opencode run (ticket work) → downstream repo
  ├── codex exec (audit/repair) → downstream repo via Scafforge skills
  └── monitoring (log tailing, state inspection)
```

## Scripts

### scripts/run_agent.sh
Main execution harness with three modes:
- `./run_agent.sh <repo>` — opencode headless ticket work
- `./run_agent.sh <repo> --audit` — codex scafforge-audit
- `./run_agent.sh <repo> --repair` — codex scafforge-repair
- `./run_agent.sh <repo> --continue` — resume last opencode session
- `./run_agent.sh <repo> --prompt "x"` — custom opencode prompt
- `./run_agent.sh <repo> --dry-run` — print command only

### Stdin Handling
All modes use `< /dev/null` to prevent EBADF errors from closed stdin in headless mode.

### Log Collection
Logs written to `active-plans/agent-logs/<repo>-<timestamp>.log`

## Resume Semantics

### opencode
- `--continue` flag resumes the last session
- Team leader agent reads workflow-state.json on startup
- Agent prompt includes current ticket state and remaining work

### codex
- Skills provide full context via SKILL.md files
- AGENTS.md at ~/.codex/ provides Scafforge operating context
- Skills synced from Scafforge/skills/ to ~/.codex/skills/

## Monitoring Strategy

1. Tail agent logs periodically to check progress
2. Check workflow-state.json for state changes
3. Check ticket manifest for completion status
4. If agent exits/fails:
   a. Analyze log for failure pattern
   b. Check if it's a Scafforge issue (fix Scafforge) or downstream issue (re-run)
   c. Run repair if needed, then re-launch agent

## Known Issues

### Glob Tool Scoping
The glob/grep tools in opencode are project-scoped. Agents trying to discover external paths (Godot templates, JDK, Android SDK) must use bash instead.

### managed_blocked Self-Resolution
Agents must use repair_follow_on_refresh to self-unblock when repair leaves managed_blocked state. The improved error message (commit 9460cc63) guides them to do this.

### Team Leader Delegation
Team leader agents delegate to implementers, which adds a sub-agent layer. If the implementer also hits blockers, the chain can fail. The team leader sometimes needs to be told explicitly to work on specific tickets.
