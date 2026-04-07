# Scafforge v1

Scafforge is a strong-host skill bundle for coding agents. Install the skills into a compatible host, point the host at a repo with specs, plans, or design docs, and let the skill chain generate or repair a complete OpenCode-shaped project workspace for downstream execution.

The generated output is intentionally shaped for OpenCode-style repos with agents, tools, plugins, commands, local skills, ticketing, provenance, and a structured truth hierarchy.

Weak-model first remains the product bias. The package is designed to make weaker or cheaper models more reliable through deterministic workflow contracts, explicit truth ownership, and narrow guarded roles.

The package competence bar is defined in [references/competence-contract.md](references/competence-contract.md). In practice that means the generated workflow must always expose one legal next move; if the operator is confused about how to proceed, Scafforge should treat that as package evidence, not user error.

## Supported stacks

Scafforge now separates detection, bootstrap, and execution-audit coverage by stack tier.

- Tier 1: full detection, bootstrap guidance, and execution audit for Python, Node, Rust, Go, Godot, Java or Android, C or C++, and .NET.
- Tier 2: detection and bootstrap guidance for Flutter or Dart, Swift, Zig, and Ruby.
- Tier 3: detection with explicit blocker reporting for Elixir, PHP, and Haskell.
- Tier 4: generic fallback detection for Makefile-driven and shell-script repos when no stronger adapter matches.

The adapter contract is documented in [references/stack-adapter-contract.md](references/stack-adapter-contract.md).

## Validation And Release Proof

Package validation runs are separate from subject-repo release proof.

- Package validation entrypoints are `npm run validate:contract`, `npm run validate:smoke`, `python3 scripts/integration_test_scafforge.py`, and `python3 scripts/validate_gpttalker_migration.py`.
- The package validators prove the Scafforge package itself; they do not substitute for stack-specific release proof in generated repos.
- The authoritative Tier 1 proof-host matrix and command contract live in [references/stack-adapter-contract.md](references/stack-adapter-contract.md).
- If a host is missing a Tier 1 toolchain, report the blocker truthfully instead of treating package smoke checks as release proof.

## Installation

Copy or symlink each folder under `skills/` into the host's skill directory. Keep each skill directory intact so its `SKILL.md`, `scripts/`, `assets/`, and `references/` remain together.

Scafforge should be treated as a skill bundle, not as a CLI product.

## Usage

1. Open a repo that contains specs, plans, notes, or design docs.
2. Tell the agent to scaffold, retrofit, pivot, repair, or diagnose the project, or invoke `scaffold-kickoff`.
3. The agent reads the inputs, asks one batched round of blocking decisions when needed, records the selected `model_tier`, and routes through the correct skill path.
4. Output: a complete project repo or an evidence-backed diagnosis and repair path.

Historical implementation-planning context for the reliability re-architecture is archived in [references/archived-diagnosis-plans/recovery-plan/00-PLAN-INDEX.md](references/archived-diagnosis-plans/recovery-plan/00-PLAN-INDEX.md).

## Live testing sandbox

The `livetesting` folder is reserved for in-repo experimentation where Scafforge is used to scaffold and iterate prototypes from inside this repo. Use the integrated IDE terminal plus `opencode` to run the full greenfield chain and inspect generated beams in `.opencode`, `tickets`, and `START-HERE.md`.

The current smoke project is `livetesting/glitch`, a simple Android 2D platformer concept for early stress tests.

## Default scaffold chain

Greenfield generation is one kickoff run. The default chain is:

```text
scaffold-kickoff
  -> spec-pack-normalizer
  -> repo-scaffold-factory
  -> repo-scaffold-factory:verify-bootstrap-lane
  -> project-skill-bootstrap
  -> opencode-team-bootstrap
  -> agent-prompt-engineering
  -> ticket-pack-builder
  -> repo-scaffold-factory:verify-generated-scaffold
  -> handoff-brief
```

This pass allows one batched blocking-decision round and then completes in one uninterrupted same-session generation run. No second Scafforge generation pass is required before development begins. Greenfield now has two proof layers: an early bootstrap-lane proof immediately after scaffold render, and the later immediate-continuation proof before handoff. Greenfield completion requires immediate continuation proof, not only surface agreement. That proof must be completed before handoff publication.
The shipped package still carries one temporary contract smell: `project-skill-bootstrap` and `opencode-team-bootstrap` form a dependency seam, so Scafforge keeps the current order until a minimal-operable-versus-specialization split exists.

The one-shot path now also includes environment detection before specialization continues. Missing prerequisites must surface as blocker guidance instead of letting the flow drift into downstream failures.

`scaffold-kickoff` remains the single public entrypoint for:
- greenfield scaffold
- retrofit scaffold
- pivot on an existing repo
- managed repair or update
- diagnosis or review of an in-progress repo

## What the agent does

The package splits work between deterministic scripts and host reasoning:

- scripts handle mechanical scaffold generation, workflow audits, and deterministic managed-surface repair
- the host agent handles spec reading, decision packets, agent-team design, prompt hardening, ticket creation, and synthesized local skills

In the standard greenfield path, `agent-prompt-engineering` always runs before `ticket-pack-builder`. The pass may be light or heavy depending on the chosen models and project-specific coordination risk, but it is not skipped.

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

The generated workflow also includes:

