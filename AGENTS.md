# AGENTS.md

This file governs work inside the Scafforge package repository itself.

Scafforge is not the generated project. It is the generator, template source, orchestration pack, validation harness, and process contract used by a host agent to build or repair a generated project.

That distinction is law in this repository. Do not collapse package-repo surfaces and generated-repo surfaces together.

## Mission

Maintain a host-agnostic scaffold package that can turn raw project inputs into a deterministic, signposted, OpenCode-oriented repo operating framework.

The product bias remains weak-model first. Stronger models should still work well, but the package exists to make weaker or cheaper models reliable through deterministic workflow contracts, narrow role boundaries, explicit truth ownership, and proof-backed restart guidance.

The package competence bar is defined in `references/competence-contract.md`. If the generated workflow leaves the operator unsure what the next legal move is, treat that as package evidence, not user error.

## Repo Identity

There are two different layers in play.

### Package layer

This repository.

It contains:
- package skills under `skills/`
- template assets under `skills/repo-scaffold-factory/assets/project-template/`
- validation and proof harnesses under `scripts/` and `tests/`
- contract references under `references/`
- package planning artifacts under `tickets/`
- live test repos under `livetesting/`

### Output layer

What Scafforge generates for a subject repo.

That output may include:
- root `AGENTS.md`
- `opencode.jsonc`
- `.opencode/agents/`
- `.opencode/tools/`
- `.opencode/plugins/`
- `.opencode/commands/`
- `.opencode/skills/`
- `.opencode/state/`
- `.opencode/meta/`
- signposted docs and ticket surfaces

Do not import the output layer into the package root. If you need to change generated-repo behavior, change package code or template assets. If you need a live generated repo for proof, use `livetesting/` or a harness-created fixture.

## Package Working Mode

Scafforge package work is not driven by the generated repo workflow-state manager.

In this repo:
- `tickets/manifest.json` is a package backlog tracker, not a runtime state manager
- `tickets/BOARD.md` is a derived tracker view, not canonical workflow state
- ticket markdown files must carry the actual implementation instructions, files to update, and verification steps
- package-root `.opencode/` runtime state surfaces must not be created to manage package work
- generated-repo runtime behavior is changed by editing template assets or package scripts, never by simulating a generated repo at the package root

This repo is being operated with a strong host and human review. That is exactly why the tickets must be self-contained and why package planning must not pretend the generated workflow manager exists here.

## Shipping State

The implementation program is complete. The shipped package baseline is now the reference point for future doc and contract updates.

`IMPLEMENTATION-HANDOFF.md` remains as historical transition guidance for the closed implementation sequence. Future package work should start from `tickets/manifest.json`, `tickets/BOARD.md`, and the ticket markdowns, then keep root docs, references, and template assets aligned to the code they describe.

## Authority Baseline

The package-wide authority map is documented in [references/authority-adr.md](references/authority-adr.md), and the invariant checklist lives in [references/invariant-catalog.md](references/invariant-catalog.md).

- `scafforge-audit` owns diagnosis disposition.
- The generated runtime workflow layer owns canonical repo mutation.
- `scafforge-pivot` owns pivot-state persistence.
- `handoff-brief` owns restart publication from the verified final snapshot.
- `agent-prompt-engineering` owns contract alignment for prompts, workflow docs, and generated behavior.

Repair-side restart rendering and raw workflow mutation were the first duplicate-authority seam to collapse. Later tickets should cite the ADR and invariant catalog directly instead of restating the owner map ad hoc.

## Canonical Package Validation Commands

The package-level validation entrypoints are:
- `npm run validate:contract`
- `npm run validate:smoke`
- `python3 scripts/integration_test_scafforge.py`
- `python3 scripts/validate_gpttalker_migration.py`

Use `python3` or `sys.executable` for Python entrypoints in this repository. Do not assume a `python` shim exists or points to the correct interpreter.

## Live Testing

`livetesting/` is the sanctioned place for in-repo experiments that need actual generated-repo surfaces.

Current focus:
- `livetesting/glitch/` is the standing Godot Android stress target

If a package change needs real generated runtime state, prove it in `livetesting/` or through the harness. Do not reproduce that state at the repository root.

## First Principles

1. Keep core package behavior host-agnostic unless a file is clearly adapter-specific.
2. Keep the default generated repo OpenCode-oriented.
3. Prefer one orchestrated full-cycle build over a base-pass-plus-manual-enrichment design.
4. Prefer deterministic workflow contracts over verbose prompting.
5. Preserve clear ownership boundaries between diagnosis, mutation, restart publication, and proof.
6. Generate the smallest surface compatible with the selected profile; for the default full profile, keep heavier packs thin or lazy-activated until they are actually needed.
7. Never treat public skill discovery as permission to auto-install random skills.
8. Treat package-root generated-repo simulation as a defect unless it lives under `livetesting/`, a fixture, or a template path.

