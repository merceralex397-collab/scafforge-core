---
source_url: https://opencode.ai/docs/skills
fetched_with: http
---

# Agent Skills

Define reusable behavior via SKILL.md definitions

Agent skills let OpenCode discover reusable instructions from your repo or home directory. Skills are loaded on-demand via the native `skill`

tool—agents see available skills and can load the full content when needed.

Create one folder per skill name and put a `SKILL.md`

inside it. OpenCode searches these locations:

- Project config:
`.opencode/skills/<name>/SKILL.md`

- Global config:
`~/.config/opencode/skills/<name>/SKILL.md`

- Project Claude-compatible:
`.claude/skills/<name>/SKILL.md`

- Global Claude-compatible:
`~/.claude/skills/<name>/SKILL.md`

- Project agent-compatible:
`.agents/skills/<name>/SKILL.md`

- Global agent-compatible:
`~/.agents/skills/<name>/SKILL.md`

For project-local paths, OpenCode walks up from your current working directory until it reaches the git worktree. It loads any matching `skills/*/SKILL.md`

in `.opencode/`

and any matching `.claude/skills/*/SKILL.md`

or `.agents/skills/*/SKILL.md`

along the way.

Global definitions are also loaded from `~/.config/opencode/skills/*/SKILL.md`

, `~/.claude/skills/*/SKILL.md`

, and `~/.agents/skills/*/SKILL.md`

.

Each `SKILL.md`

must start with YAML frontmatter. Only these fields are recognized:

`name`

(required)`description`

(required)`license`

(optional)`compatibility`

(optional)`metadata`

(optional, string-to-string map)

Unknown frontmatter fields are ignored.

`name`

must:

- Be 1–64 characters
- Be lowercase alphanumeric with single hyphen separators
- Not start or end with
`-`

- Not contain consecutive
`--`

- Match the directory name that contains
`SKILL.md`

Equivalent regex:

`description`

must be 1-1024 characters. Keep it specific enough for the agent to choose correctly.

Create `.opencode/skills/git-release/SKILL.md`

like this:

OpenCode lists available skills in the `skill`

tool description. Each entry includes the skill name and description:

The agent loads a skill by calling the tool:

Control which skills agents can access using pattern-based permissions in `opencode.json`

:

| Permission | Behavior |
|---|---|
`allow` | Skill loads immediately | `deny` | Skill hidden from agent, access rejected | `ask` | User prompted for approval before loading |

Patterns support wildcards: `internal-*`

matches `internal-docs`

, `internal-tools`

, etc.

Give specific agents different permissions than the global defaults.

**For custom agents** (in agent frontmatter):

**For built-in agents** (in `opencode.json`

):

Completely disable skills for agents that shouldn’t use them:

**For custom agents**:

**For built-in agents**:

When disabled, the `<available_skills>`

section is omitted entirely.

If a skill does not show up:

- Verify
`SKILL.md`

is spelled in all caps - Check that frontmatter includes `name`

and`description`

- Ensure skill names are unique across all locations
- Check permissions—skills with
`deny`

are hidden from agents
