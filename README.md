# Scafforge

Scafforge is a scaffold-generation package for CLI coding agents.

Its job is not to be the project itself. Its job is to help a host agent turn a spec pack, planning notes, design docs, or messy requirements into a **working project operating framework**.

The package should be usable from multiple hosts, but the default generated output is intentionally shaped for **OpenCode-style projects**.

In plain English:

- **the host can vary**: Codex, OpenCode, Claude Code, or another capable CLI
- **the generated repo is opinionated**: it should come out with a strong OpenCode workflow surface by default

## Core promise

A full greenfield run should produce, in **one orchestrated cycle**:

- a normalized canonical brief
- a repo skeleton with signposted docs
- a project `AGENTS.md`
- `opencode.jsonc`
- `.opencode/agents/`
- `.opencode/tools/`
- `.opencode/plugins/`
- `.opencode/commands/`
- `.opencode/skills/`
- an initial ticket system
- a process audit pass
- a restart / handoff surface

The intended outcome is not just "some starter files." It is a repo that is easier for weaker models and future sessions to operate safely.

## Refined v1 product contract

The current implementation direction is now:

- accept messy source repos through **opportunistic scanning first**, then normalize them into a canonical brief and decision packet before scaffolding
- generate a **full orchestration OpenCode scaffold by default**, while keeping heavier packs thin or lazy-activated when they are not immediately needed
- produce an **implementation-ready first execution wave**, but only after blocking ambiguities have been surfaced and resolved rather than guessed
- keep generated repos anchored on a **structured truth hierarchy** so repeated docs become derived views instead of competing sources of truth
- let `repo-process-doctor` **apply safe repairs by default unless explicitly blocked**, while escalating repairs that would change project intent, scope, stack, or human preferences
- ship cross-host installation primarily through **npm package(s)** and documented bootstrap flows, while keeping the generated output OpenCode-oriented

## Canonical generated-repo truth hierarchy

Generated repos should converge on these canonical roles:

- `docs/spec/CANONICAL-BRIEF.md` for durable project facts, goals, constraints, accepted decisions, and unresolved questions
- `tickets/manifest.json` for machine-readable queue state
- `tickets/BOARD.md` for the derived human queue board
- `.opencode/state/workflow-state.json` for transient stage and approval state
- `.opencode/state/artifacts/` plus manifest-backed registration for stage proof and lifecycle evidence
- `.opencode/meta/bootstrap-provenance.json` for scaffold provenance and later repair/synthesis history
- `START-HERE.md` for the derived restart surface, not as a second hidden state machine

This hierarchy is the core mechanism for reducing drift between prompts, tickets, handoff surfaces, and process docs.

## What this repo is

This repository is the **generator package**.

It contains:

- orchestration skills
- scaffold scripts
- templates
- local reference material
- process audit logic
- prompt hardening guidance

## What this repo is not

This repository is not:

- a personal CLI home-folder mirror
- a random bundle of generic utility skills
- a one-host-only configuration repo
- the generated project itself

## Architecture model

Scafforge has two layers.

### Host layer

This package should be consumable by multiple CLI hosts.

That means core skills should avoid assuming one host unless they are clearly adapter-specific.

### Output layer

The generated scaffold is primarily for OpenCode-oriented projects.

That means generated repositories may contain:

- `opencode.jsonc`
- `.opencode/agents/`
- `.opencode/tools/`
- `.opencode/plugins/`
- `.opencode/commands/`
- `.opencode/skills/`
- `.opencode/state/`
- signposted docs and ticket surfaces designed for autonomous agent workflows

OpenCode supports project rules via `AGENTS.md`, reusable skills via `SKILL.md`, JSONC config, markdown commands, local tools, and plugins, which makes it a good target for a generated project operating layer. citeturn375117search2turn375117search0turn375117search4turn375117search12turn375117search18turn375117search8

## Repository structure

```text
skills/
  scaffold-kickoff/
  spec-pack-normalizer/
  repo-scaffold-factory/
  opencode-team-bootstrap/
  ticket-pack-builder/
  project-skill-bootstrap/
  agent-prompt-engineering/
  repo-process-doctor/
  review-audit-bridge/
  handoff-brief/
```

## Skill map

### `scaffold-kickoff`
The default entrypoint and conductor.

It should decide whether the run is:

- greenfield full-cycle scaffold
- OpenCode retrofit
- targeted refinement of an existing generated repo

It should route into downstream skills rather than duplicate their internals.

### `spec-pack-normalizer`
Turns raw notes, chats, Markdown specs, and fragmented plans into one canonical brief.

### `repo-scaffold-factory`
Owns the base scaffold template and renders the first full repo skeleton.

### `opencode-team-bootstrap`
Adds or repairs the `.opencode/` operating layer when the repo already exists and does not need a full scaffold reset.

### `ticket-pack-builder`
Owns ticket generation and refinement.

This should support two modes:

- **bootstrap mode** during the default full-cycle run
- **refine mode** later when the backlog needs regeneration or expansion

### `project-skill-bootstrap`
Owns local project skill generation and refinement.

This should also support two modes:

- **foundation mode**: generate the tight workflow pack the repo needs immediately
- **synthesis mode**: derive stack- and domain-specific skills from the project itself, curated references, external skill patterns, and documentation

