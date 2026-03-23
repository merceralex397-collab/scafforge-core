# Scafforge v1

A skill pack for CLI coding agents. Install these skills into GitHub Copilot, Codex, or another compatible agent, then point the agent at a repo with specs, plans, or design docs. The agent follows the skill chain and generates a complete, structured project repository ready for autonomous development.

The generated output is intentionally shaped for **OpenCode-style projects** — with agents, tools, plugins, commands, local skills, a ticket system, and a structured truth hierarchy.

Scafforge is designed first to make weaker or cheaper models more reliable through deterministic workflow contracts, explicit truth ownership, and narrow guarded roles. Stronger hosts still benefit, but the product bias is toward structure that reduces hallucination and uncontrolled drift.

## Installation

### GitHub Copilot (personal — all projects)

Install the Scafforge skill folders into Copilot's user skills directory. The supported contract is to copy or symlink each folder under `skills/` as-is so every skill keeps its own `SKILL.md`, `scripts/`, `assets/`, and `references/`.

The commands below install the full bundled skill pack, including the non-backbone `pr-review-ticket-bridge` extension skill. If you do not want that extension available, omit the `skills/pr-review-ticket-bridge/` directory when copying or symlinking.

```sh
# From this repo
cp -r skills/*/ ~/.copilot/skills/

# Or symlink each skill
for skill in skills/*/; do
  ln -s "$(pwd)/$skill" ~/.copilot/skills/$(basename $skill)
done
```

Verify with Copilot's `/skills` command — you should see the full Scafforge skill set, including the bundled `pr-review-ticket-bridge` extension skill if you kept it installed.

### GitHub Copilot (per-project)

Copy the skills into a specific project:

```sh
cp -r skills/*/ <your-project>/.github/skills/
```

### Via npm

```sh
npm install -g @scafforge/core
# Then copy or symlink the installed package's `skills/*/` directories into ~/.copilot/skills/
```

## Usage

1. Open a repo that contains specs, plans, notes, or design docs
2. Tell the agent: "scaffold this project" (or invoke `/scaffold-kickoff`) even if the repo already exists and needs retrofit or process repair
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
  → agent-prompt-engineering  runs the required prompt-hardening pass
  → repo-process-doctor      audits for workflow drift, applies safe repairs
  → handoff-brief            generates START-HERE.md restart surface
```

`scaffold-kickoff` remains the public entrypoint for existing repos as well. It classifies whether the job is greenfield scaffold, retrofit, or managed workflow repair, then routes to the right downstream skills without asking the user to choose the lower-level skill manually.

The package's Python 3 scripts handle deterministic mechanical work (copying 100+ template files, placeholder substitution, running workflow audits, and applying managed-surface retrofit repairs). The agent handles creative work (reading specs, designing agents, writing project-specific prompts, creating tickets, synthesizing skills).

In the standard greenfield path, `agent-prompt-engineering` always runs before `repo-process-doctor`. The pass may be light or heavy depending on the selected models and project-specific coordination risk, but it is not skipped.

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

## Default scaffold chain

| Skill | What it does |
|-------|-------------|
| `scaffold-kickoff` | Entrypoint — classifies run type, orchestrates the full chain |
| `spec-pack-normalizer` | Reads messy inputs, extracts facts, asks about ambiguities, writes canonical brief |
| `repo-scaffold-factory` | Script generates base template tree; agent customizes docs and config |
| `opencode-team-bootstrap` | Analyzes project type, designs project-specific agent team with domain specialists |
| `ticket-pack-builder` | Creates wave-based ticket backlog with acceptance criteria and dependencies |
| `project-skill-bootstrap` | Creates project-specific skills from real data and stack research |
| `agent-prompt-engineering` | Runs the required prompt-hardening pass for the generated agent, command, and workflow surfaces |
| `repo-process-doctor` | Script audits workflow drift; agent applies safe repairs or runs deterministic managed-surface replacement |
| `handoff-brief` | Generates START-HERE.md with actual project state for restart |

## Generated repo-local skills

Scafforge ships the scaffold logic that creates `.opencode/skills/` inside output repos. Those generated local skills belong to the output repo operating layer, not to Scafforge's own top-level package skill taxonomy.

Baseline generated local skills include:

- `project-context`
- `repo-navigation`
- `stack-standards`
- `ticket-execution`
- `review-audit-bridge`
- `docs-and-handoff`
- `workflow-observability`
- `research-delegation`
- `local-git-specialist`
- `isolation-guidance`

`review-audit-bridge` lives here because it is consumed by the generated repo's implementation, review, security, and QA lanes after scaffold creation.

## Bundled optional extension skills

| Skill | What it does |
|-------|-------------|
| `pr-review-ticket-bridge` | Host-side PR review, comment validation, and guarded follow-up ticket generation for valid findings. Bundled with the package, but outside the default scaffold chain. |

## Existing repo path

For repos that already have code, start at `scaffold-kickoff` and let it classify whether the repo needs retrofit or doctor-led repair:

```
scaffold-kickoff (detects existing repo state)
  → spec-pack-normalizer     only if the canonical brief is missing or badly fragmented
  → opencode-team-bootstrap  adds or repairs the .opencode layer when needed
  → ticket-pack-builder      repairs backlog state if missing or weak
  → project-skill-bootstrap  repairs local skills when needed
  → repo-process-doctor      audits or runs apply-repair for managed-surface correction
  → handoff-brief            generates restart surface
```

If the repo is already Scafforge-managed and mainly needs a workflow-contract update, kickoff should route straight into `repo-process-doctor` in `apply-repair` mode. The doctor applies safe repairs by default and escalates intent-changing choices instead of silently rewriting project intent.

## Design principles

- **One orchestrated cycle** — no manual enrichment phases
- **Agent does creative work, scripts do mechanical work** — clean separation
- **Project-specific output** — agents, skills, and tickets are customized per project
- **Structured truth hierarchy** — one source of truth per kind of state
- **Weak-model first** — generated repos are shaped so smaller or cheaper models can operate without inventing hidden workflow state
- **Default orchestration stays flat** — one visible team leader is standard; manager or section-leader layers remain advanced customization, not a first-class scaffold profile
- **Discovery as research, not deployment** — external skills used as reference only
