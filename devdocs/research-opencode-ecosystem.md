# OpenCode ecosystem research for Scafforge

## Scope

This research focuses on practical OpenCode patterns that can improve Scafforge’s generated output, especially `.opencode/agents`, tools, plugins, commands, skills, parallel delegation, workflow observability, and safe orchestration boundaries.

Evidence sources:

- Scafforge package and templates
- `/home/a/GPTTalker` as a realized generated output
- official OpenCode docs
- public ecosystem examples and plugin/skill repos

## Executive summary

Scafforge already has the right structural model:

- human commands as entrypoints
- tools for canonical state changes
- plugins for enforcement
- skills for lazy-loaded procedure
- a truth hierarchy centered on brief, tickets, workflow state, artifacts, provenance, and `START-HERE.md`

The main opportunity is not to add more generic scaffolding. It is to improve how generated output becomes project-specific while keeping optional ecosystem integrations opt-in.

## What GPTTalker confirms

`GPTTalker` demonstrates the value of:

- one visible team leader with hidden specialists
- domain-specialized implementers
- strict stage gates
- explicit read-only vs write-capable boundaries
- invocation logging and provenance
- project-specific synthesized skills instead of generic skill dumping

That supports Scafforge’s existing direction and argues for sharper specialization during `opencode-team-bootstrap`, not for a larger generic baseline.

## Official OpenCode patterns that matter

### Agents

OpenCode’s agent model supports primary agents plus subagents. That maps well to Scafforge’s one visible lead plus hidden specialists.

Source: <https://opencode.ai/docs/agents/>

### Commands

Commands are human entrypoints, not the internal workflow. That matches Scafforge’s design and should remain true.

Source: <https://opencode.ai/docs/commands/>

### Skills

Skills are lazy-loaded on demand through the `skill` tool. This strongly supports Scafforge’s small baseline plus evidence-based synthesis model.

Source: <https://opencode.ai/docs/skills/>

### Plugins and custom tools

Plugins and local custom tools are the correct place for guardrails, synchronization, and enforcement logic. This validates Scafforge’s emphasis on tool-backed stage control and plugin-backed safety.

Sources:

- <https://opencode.ai/docs/plugins/>
- <https://opencode.ai/docs/custom-tools/>

### MCP

Official docs warn that MCP servers add context and can become expensive. This supports per-agent MCP access instead of wide-open defaults.

Source: <https://opencode.ai/docs/mcp-servers/>

## Ecosystem patterns worth adopting selectively

### Good patterns

- bounded background or read-only delegation
- stronger env and shell safety guards
- optional observability extensions
- narrow specialist subagents for CI, review, or repo exploration

### Patterns to avoid in the default scaffold

- always-on heavy orchestration harnesses
- broad write-capable background agents
- automatic external skill imports
- always-enabled external MCP bundles

## Recommendations for Scafforge

1. Generate multiple implementers only when the brief shows distinct subsystems.
2. Keep parallelism bounded and mostly read-only unless isolation is explicit.
3. Tighten per-agent tool and MCP boundaries.
4. Keep the baseline skill pack small, but require synthesized skills to be procedural and project-specific.
5. Strengthen provenance and observability defaults.
6. Treat advanced integrations as optional profile packs, not core defaults.

## Bottom line

Scafforge should use the OpenCode ecosystem as a pattern source, not as something to auto-import wholesale. The best path is to keep the current deterministic scaffold contract, make project-specific customization sharper, and expose opt-in extension points for advanced teams.
