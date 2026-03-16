# Scafforge v1

A skill pack for CLI coding agents. Install these skills into GitHub Copilot, Codex, or another compatible agent, then point the agent at a repo with specs, plans, or design docs. The agent follows the skill chain and generates a complete, structured project repository ready for autonomous development.

The generated output is intentionally shaped for **OpenCode-style projects** — with agents, tools, plugins, commands, local skills, a ticket system, and a structured truth hierarchy.

Scafforge is designed first to make weaker or cheaper models more reliable through deterministic workflow contracts, explicit truth ownership, and narrow guarded roles. Stronger hosts still benefit, but the product bias is toward structure that reduces hallucination and uncontrolled drift.

## Installation

### GitHub Copilot (personal — all projects)

Install the Scafforge skill folders into Copilot's user skills directory. The supported contract is to copy or symlink each folder under `skills/` as-is so every skill keeps its own `SKILL.md`, `scripts/`, `assets/`, and `references/`.

```sh
# From this repo
cp -r skills/* ~/.copilot/skills/

# Or symlink each skill
for skill in skills/*/; do
  ln -s "$(pwd)/$skill" ~/.copilot/skills/$(basename $skill)
done
```

Verify with Copilot's `/skills` command — you should see the full Scafforge skill set, including the optional `pr-review-ticket-bridge` extension skill.

### GitHub Copilot (per-project)

Copy the skills into a specific project:

```sh
cp -r skills/* <your-project>/.github/skills/
```

### Via npm

```sh
npm install -g @scafforge/core
# Then copy or symlink the installed package's `skills/*` folders into ~/.copilot/skills/
```

## Usage

1. Open a repo that contains specs, plans, notes, or design docs
2. Tell the agent: "scaffold this project" (or invoke `/scaffold-kickoff`)
3. The agent reads your specs, asks about ambiguities, then follows the full skill chain
4. Output: a complete project repo with agents, tickets, skills, docs, and a restart surface

## What the agent does

The skill chain guides the agent through a single orchestrated cycle:

```
scaffold-kickoff (entrypoint)
  → spec-pack-normalizer     reads messy inputs, produces canonical brief
  → repo-scaffold-factory    generates base file tree (script), then customizes (agent)
  → opencode-team-bootstrap  designs project-specific agent team
  → ticket-pack-builder      creates implementation-ready ticket backlog
  → project-skill-bootstrap  creates project-specific local skills
  → agent-prompt-engineering  hardens prompts with model-specific techniques
  → repo-process-doctor      audits for workflow drift, applies safe repairs
  → handoff-brief            generates START-HERE.md restart surface
```

The package's Python 3 scripts handle deterministic mechanical work (copying 100+ template files, placeholder substitution, running 21 audit checks). The agent handles creative work (reading specs, designing agents, writing project-specific prompts, creating tickets, synthesizing skills).

## What the generated repo contains

A full greenfield run produces:

- `docs/spec/CANONICAL-BRIEF.md` — normalized project brief (source of truth for facts)
- `tickets/manifest.json` + `tickets/BOARD.md` — implementation-ready work queue
- `.opencode/agents/` — project-specific agent team (customized, not generic)
- `.opencode/tools/` — workflow tools (artifact write, ticket update, etc.)
- `.opencode/plugins/` — enforcement plugins (stage gates, tool guards, etc.)
- `.opencode/commands/` — human commands (kickoff, resume)
- `.opencode/skills/` — project-specific local skills (stack standards, repo navigation, etc.)
- `.opencode/state/` — workflow state and artifact registry
- `START-HERE.md` — restart surface for the next session
- `README.md`, `AGENTS.md`, process docs

## Truth hierarchy

Generated repos use a structured truth hierarchy so state does not drift:

| File | Owns |
|------|------|
| `docs/spec/CANONICAL-BRIEF.md` | Durable project facts, constraints, decisions |
| `tickets/manifest.json` | Machine-readable queue state |
| `tickets/BOARD.md` | Derived human-readable board |
| `.opencode/state/workflow-state.json` | Transient stage, approval, and process-version state |
| `.opencode/state/artifacts/` | Stage proof and lifecycle evidence |
| `.opencode/meta/bootstrap-provenance.json` | Scaffold provenance and repair history |
| `START-HERE.md` | Derived restart surface |

## Skill map

| Skill | What it does |
|-------|-------------|
| `scaffold-kickoff` | Entrypoint — classifies run type, orchestrates the full chain |
| `spec-pack-normalizer` | Reads messy inputs, extracts facts, asks about ambiguities, writes canonical brief |
| `repo-scaffold-factory` | Script generates base template tree; agent customizes docs and config |
| `opencode-team-bootstrap` | Analyzes project type, designs project-specific agent team with domain specialists |
| `ticket-pack-builder` | Creates wave-based ticket backlog with acceptance criteria and dependencies |
| `project-skill-bootstrap` | Creates project-specific skills from real data and stack research |
| `agent-prompt-engineering` | Hardens prompts with model-specific techniques (web-researches chosen model) |
| `repo-process-doctor` | Script audits for 21 workflow smells; agent applies safe repairs |
| `review-audit-bridge` | Structures review/QA passes during implementation cycles (post-scaffold) |
| `handoff-brief` | Generates START-HERE.md with actual project state for restart |

## Optional extension skills

| Skill | What it does |
|-------|-------------|
| `pr-review-ticket-bridge` | Host-side PR review, comment validation, and guarded follow-up ticket generation for valid findings |

## Retrofit path

For repos that already have code but need the OpenCode operating layer:

```
scaffold-kickoff (detects existing repo)
  → opencode-team-bootstrap  adds .opencode/ layer
  → ticket-pack-builder      creates backlog if missing
  → project-skill-bootstrap  creates local skills
  → repo-process-doctor      audits and repairs
  → handoff-brief            generates restart surface
```

## Design principles

- **One orchestrated cycle** — no manual enrichment phases
- **Agent does creative work, scripts do mechanical work** — clean separation
- **Project-specific output** — agents, skills, and tickets are customized per project
- **Structured truth hierarchy** — one source of truth per kind of state
- **Weak-model first** — generated repos are shaped so smaller or cheaper models can operate without inventing hidden workflow state
- **Discovery as research, not deployment** — external skills used as reference only