### `agent-prompt-engineering`
Hardens prompts, prompt contracts, and agent instructions when the generated workflow needs stricter rails.

### `repo-process-doctor`
Audits the generated repo for workflow drift, contradictory state models, and brittle agent behavior.

### `review-audit-bridge`
Structures implementation review, QA, and audit passes.

### `handoff-brief`
Refreshes `START-HERE.md` and the restart surface so work can resume cleanly.

## Canonical full-cycle flow

The default greenfield contract should be a **single orchestrated run**.

```text
scaffold-kickoff
  -> spec-pack-normalizer
  -> repo-scaffold-factory
  -> ticket-pack-builder (bootstrap mode)
  -> project-skill-bootstrap (foundation mode, then synthesis mode if enough context exists)
  -> agent-prompt-engineering (only when needed)
  -> repo-process-doctor
  -> handoff-brief
```

Optional branch:

- `review-audit-bridge` is mainly for later implementation and QA loops, not for basic initial scaffold creation

Retrofit path:

```text
scaffold-kickoff
  -> spec-pack-normalizer (if inputs are messy)
  -> opencode-team-bootstrap
  -> ticket-pack-builder (if the repo lacks a usable queue)
  -> project-skill-bootstrap
  -> repo-process-doctor
  -> handoff-brief
```

## Project skill generation policy

Scafforge should **not** blindly pull random public skills into the generated repo.

That would create a patchwork of mismatched assumptions, duplicate instructions, and unknown maintenance burdens.

Instead, `project-skill-bootstrap` should use a controlled ladder.

### Layer 1: foundation pack
Generate the core local skills that keep workflow tight:

- project context
- repo navigation
- stack standards
- ticket execution
- docs and handoff
- any repo-specific execution rules needed for safe operation

The default full-orchestration profile should also provision thin versions of:

- workflow observability
- research delegation
- local git specialist guidance
- isolation guidance

Those heavier packs do not all need to be equally verbose on day one. The goal is to ship the lane and its contract without overwhelming weaker models.

### Layer 2: internal or curated patterns
Check a maintained catalog of trusted patterns first.

### Layer 3: project documentation synthesis
Read stack docs, architecture docs, framework docs, API docs, and project references to derive local skills that are specific to the repo.

Examples:

- a migrations skill for the project’s database stack
- a testing skill tuned to the project’s test runner and fixtures
- an API contract skill derived from OpenAPI or internal interface docs
- a deployment safety skill derived from the actual deployment path

### Layer 4: external pattern mining
Search public skill ecosystems for useful patterns, but use them as **inputs to synthesis**, not as direct installs.

Vercel’s skills ecosystem is explicitly built around discoverable, installable skills, and its `find-skills` helper is meant to help agents discover capabilities. The ecosystem now supports many agent hosts, including OpenCode and Codex. citeturn375117search3turn375117search5turn375117search13turn375117search19

### Layer 5: synthesis and normalization
Take the useful workflow shape, rewrite it to match the current project, and emit a local `.opencode/skills/<name>/SKILL.md` that conforms to the repo’s own conventions.

## Critical review of the skill-synthesis idea

This idea is **good**, but only when constrained.

### What is good about it

- It allows generated repos to become more stack-aware and less generic.
- It avoids stuffing every possible rule into the base scaffold.
- It makes local skills project-shaped rather than host-shaped.
- It fits OpenCode well, because OpenCode can discover project-local skills directly from the repo. citeturn375117search0

### What is risky about it

- Public skill discovery can produce noisy or low-fit results.
- Direct installation encourages cargo-cult behavior.
- Documentation-derived skills can become bloated if the synthesis layer copies reference prose instead of extracting procedure.
- Too many local skills can fragment the workflow and confuse weaker models.
- A generated skill pack can drift away from the actual repo if it is not audited later.

### The right stance

Use **discovery as research**, not as deployment.

Use **documentation as evidence**, not as a dumping ground.

Generate **few, sharp, project-specific skills**, not a parade of mediocre helpers.

## Design principles

### One orchestrated build cycle
The default path should not depend on a second manual enrichment phase.

### Host-agnostic, output-opinionated
The host CLI can vary. The generated repo can still be intentionally OpenCode-shaped.

### Deterministic over clever
Prefer a smaller number of explicit, reusable rails over a larger number of vague prompts.

### Tools and local skills before prompt sprawl
Stable procedure should live in tools, plugins, commands, and local skills where possible.

### One source of truth per kind of state
Queue state, approval state, artifacts, and handoff state should not all be conflated.

### Small skill packs beat sprawling skill zoos
Every local skill should justify its existence.

## Current gaps to close

- some skill descriptions still use Codex-specific wording
- `ticket-pack-builder` and `project-skill-bootstrap` need clearer dual-mode contracts
- the package needs a skill-flow manifest or machine-checkable dependency map
- generated template validation still needs a repeatable smoke-test harness
- public-skill pattern mining needs an explicit trust and synthesis policy

## Success criteria

Scafforge is doing its job when a host agent can:

1. ingest a messy spec pack
2. generate a coherent OpenCode-oriented project operating layer in one cycle
3. produce a usable initial ticket system and local skill pack
4. leave behind a repo that can be resumed by weaker models without re-planning the world