## Default Scaffold Spine

These skills are the backbone of the greenfield path and should remain coherent as one chain:

- `scaffold-kickoff`
- `spec-pack-normalizer`
- `repo-scaffold-factory`
- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`
- `ticket-pack-builder`
- `handoff-brief`

`scafforge-audit`, `scafforge-repair`, and `scafforge-pivot` are separate post-generation lifecycle skills.

The greenfield proof chain includes:
- environment bootstrap detection
- bootstrap-blocker persistence and routing
- stack-specific execution proof where available
- reference-integrity verification before handoff

The shipped package still carries one explicit temporary contract smell: `project-skill-bootstrap` and `opencode-team-bootstrap` form a dependency seam, and the current order remains until Scafforge has a real minimal-operable-versus-specialization split.

## Canonical Workflow Contract

### Greenfield full-cycle scaffold

The default route is:

1. `scaffold-kickoff` decides this is a greenfield build.
2. `spec-pack-normalizer` produces the canonical brief.
3. `repo-scaffold-factory` renders the base scaffold.
4. Environment bootstrap detection runs and halts the flow with explicit blocker guidance when prerequisites are still missing.
5. The kickoff-owned bootstrap-lane proof confirms one canonical first move before specialization begins, including VERIFY009 bootstrap-blocker persistence and routing.
6. `project-skill-bootstrap` completes the repo-local skill pass.
7. `opencode-team-bootstrap` designs the project-specific agent team.
8. `agent-prompt-engineering` performs the same-session prompt-hardening pass.
9. `ticket-pack-builder` runs in bootstrap mode.
10. The kickoff-owned immediate-continuation verification gate proves the repo is truthful and immediately runnable, including VERIFY010 execution-surface checks and VERIFY011 reference-integrity checks.
11. `handoff-brief` refreshes the restart surface.

The greenfield contract remains one-shot: one batched blocking-decision round, one uninterrupted same-session generation pass, then direct handoff into development. No second Scafforge generation pass is required before development begins.

Greenfield output must be immediately continuable.

### Retrofit flow

Use the lighter path when a repo already exists and mainly needs an OpenCode operating layer:

1. `scaffold-kickoff` decides this is retrofit work.
2. `spec-pack-normalizer` runs only if the input context is fragmented.
3. `opencode-team-bootstrap` adds or repairs `.opencode/`.
4. `ticket-pack-builder` runs if ticketing is missing or weak.
5. `project-skill-bootstrap` creates or repairs local skills.
6. `scafforge-audit` audits the resulting workflow.
7. `handoff-brief` publishes restart state.

### Managed repair or update flow

Use this path when a repo is already Scafforge-managed or otherwise OpenCode-oriented and mainly needs workflow-contract correction, managed-surface replacement, or process-version refresh:

1. `scaffold-kickoff` decides this is managed repair or update work.
2. `scafforge-repair` runs for safe workflow repairs and managed-surface refresh; it must escalate instead of auto-applying intent-changing workflow changes.
3. `project-skill-bootstrap` repairs local skills if needed.
4. `opencode-team-bootstrap` follows only if project-specific `.opencode/` drift remains.
5. `agent-prompt-engineering` reruns when regenerated skills or agents changed prompt behavior.
6. `ticket-pack-builder` repairs backlog state if needed.
7. `handoff-brief` publishes restart state.

### Pivot flow

Use this path when a repo needs a midstream feature, design, architecture, or workflow change that alters canonical truth:

1. `scaffold-kickoff` decides this is pivot work.
2. `scafforge-pivot` updates canonical brief truth and emits a stale-surface map.
3. `project-skill-bootstrap` reruns only if repo-local skills changed.
4. `opencode-team-bootstrap` follows only if team or tool surfaces changed.
5. `agent-prompt-engineering` reruns only if prompt behavior changed.
6. `ticket-pack-builder` repairs lineage when tickets must be refined, reopened, superseded, or reconciled.
7. `scafforge-repair` runs only if the pivot also exposed managed workflow drift.
8. `handoff-brief` publishes restart state.

### Diagnosis or review flow

Use this path when a repo needs read-only diagnosis, evidence validation, or the four-report diagnosis pack:

1. `scaffold-kickoff` decides this is diagnosis or review work.
2. `scafforge-audit` validates findings and owns full diagnosis-pack generation on every audit run.
3. If package defects or prevention work are required, the user manually carries the diagnosis pack into the Scafforge dev repo.
4. Package changes land here before any subject-repo repair run.
5. The user runs exactly one fresh subject-repo audit as post-package revalidation against the updated package.
6. `scafforge-repair` runs only if that revalidation pack no longer requires package work first.
7. `ticket-pack-builder` follows up when remediation tickets are needed.
8. `handoff-brief` publishes restart state when a closeout surface is needed.

## Product contract refinements

These refinements govern the package contract and implementation priorities:

- intake is opportunistic first: scan messy docs, notes, and fragmented inputs before normalizing them into a canonical brief
- meaningful ambiguity must be converted into a batched decision packet and asked, not silently assumed
- the default output remains one full orchestration OpenCode scaffold
- `scaffold-kickoff` remains the single public entrypoint for greenfield, retrofit, pivot, managed-repair or update, and diagnosis or review flows
- the greenfield path is one-shot: one batched blocking-decision round, one uninterrupted same-session generation pass, then direct handoff into development
- the greenfield handoff must be immediately continuable: one legal next move, one named owner, no bootstrap-first ambiguity, and zero unresolved stack-specific execution or canonical-reference failures
- the generated repo must have a structured truth hierarchy with exact canonical owners for facts, queue state, transient workflow state, artifacts, provenance, and restart surfaces
- the generated repo must always expose one legal next move with one named owner and one blocker return path
- the initial backlog should be implementation-ready where decisions are resolved, while unresolved major choices become explicit blocked or decision tickets instead of fabricated detail
- `scafforge-audit` owns read-only diagnosis, review validation, and full diagnosis-pack generation on every audit run
- `scafforge-audit` should emit code-quality findings for stack-specific execution and canonical reference-integrity failures, not only workflow-surface drift
- `scafforge-repair` should consume audit outputs, apply safe repairs non-destructively, continue into required project-specific regeneration steps, create canonical remediation tickets for source follow-up, and escalate intent-changing repairs
- `scafforge-pivot` should update canonical truth first, emit a stale-surface map, and route only the affected downstream refresh steps
- post-repair verification must prove both current-state cleanliness and causal-regression coverage whenever the repair basis was transcript-backed
- package-level PR evidence intake should be folded into `scafforge-audit` instead of surviving as a separate primary skill
- standalone refinement routing should not remain as a package-level flow
- managed-surface process replacement must leave explicit version and verification state so the generated repo can tell when its workflow contract changed
- cross-host installability should come from adapter packaging and bootstrap flows, not by making the generated output multi-host

## Canonical generated-repo truth hierarchy

The generated repo should converge on these canonical roles:

- `docs/spec/CANONICAL-BRIEF.md` owns durable project facts, constraints, accepted decisions, and unresolved questions
- `tickets/manifest.json` owns machine queue state
- `tickets/BOARD.md` is the derived human queue board
- `.opencode/state/workflow-state.json` owns transient stage, approval, and process-version state
- `.opencode/state/artifacts/` plus manifest-backed registration own stage proof
- `.opencode/meta/bootstrap-provenance.json` owns provenance for scaffold, later synthesis, and repairs
- `START-HERE.md` is the derived restart surface

Derived restart surfaces must agree with canonical manifest and workflow state. They do not outrank them.

## Package Backlog Contract

The package uses `tickets/` for planning and implementation sequencing.

Rules:
- `tickets/manifest.json` tracks the package backlog and current focus ticket
- `tickets/BOARD.md` is a derived view for humans
- ticket markdown files contain the actual implementation instructions, files to update, and verification steps
- the package backlog must not depend on package-root generated-repo runtime state
- planning changes must keep `tickets/manifest.json`, `tickets/BOARD.md`, and the ticket markdown in sync
- if a ticket changes generated-repo behavior, the corresponding package source or template asset must be named in the ticket itself

## Implementation and PR Execution

Implementation in this repository must be reviewable in small PRs.

Rules:
- branch from `main`
- use one PR per approved ticket bundle in `IMPLEMENTATION-HANDOFF.md`
- keep branch scope aligned to the listed tickets; do not smuggle unrelated refactors into a PR
- validate the touched surfaces before review
- keep validator-required contract text and real package behavior aligned in the same PR
- use the reviewer checklist in `IMPLEMENTATION-HANDOFF.md` before marking a PR ready

## Skill Boundary Rules

### `scaffold-kickoff`

The conductor.

It should:
- classify the run type
- sequence downstream skills
- remain the single public entrypoint
- enforce required outputs
- avoid duplicating scaffold logic itself

It should not become a second scaffold engine.

### `spec-pack-normalizer`

Owns canonical brief creation.

It should not scaffold files or invent a ticket system.
It should emit the ambiguity packet and backlog-readiness signal that downstream scaffold and ticket steps depend on.

### `repo-scaffold-factory`

Owns the base template and structural rendering.

It should remain the single source of truth for scaffold assets.

### `opencode-team-bootstrap`

Owns agent team design for the generated project.

In a greenfield flow, this runs after `repo-scaffold-factory` generates generic agent templates and after the repo-local skill pack exists, so agent skill allowlists can reference only generated local skills that are already present.

In a retrofit flow, this adds or repairs the `.opencode/` operating layer when the repo already exists.

### `ticket-pack-builder`

Owns ticket pack structure.

It must support:
- bootstrap mode during the first full-cycle scaffold
- refine mode later for backlog expansion or regeneration
- remediation follow-up where repair or audit needs explicit source-layer ticket output

It should not be treated as an alternate scaffold root.
It should convert unresolved major choices into explicit blocked or decision tickets rather than guessing at implementation detail.

### `project-skill-bootstrap`

Owns project-local skill generation.

It must support:
- one full greenfield pass that populates the baseline workflow pack and any required synthesized local skills
- targeted repair or regeneration later when an existing repo needs local-skill fixes

It should not blindly copy generic internet skills into the repo.
It should keep heavier orchestration packs thin or lazy-activated unless project evidence justifies more depth.

### `agent-prompt-engineering`

Owns prompt hardening, not overall flow control.

It remains a required step in the standard greenfield scaffold chain even when the resulting hardening pass is light.

### `scafforge-audit`

Owns workflow diagnosis, review validation, and diagnosis-pack generation.

It must remain read-only.
It should validate PR or review evidence against the actual repo before treating anything as canonical.
It should emit code-quality findings for stack-specific execution and canonical reference-integrity failures, not just workflow-surface drift.

### `scafforge-repair`

Owns workflow repair execution and post-audit follow-up.

It should consume audit outputs, apply safe managed-surface repairs, leave explicit provenance and verification state, record backup and diff summaries, and create remediation tickets when source-layer follow-up remains.

### `scafforge-pivot`

Owns pivot classification and bounded downstream refresh routing.

It should update canonical truth first, emit a stale-surface map, and reuse repair or ticket machinery where needed without becoming a second scaffold or repair engine.

### `handoff-brief`

Owns the restart surface and closeout summary, not planning.

## Public Skill Discovery Policy

Scafforge may inspect public skill ecosystems and public documentation, but it must not confuse discovery with deployment.

Allowed:
- search public skill sources for patterns
- inspect project or framework documentation
- compare multiple candidate workflows
- synthesize a project-local skill based on evidence
- cite the evidence source in package notes when useful

Not allowed by default:
- auto-install random external skills directly into generated repos
- create local skills that merely paraphrase docs with no procedural value
- create multiple overlapping local skills with fuzzy boundaries
- adopt public skill assumptions without checking whether they match the project stack

## Local Skill Synthesis Rules

When generating project-local skills:

1. Start with the smallest workflow pack that keeps the repo usable.
2. Prefer project evidence over generic best-practice prose.
3. Prefer procedure over reference dumping.
4. Synthesize from docs and external patterns only when the result is clearly repo-specific.
5. Keep the number of local skills low enough that a weaker model can navigate them.
6. Add or revise skills only when they reduce ambiguity, not just because more skills feel impressive.

## Editing Priorities

When editing this package, prioritize in this order:

1. correctness of the generated scaffold
2. correctness of the one-cycle workflow contract
3. package-vs-output boundary discipline
4. restart and mutation authority coherence
5. OpenCode compatibility of the generated output
6. clarity of skill boundaries
7. local skill synthesis quality
8. documentation polish

## What Not To Reintroduce

Do not add back:
- package-root generated-repo runtime state for planning convenience
- personal home-directory sync logic as core package behavior
- Codex self-improvement workflows as part of the core product
- unrelated generic utility skills in the core pack
- duplicate scaffold logic across multiple skills
- hidden workflow state spread across too many files
- unconditional public skill imports
- a second package-side mutation engine that shadows runtime-owned ticket or restart logic

## Maintenance Checklist

When changing the package:

- verify the skill chain still makes sense end to end
- verify `scaffold-kickoff` still describes the real default workflow
- verify bootstrap-mode ticket generation happens in the full-cycle path
- verify stack adapter registry and bootstrap guidance still cover the intended Tier 1 stacks
- verify post-repair verification still uses stack-specific execution and reference-integrity checks where available
- verify audit still produces code-quality findings for non-Python stacks, not only workflow findings
- verify diagnosis, mutation, restart publication, and pivot-state ownership remain single-owner domains
- verify package-root planning surfaces have not drifted back into generated-repo semantics
- verify generated template paths still match current OpenCode conventions
- verify any runtime assumptions about tools or plugins are still current
- remove stale host-specific wording from core skills and docs
- verify the package still meets the competence contract in `references/competence-contract.md`

## Definition Of Done For Package Changes

A package change is not done until:

- the skill boundaries remain coherent
- the default flow still completes in one orchestrated cycle
- generated output remains OpenCode-oriented and structurally valid
- the package-vs-output boundary remains intact
- docs, templates, validators, and harnesses agree with the actual package behavior
- obvious legacy wording, hidden writers, or orphaned assumptions are removed
