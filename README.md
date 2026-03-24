# Scafforge v1

Scafforge is a host-side skill bundle for coding agents. Install the skills into a compatible host, point the host at a repo with specs, plans, or design docs, and let the skill chain generate or repair a complete OpenCode-oriented project workspace.

The generated output is intentionally shaped for OpenCode-style repos with agents, tools, plugins, commands, local skills, ticketing, provenance, and a structured truth hierarchy.

Weak-model first remains the product bias. The package is designed to make weaker or cheaper models more reliable through deterministic workflow contracts, explicit truth ownership, and narrow guarded roles.

## Installation

Copy or symlink each folder under `skills/` into the host's skill directory. Keep each skill directory intact so its `SKILL.md`, `scripts/`, `assets/`, and `references/` remain together.

Example for GitHub Copilot user skills:

```sh
cp -r skills/*/ ~/.copilot/skills/
```

Or symlink each skill:

```sh
for skill in skills/*/; do
  ln -s "$(pwd)/$skill" ~/.copilot/skills/$(basename "$skill")
done
```

Per-project installation works the same way:

```sh
cp -r skills/*/ <your-project>/.github/skills/
```

Scafforge should be treated as a skill bundle, not as a CLI product.

## Usage

1. Open a repo that contains specs, plans, notes, or design docs.
2. Tell the agent to scaffold, retrofit, repair, or diagnose the project, or invoke `scaffold-kickoff`.
3. The agent reads the inputs, asks for blocking decisions, and routes through the correct skill path.
4. Output: a complete project repo or an evidence-backed diagnosis and repair path.

## Default scaffold chain

The default greenfield chain is:

```text
scaffold-kickoff
  -> spec-pack-normalizer
  -> repo-scaffold-factory
  -> opencode-team-bootstrap
  -> ticket-pack-builder
  -> project-skill-bootstrap
  -> agent-prompt-engineering
  -> scafforge-audit
  -> handoff-brief
```

If the audit identifies safe managed-surface drift that can be repaired with the current package, kickoff routes next into `scafforge-repair` before closeout. If the diagnosis identifies a Scafforge package defect first, the diagnosis pack is the handoff: the user manually carries it into the Scafforge dev repo, the package is updated there, and only then does repair return to the subject repo.

`scaffold-kickoff` remains the single public entrypoint for:
- greenfield scaffold
- retrofit scaffold
- managed repair or update
- diagnosis or review of an in-progress repo

## What the agent does

The package splits work between deterministic scripts and host reasoning:

- scripts handle mechanical scaffold generation, workflow audits, and deterministic managed-surface repair
- the host agent handles spec reading, decision packets, agent-team design, prompt hardening, ticket creation, and synthesized local skills

In the standard greenfield path, `agent-prompt-engineering` always runs before `scafforge-audit`. The pass may be light or heavy depending on the chosen models and project-specific coordination risk, but it is not skipped.

## What the generated repo contains

A full greenfield run produces:

- `docs/spec/CANONICAL-BRIEF.md`
- `tickets/manifest.json` and `tickets/BOARD.md`
- `.opencode/agents/`
- `.opencode/tools/`
- `.opencode/plugins/`
- `.opencode/commands/`
- `.opencode/skills/`
- `.opencode/state/`
- `.opencode/meta/bootstrap-provenance.json`
- `START-HERE.md`
- root docs such as `README.md` and `AGENTS.md`

## Truth hierarchy

Generated repos use a structured truth hierarchy so state does not drift:

| File | Owns |
|------|------|
| `docs/spec/CANONICAL-BRIEF.md` | Durable project facts, constraints, decisions, unresolved questions |
| `tickets/manifest.json` | Machine-readable queue state |
| `tickets/BOARD.md` | Derived human-readable board |
| `.opencode/state/workflow-state.json` | Transient stage, approval, and process-version state |
| `.opencode/state/artifacts/` | Stage proof and lifecycle evidence |
| `.opencode/meta/bootstrap-provenance.json` | Scaffold provenance, synthesis history, and repair history |
| `START-HERE.md` | Derived restart surface |

## Package skills

| Skill | What it does |
|-------|-------------|
| `scaffold-kickoff` | Public entrypoint that classifies the run type and routes the chain |
| `spec-pack-normalizer` | Reads messy inputs, extracts facts, asks about ambiguities, writes the canonical brief |
| `repo-scaffold-factory` | Generates the base template tree and structural repo surfaces |
| `opencode-team-bootstrap` | Designs the project-specific agent team and operating layer |
| `ticket-pack-builder` | Creates or repairs a wave-based ticket backlog and remediation follow-up |
| `project-skill-bootstrap` | Creates project-local skills from repo evidence and stack needs |
| `agent-prompt-engineering` | Hardens prompts for generated agents, commands, and workflow surfaces |
| `scafforge-audit` | Runs read-only workflow diagnosis, review validation, and the diagnosis pack |
| `scafforge-repair` | Applies safe workflow-contract repair and managed-surface refreshes |
| `handoff-brief` | Publishes `START-HERE.md` and the restart surface |

## Diagnosis and repair

Diagnosis and repair are now separate host-side skills.

- `scafforge-audit` is read-only and can validate review evidence, run the audit script, and emit the four-report diagnosis pack in the subject repo's `diagnosis/` folder.
- `scafforge-repair` consumes the audit outputs, applies safe managed-surface repairs, records provenance, and routes ticket follow-up when needed.
- When the diagnosis identifies package defects or prevention gaps, the user manually copies the diagnosis pack into the Scafforge dev repo, package changes are implemented there, and repair happens only after returning to the subject repo with the updated package surface.

PR comments, review threads, and check metadata are optional evidence only. They do not become canonical findings until the repo validates them.

## Generated repo-local skills

Scafforge ships the scaffold logic that creates `.opencode/skills/` inside generated repos. Those local skills belong to the output repo operating layer, not to Scafforge's own top-level package skill taxonomy.

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

`review-audit-bridge` remains repo-local generated functionality. It helps the live repo review itself, recommend remediation tickets, and emit process-log output without becoming a top-level Scafforge skill.

## Existing repo path

For repos that already have code, start at `scaffold-kickoff` and let it classify the path:

```text
retrofit
  -> spec-pack-normalizer (if needed)
  -> opencode-team-bootstrap
  -> ticket-pack-builder
  -> project-skill-bootstrap
  -> scafforge-audit
  -> handoff-brief

managed repair or update
  -> scafforge-repair
  -> opencode-team-bootstrap (if project-specific drift remains)
  -> ticket-pack-builder (if follow-up is needed)
  -> project-skill-bootstrap (if repair is needed)
  -> handoff-brief

diagnosis or review
  -> scafforge-audit
  -> manual diagnosis-pack handoff into the Scafforge dev repo when package work is required
  -> scafforge-repair (only if recommended and the required package changes already exist)
  -> handoff-brief
```

## Design principles

- One orchestrated cycle instead of scaffold-now-enrich-later by default
- Agent does creative work, scripts do deterministic mechanical work
- Structured truth hierarchy with exact ownership boundaries
- Weak-model first workflow contracts
- Discovery as research, not deployment
- No standalone package-level refinement route