- environment bootstrap detection and blocker persistence in workflow state
- stack-specific smoke or execution checks where the detected stack supports them
- review and QA expectations that fail closed when build, lint, type, reference, or smoke validation cannot run
- verdict-aware ticket transitions, including remediation follow-up that preserves original finding codes

## Truth hierarchy

Generated repos use a structured truth hierarchy so state does not drift:

| File | Owns |
|------|------|
| `docs/spec/CANONICAL-BRIEF.md` | Durable project facts, constraints, decisions, unresolved questions |
| `tickets/manifest.json` | Machine-readable queue state and registered artifact metadata |
| `tickets/BOARD.md` | Derived human-readable board |
| `.opencode/state/workflow-state.json` | Transient stage, approval, and process-version state |
| `.opencode/state/artifacts/` | Canonical artifact bodies, historical snapshots, and mirrored registry state |
| `.opencode/meta/bootstrap-provenance.json` | Scaffold provenance, synthesis history, and repair history |
| `START-HERE.md` | Top-level derived restart surface |

`START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces. They must agree with `tickets/manifest.json` and `.opencode/state/workflow-state.json`; they do not outrank them.

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
| `scafforge-pivot` | Routes midstream feature/design changes through canonical-truth updates and bounded refresh |
| `handoff-brief` | Publishes `START-HERE.md` and the restart surface |

## Diagnosis and repair

Generation, audit, repair, and pivot are separate lifecycle stages.

- `scaffold-kickoff` is the only public generation entrypoint.
- Initial generation ends only after the pre-handoff verification gate and `handoff-brief`.
- `scafforge-audit`, `scafforge-repair`, and `scafforge-pivot` are later lifecycle tools, not part of the initial generation cycle.

- `scafforge-audit` is read-only and always validates review evidence, runs the audit script, and emits the four-report diagnosis pack in the subject repo's `diagnosis/` folder.
- `scafforge-audit` includes code-quality diagnosis as well as workflow-surface diagnosis, using EXEC and REF finding families for execution and reference-integrity failures.
- `scafforge-repair` is the public repair contract: it must apply safe managed-surface repairs, continue into any required local-skill or agent/prompt/ticket follow-up, record provenance, and route ticket follow-up when needed.
- `scafforge-repair` replaces managed surfaces non-destructively, records backup and diff provenance, and creates remediation tickets instead of editing product code when audit finds source-layer EXEC or REF issues.
- `scafforge-pivot` is the public pivot contract: it must update canonical brief truth first, record stale surfaces, route only the affected refresh steps, and verify the repo before handoff.
- Source-layer `EXEC*` follow-up and visible `pending_process_verification` are not, by themselves, proof that managed repair failed. They remain live repo follow-up after the managed workflow layer is repaired.
- `skills/scafforge-repair/scripts/run_managed_repair.py` is the public fail-closed repair runner. It emits the machine-readable repair plan, execution record, and post-repair verification diagnosis pack, automatically carries forward transcript-backed audit evidence when that evidence exists, reruns verification, and blocks handoff when required downstream stages still have not run.
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py` is the deterministic refresh engine for the first repair phase only. Invoking that script alone does not satisfy the full repair contract unless no downstream regeneration or ticket follow-up is required.
- When the diagnosis identifies package defects or prevention gaps, the user manually copies the diagnosis pack into the Scafforge dev repo, package changes are implemented there, and repair happens only after returning to the subject repo with the updated package surface.
- After package changes land, run exactly one fresh subject-repo audit as `--diagnosis-kind post_package_revalidation`, using the same supporting logs when the original basis was transcript-backed. If that revalidation pack still says package work first, stop and return to the Scafforge dev repo; if it clears package work, use that revalidation pack as the repair basis immediately.
- Do not keep running extra subject-repo audits after repair. The public repair runner owns post-repair verification and emits the `post_repair_verification` diagnosis pack itself.
- If repeated diagnosis packs report the same repair-routed findings and no newer package or process-version change exists, or if a later zero-finding verification pack dropped the earlier transcript basis, stop auditing the subject repo and fix the Scafforge package first.

PR comments, review threads, and check metadata are optional evidence only. They do not become canonical findings until the repo validates them.

## Generated repo-local skills

Scafforge ships the scaffold logic that creates `.opencode/skills/` inside generated repos. Those local skills belong to the output repo operating layer, not to Scafforge's own top-level package skill taxonomy.

Baseline generated local skills include:

- `project-context`
- `repo-navigation`
- `stack-standards`
- `model-operating-profile`
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
  -> project-skill-bootstrap
  -> ticket-pack-builder
  -> scafforge-audit
  -> handoff-brief

managed repair or update
  -> scafforge-repair
  -> project-skill-bootstrap (if repair is needed)
  -> opencode-team-bootstrap (if project-specific drift remains)
  -> agent-prompt-engineering (if prompts or model-profile surfaces changed)
  -> ticket-pack-builder (if follow-up is needed)
  -> handoff-brief

pivot
  -> scafforge-pivot
  -> project-skill-bootstrap (if local skills changed)
  -> opencode-team-bootstrap (if team/tools drifted)
  -> agent-prompt-engineering (if prompts changed)
  -> ticket-pack-builder (if lineage must be refined, reopened, or superseded)
  -> scafforge-repair (if managed workflow surfaces drifted)
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
- One kickoff run for full-depth generation
- No standalone package-level refinement route
