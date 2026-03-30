# AGENTS.md

This file governs work **inside the Scafforge package repository itself**.

Scafforge is not the generated project. It is the generator, template source, orchestration pack, and process contract used by a host agent to build a generated project.

## Mission

Maintain a host-agnostic scaffold package that can turn raw project inputs into a deterministic, signposted, OpenCode-oriented repo operating framework.

The package should help even weaker models operate inside a generated project without having to reinvent the workflow every session.
That weaker-model-first bias is intentional: stronger hosts should still work well, but the generated workflow should stay robust even when the model needs tighter structure and narrower delegation boundaries.

## Core operating model

There are two different things in play.

### Host layer
How a CLI host uses this package.

Examples:
- OpenCode as host
- another compatible host agent
- later adapter-specific hosts

### Output layer
What the generated repo looks like.

The default output is intentionally OpenCode-oriented and may include:
- root `AGENTS.md`
- `opencode.jsonc`
- `.opencode/agents/`
- `.opencode/tools/`
- `.opencode/plugins/`
- `.opencode/commands/`
- `.opencode/skills/`
- `.opencode/state/`
- signposted docs and ticket surfaces

Do not collapse these layers together.

## First principles

1. Keep core package behavior host-agnostic unless a file is clearly adapter-specific.
2. Keep the default generated repo OpenCode-oriented.
3. Prefer one orchestrated full-cycle build over a base-pass-plus-manual-enrichment design.
4. Prefer deterministic workflow contracts over verbose prompting.
5. Preserve clear boundaries between skills.
6. Generate the smallest surface compatible with the selected profile; for the default full profile, keep heavier packs thin or lazy-activated until they are actually needed.
7. Never treat public skill discovery as permission to auto-install random skills.

The package competence bar is defined in `references/competence-contract.md`. If the generated workflow leaves the operator unsure what the next legal move is, treat that as a Scafforge defect.

## Default scaffold spine

These skills are the current backbone and should remain coherent as a chain:

- `scaffold-kickoff`
- `spec-pack-normalizer`
- `repo-scaffold-factory`
- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`
- `ticket-pack-builder`
- `handoff-brief`

`scafforge-audit`, `scafforge-repair`, and `scafforge-pivot` remain separate post-generation lifecycle skills.
Optional extension skills may exist outside this default scaffold spine when they solve later host-side workflow needs without polluting the scaffold chain. These should stay clearly marked as optional.

## Canonical workflow contract

### Greenfield full-cycle scaffold

The default route should be:

1. `scaffold-kickoff` decides this is a greenfield build
2. `spec-pack-normalizer` produces a canonical brief
3. `repo-scaffold-factory` renders the base scaffold
4. `project-skill-bootstrap` completes the full greenfield local-skill pass
5. `opencode-team-bootstrap` designs the project-specific agent team
6. `agent-prompt-engineering` runs the required same-session prompt-hardening pass
7. `ticket-pack-builder` runs in bootstrap mode
8. the kickoff-owned immediate-continuation verification gate proves the repo is truthful and immediately runnable
9. `handoff-brief` refreshes the restart surface

A greenfield scaffold allows one batched blocking-decision round and then completes in one uninterrupted same-session pass. No second Scafforge generation pass is required before development begins. Greenfield completion requires immediate continuation proof before handoff publication, not only surface agreement.
The package still carries one explicit temporary contract smell: `project-skill-bootstrap` and `opencode-team-bootstrap` form a dependency seam, and the current order stays in place until Scafforge introduces a real minimal-operable-versus-specialization split.

## Product contract refinements

These refinements now govern implementation of the package contract:

- intake is **opportunistic first**: scan messy docs, notes, and fragmented inputs before normalizing them into a canonical brief
- meaningful ambiguity must be converted into a **batched decision packet** and asked, not silently assumed
- the default output remains **one full orchestration OpenCode scaffold**
- `scaffold-kickoff` remains the **single public entrypoint** for greenfield, retrofit, pivot, managed-repair/update, and diagnosis/review flows; downstream skills are routing targets, not user-facing starting points
- the greenfield path is **one-shot**: one batched blocking-decision round, one uninterrupted same-session generation pass, then direct handoff into development
- the greenfield handoff must be **immediately continuable**: one legal first move, one named owner, and no bootstrap-first ambiguity across restart, prompt, tool, and workflow surfaces
- the generated repo must have a **structured truth hierarchy** with exact canonical owners for facts, queue state, transient workflow state, artifacts, provenance, and restart surfaces
- the generated repo must always expose **one legal next move** with one named owner and one blocker return path
- the initial backlog should be **implementation-ready where decisions are resolved**, while unresolved major choices become explicit blocked or decision tickets instead of fabricated detail
- `scafforge-audit` should own read-only diagnosis, review validation, and full diagnosis-pack generation on every audit run
- `scafforge-repair` should consume audit outputs, apply safe repairs, continue into required project-specific regeneration steps, and escalate intent-changing repairs
- `scafforge-pivot` should update canonical truth first, emit a stale-surface map, and route only the affected downstream refresh steps
- post-repair verification must prove both current-state cleanliness and causal-regression coverage whenever the repair basis was transcript-backed
- package-level PR evidence intake should be folded into `scafforge-audit` instead of surviving as a separate primary skill
- standalone refinement routing should not remain as a package-level flow
- managed-surface process replacement must leave explicit version and verification state so the generated repo can tell when its workflow contract changed
- cross-host installability should come from **adapter packaging and bootstrap flows**, not by making the generated output multi-host

## Canonical generated-repo truth hierarchy

The generated repo should converge on these canonical roles:

- `docs/spec/CANONICAL-BRIEF.md` owns durable project facts, constraints, accepted decisions, and unresolved questions
- `tickets/manifest.json` owns machine queue state
- `tickets/BOARD.md` is the derived human queue board
- `.opencode/state/workflow-state.json` owns transient stage, approval, and process-version state
- `.opencode/state/artifacts/` plus manifest-backed registration own stage proof
- `.opencode/meta/bootstrap-provenance.json` owns provenance for scaffold, later synthesis, and repairs
- `START-HERE.md` is the derived restart surface

### Retrofit flow

Use the lighter path when a repo already exists and mainly needs an OpenCode operating layer:

1. `scaffold-kickoff` decides this is retrofit work
2. `spec-pack-normalizer` runs only if the input context is fragmented
3. `opencode-team-bootstrap` adds or repairs `.opencode/`
4. `ticket-pack-builder` runs if ticketing is missing or weak
5. `project-skill-bootstrap` creates or repairs local skills
6. `scafforge-audit` audits the resulting workflow
7. `handoff-brief` publishes restart state

### Managed repair / update flow

Use this path when a repo is already Scafforge-managed or otherwise OpenCode-oriented and mainly needs workflow-contract correction, managed-surface replacement, or process-version refresh:

1. `scaffold-kickoff` decides this is managed repair/update work
2. `scafforge-repair` runs for safe workflow repairs and managed-surface refresh
3. `project-skill-bootstrap` repairs local skills if needed
4. `opencode-team-bootstrap` follows up only if project-specific `.opencode/` drift remains
5. `agent-prompt-engineering` reruns when regenerated skills or agents changed prompt behavior
6. `ticket-pack-builder` repairs backlog state if needed
7. `handoff-brief` publishes restart state

### Pivot flow

Use this path when a repo needs a midstream feature, design, architecture, or workflow change that alters canonical truth:

1. `scaffold-kickoff` decides this is pivot work
2. `scafforge-pivot` updates canonical brief truth and emits a stale-surface map
3. `project-skill-bootstrap` reruns only if repo-local skills changed
4. `opencode-team-bootstrap` follows only if team or tool surfaces changed
5. `agent-prompt-engineering` reruns only if prompt behavior changed
6. `ticket-pack-builder` repairs lineage when tickets must be refined, reopened, superseded, or reconciled
7. `scafforge-repair` runs only if the pivot also exposed managed workflow drift
8. `handoff-brief` publishes restart state

### Diagnosis / review flow

Use this path when a repo needs read-only diagnosis, evidence validation, or the four-report diagnosis pack:

1. `scaffold-kickoff` decides this is diagnosis/review work
2. `scafforge-audit` validates findings and emits the diagnosis outputs
3. if package defects or prevention work are required, the user manually carries the diagnosis pack into the Scafforge dev repo
4. Scafforge package changes land there before any subject-repo repair run
5. the user runs exactly one fresh subject-repo audit as post-package revalidation against the updated package
6. `scafforge-repair` runs only if that revalidation pack no longer requires package work first
7. `ticket-pack-builder` follows up when remediation tickets are needed
8. `handoff-brief` publishes restart state when a closeout surface is needed

### Review / QA flow

Implementation, review, security, and QA procedure should be emitted as generated repo-local skills under `.opencode/skills/`, not carried as top-level Scafforge package skills.

## Skill boundary rules

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
It should also emit the ambiguity packet and backlog-readiness signal that downstream scaffold and ticket steps depend on.

### `repo-scaffold-factory`
Owns the base template and structural rendering.

It should remain the single source of truth for scaffold assets.

### `opencode-team-bootstrap`
Owns agent team design for the generated project.

In a greenfield flow, this runs after `repo-scaffold-factory` generates generic agent templates. It analyzes the project type and stack from the canonical brief, then customizes all agents to be project-specific. This includes adding domain-specific implementers, rewriting generic prompts, and reviewing tools/plugins for project-specific additions.
In a greenfield flow, this runs after the repo-local skill pack already exists, so agent skill allowlists can reference only generated local skills that are already present.

In a retrofit flow, this adds or repairs the `.opencode/` operating layer when the repo already exists.

### `ticket-pack-builder`
Owns ticket pack structure.

It must support:
- bootstrap mode during the first full-cycle scaffold
- refine mode later for backlog expansion or regeneration

It should not be treated as an alternate scaffold root.
It should convert unresolved major choices into explicit blocked or decision tickets rather than guessing at implementation detail.

### `project-skill-bootstrap`
Owns project-local skill generation.

It must support:
- one full greenfield pass that populates the baseline workflow pack and any required synthesized local skills
- targeted repair or regeneration later when an existing repo needs local-skill fixes

It should not blindly copy generic internet skills into the repo.
It should keep heavier orchestration packs thin or lazy-activated unless project evidence justifies more depth.
It owns output-repo review and QA local skills such as `review-audit-bridge` when those procedures belong inside the generated `.opencode/skills/` layer.

### `agent-prompt-engineering`
Owns prompt hardening, not overall flow control.

It remains a required step in the standard greenfield scaffold chain even when the resulting hardening pass is light.
In greenfield generation, it runs in the same session and finishes before ticket bootstrap and handoff.

### `scafforge-audit`
Owns workflow diagnosis, review validation, and diagnosis-pack generation.

It must remain read-only.
It should validate PR or review evidence against the actual repo before treating anything as a canonical finding.

### `scafforge-repair`
Owns workflow repair execution and post-audit follow-up.

It should consume audit outputs, apply safe managed-surface repairs, and leave explicit provenance and verification state.

### `scafforge-pivot`
Owns pivot classification and bounded downstream refresh routing.

It should update canonical truth first, emit a stale-surface map, and reuse repair or ticket machinery where needed without becoming a second scaffold or repair engine.

### `handoff-brief`
Owns the restart surface and closeout summary, not planning.

## Public skill discovery policy

Scafforge may inspect public skill ecosystems and public documentation, but it must not confuse **discovery** with **deployment**.

### Allowed

- search public skill sources for patterns
- inspect project/framework documentation
- compare multiple candidate workflows
- synthesize a project-local skill based on evidence
- cite the evidence source in package notes when useful

### Not allowed by default

- auto-install random external skills directly into generated repos
- create local skills that merely paraphrase docs with no procedural value
- create multiple overlapping local skills with fuzzy boundaries
- adopt public skill assumptions without checking whether they match the project stack

## Local skill synthesis rules

When generating project-local skills:

1. Start with the smallest workflow pack that keeps the repo usable.
2. Prefer project evidence over generic best-practice prose.
3. Prefer procedure over reference dumping.
4. Synthesize from docs and external patterns only when the result is clearly repo-specific.
5. Keep the number of local skills low enough that a weaker model can navigate them.
6. Add or revise skills only when they reduce ambiguity, not just because more skills feel impressive.

## Editing priorities

When editing this package, prioritize in this order:

1. correctness of the generated scaffold
2. correctness of the one-cycle workflow contract
3. OpenCode compatibility of the generated output
4. clarity of skill boundaries
5. local skill synthesis quality
6. documentation polish

## What not to reintroduce

Do not add back:

- personal home-directory sync logic as core package behavior
- Codex self-improvement workflows as part of the core product
- unrelated generic utility skills in the core pack
- duplicate scaffold logic across multiple skills
- hidden workflow state spread across too many files
- unconditional public skill imports

## Maintenance checklist

When changing the package:

- verify the skill chain still makes sense end to end
- verify `scaffold-kickoff` still describes the real default workflow
- verify bootstrap-mode ticket generation happens in the full-cycle path
- verify project-skill synthesis rules are still conservative and evidence-based
- verify generated template paths still match current OpenCode conventions
- verify any runtime assumptions about tools/plugins are still current
- remove stale host-specific wording from core skills and docs
- verify the package still meets the competence contract in `references/competence-contract.md`

## Definition of done for package changes

A package change is not done until:

- the skill boundaries remain coherent
- the default flow still completes in one orchestrated cycle
- generated output remains OpenCode-oriented and structurally valid
- docs and templates agree with the actual package behavior
- obvious legacy wording or orphaned assumptions are removed
