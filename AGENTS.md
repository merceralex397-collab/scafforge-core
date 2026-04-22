# AGENTS.md

This file governs work inside the Scafforge package repository itself.

Scafforge is not the generated project. It is the generator, template source, validation harness, and workflow contract used by a host agent to build, audit, repair, or update a generated project repo.

That distinction is law in this repository. Do not collapse package-repo surfaces and generated-repo surfaces together.

## Mission

Maintain a host-agnostic scaffold package that can turn raw project inputs into a deterministic, signposted, OpenCode-oriented repo operating framework.

The product bias remains weak-model first. Stronger models should still work well, but the package exists to make weaker or cheaper models reliable through deterministic workflow contracts, narrow role boundaries, explicit truth ownership, and proof-backed restart guidance.

The package competence bar is defined in [references/competence-contract.md](references/competence-contract.md). If the generated workflow stops exposing one legal next move, treat that as package evidence, not user error.

## Documentation routing

Use the package docs this way:

- `README.md` for orientation and the current lifecycle summary
- `USERGUIDE.md` for operator routing and lightweight context acquisition
- `architecture.md` for the package structure and adjacent-system boundaries
- `references/*.md` for durable contract detail
- [references/documentation-authority-map.md](references/documentation-authority-map.md) for the current source-of-truth map across package, planning, and generated-template docs

Root docs should stay short and authoritative. Detailed rules belong in the references or the relevant skill docs.

## Repo identity

There are three layers to keep separate.

### Package layer

This repository contains:

- package skills under `skills/`
- generated-template assets under `skills/repo-scaffold-factory/assets/project-template/`
- validation and proof harnesses under `scripts/` and `tests/`
- contract references under `references/`
- copied diagnosis evidence under `active-audits/`
- active package implementation planning under `active-plans/`

### Output layer

This is what Scafforge generates for a subject repo.

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
- `tickets/`
- `docs/spec/CANONICAL-BRIEF.md`
- `START-HERE.md`

Do not import output-layer runtime state into the package root. If generated-repo behavior needs to change, change package code or template assets.

### Adjacent systems

Some systems are intentionally separate from both the package layer and generated output layer.

Examples:

- an adjacent spec factory repo or workspace that owns intake, drafting, review, approval, and approved-brief publication
- an adjacent orchestration service that owns job progression and runtime invocation
- an adjacent control plane or ChatGPT-facing ingress surface

These systems may consume Scafforge contracts, but they must not smuggle their runtime state or authority into the package root.

An adjacent orchestration service may trigger `scaffold-kickoff` from a persisted approved-brief bundle, schedule downstream PR phases, and own pause, retry, and resume controls. It must stay read-only with respect to generated `tickets/manifest.json` and `.opencode/state/workflow-state.json`, and it must derive wrapper state from package and GitHub evidence instead of inventing repo truth in the UI.

An adjacent control plane may render orchestration job state, package investigations, and provider/router summaries, but it must route approvals, overrides, pause/resume, retry, merge, and policy mutations through backend APIs. If auth, trust, or connectivity is ambiguous, the control plane must fail closed to read-only and must not fall back to direct WSL, SSH, GitHub, or repo-local shell mutation.

## Package working mode

Scafforge package work is not driven by generated-repo runtime state.

In this repo:

- `active-plans/README.md` is the canonical portfolio index
- each numbered `active-plans/NN-kebab-case/README.md` is the authoritative implementation plan for that plan
- `active-plans/FULL-REPORT.md` is the cross-plan summary and sequencing rationale
- `active-plans/docscleanup.md` is the planning-surface placement policy
- `active-plans/WORK-JOURNAL.md` is historical provenance, not current authority
- `active-plans/codexinstructions.md` is a supporting execution guide, not a canonical contract source
- package-root `.opencode/` runtime state must not be created to manage package work
- package-root `tickets/manifest.json` and `tickets/BOARD.md` are not current package planning surfaces and must not be reintroduced as shadow workflow state

## Standing documentation rule

Every contract-changing PR must update the affected root docs, references, generated-template docs, and validator expectations in the same change set. Do not treat documentation as final polish.

Before review:

1. Identify which truth domains changed.
2. Update the affected root docs and the canonical reference for each changed truth domain.
3. Update any touched generated-template docs or local-skill guidance that would otherwise inherit stale wording.
4. Run the contract validator after changing validator-pinned docs, then run the wider package validation stack.
5. Record remaining gaps or environment blockers explicitly instead of implying the docs already converge.

`AGENTS.md` is the durable policy home for this rule. `active-plans/README.md` and `active-plans/docscleanup.md` are program-level reminders and formatting guidance only.

## Authority baseline

The package-wide authority map is documented in [references/authority-adr.md](references/authority-adr.md), and the invariant checklist lives in [references/invariant-catalog.md](references/invariant-catalog.md).

- `scafforge-audit` owns diagnosis disposition.
- The generated runtime workflow layer owns canonical repo mutation.
- An adjacent orchestration service owns job progression, PR automation, idempotency or retry state, and pause or resume controls while staying read-only over generated canonical repo truth.
- `scafforge-pivot` owns pivot-state persistence.
- `handoff-brief` owns restart publication from the verified final snapshot.
- `agent-prompt-engineering` owns contract alignment for prompts, workflow docs, and generated behavior.

Repair-side restart rendering and raw workflow mutation were the first duplicate-authority seam to collapse. Later work should cite the ADR and invariant catalog directly instead of restating the owner map ad hoc.

## Canonical package validation commands

The package-level validation entrypoints are:

- `npm run validate:contract`
- `npm run validate:smoke`
- `python3 scripts/integration_test_scafforge.py`
- `python3 scripts/validate_gpttalker_migration.py`

Use `python3` or `sys.executable` for Python entrypoints in repository guidance. Do not assume a `python` shim exists or points to the correct interpreter.

## Active audits and plans

`active-audits/` holds diagnosis packs copied from generated repositories for package-level investigation.

- each generated repo gets its own named subfolder
- copied raw evidence under `raw/` stays immutable
- canonical package-side sidecars include `evidence-manifest.json`, `investigator/report.md`, `investigator/report.json`, `fixer/package-fix-record.json`, and `revalidation/resume-ready.json`
- archive indexes for copied logs, session files, or database exports must stay derived and non-authoritative relative to the copied raw evidence and sidecar manifests

`active-plans/` holds the live package implementation program.

- numbered folders are the canonical plans
- plan-local references stay under that folder's `references/`
- `_source-material/` stays active supporting material, not a disposal queue
- root-level files under `active-plans/` are portfolio-wide routing, reporting, provenance, or execution guidance

## Skill evolution and distillation

Skill evolution is a bounded package lifecycle, not permissionless skill accumulation. The durable rules live in [references/skill-evolution-policy.md](references/skill-evolution-policy.md), [references/external-source-evaluation-rubric.md](references/external-source-evaluation-rubric.md), [references/rejected-sources.md](references/rejected-sources.md), and [references/skill-validation-policy.md](references/skill-validation-policy.md).

- audit-derived package evidence enters skill evaluation only after `scafforge-audit` and the `active-audits/` sidecars accept it
- copied bundles, public skill ecosystems, and adjacent repos are research inputs only; blind import into Scafforge or generated repos is forbidden
- distill external concepts into Scafforge-owned language with explicit provenance, purpose, and validation expectations
- keep package skills, repo-local synthesized skills, and adjacent skill repos as separate layers with no shared hidden authority
- prefer sharpening an existing skill, prompt contract, or workflow reference before adding a new package skill
- downstream skill refresh must route through explicit greenfield generation or `scafforge-repair` follow-on stages; do not silently mutate subject repos because package policy improved
- every new or materially re-scoped package skill must register in `skills/skill-flow-manifest.json` and pass the named skill-governance checks in `npm run validate:contract`

## First principles

1. Keep core package behavior host-agnostic unless a file is clearly adapter-specific.
2. Keep the default generated repo OpenCode-oriented.
3. Prefer one orchestrated full-cycle build over a base-pass-plus-manual-enrichment design.
4. Prefer deterministic workflow contracts over verbose prompting.
5. Preserve clear ownership boundaries between diagnosis, mutation, restart publication, and proof.
6. Generate the smallest surface compatible with the selected profile; keep heavier packs thin or lazy-activated until they are actually needed.
7. Never treat public skill discovery as permission to auto-install random skills.
8. Treat package-root generated-repo simulation as a defect unless it lives under a fixture or a template path.

## Default scaffold spine

These skills are the backbone of the default greenfield path:

- `scaffold-kickoff`
- `spec-pack-normalizer`
- `repo-scaffold-factory`
- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`
- `ticket-pack-builder`
- `handoff-brief`

`asset-pipeline` is an optional extension for game or asset-heavy repos. `scafforge-audit`, `scafforge-repair`, and `scafforge-pivot` are separate post-generation lifecycle skills.

The greenfield proof chain includes environment bootstrap detection, bootstrap-blocker persistence and routing, stack-specific execution proof where available, and reference-integrity verification before handoff.

The shipped package still carries one explicit temporary contract smell: `project-skill-bootstrap` and `opencode-team-bootstrap` form a dependency seam, and the current order remains until Scafforge has a real minimal-operable-versus-specialization split.

## Canonical workflow contract

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

Greenfield output must be immediately continuable and immediately continuable means the repo is truthful enough to expose one legal next move without bootstrap-first ambiguity.

### Retrofit flow

Use this lighter path when a repo already exists and mainly needs an OpenCode operating layer:

1. `scaffold-kickoff` decides this is retrofit work.
2. `spec-pack-normalizer` runs only if the input context is fragmented.
3. `opencode-team-bootstrap` adds or repairs `.opencode/`.
4. `project-skill-bootstrap` creates or repairs local skills.
5. `ticket-pack-builder` runs if ticketing is missing or weak.
6. `scafforge-audit` audits the resulting workflow.
7. `handoff-brief` publishes restart state.

### Managed repair or update flow

Use this path when a repo already has Scafforge-managed or OpenCode-oriented workflow surfaces and mainly needs managed repair:

1. `scaffold-kickoff` decides this is managed repair or update work.
2. `scafforge-repair` runs for safe workflow repairs and managed-surface refresh.
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
- `scaffold-kickoff` remains the single public entrypoint for greenfield, retrofit, pivot, managed repair or update, and diagnosis or review flows
- approved factory briefs are valid upstream inputs only when their handoff bundle is persisted
- the greenfield handoff must be immediately continuable: one legal next move, one named owner, no bootstrap-first ambiguity, and zero unresolved stack-specific execution or canonical-reference failures
- what "done" means per repo family must be explicit, machine-readable, and tied to proof artifacts instead of agent self-report
- the generated repo must expose a structured truth hierarchy with exact canonical owners for facts, queue state, transient workflow state, artifacts, provenance, and restart surfaces
- orchestration-owned phase grouping, PR numbers, reviewer assignment, and package-change wait states must stay outside generated canonical repo state
- managed-surface process replacement must leave explicit version and verification state so the generated repo can tell when its workflow contract changed
- post-repair verification must prove both current-state cleanliness and causal-regression coverage whenever the repair basis was transcript-backed
- the package still carries one explicit temporary contract smell until a minimal-operable-versus-specialization split exists between minimal managed surfaces and later specialization

## Canonical generated-repo truth hierarchy

Generated repos should converge on these canonical roles:

| Surface | Owns |
| --- | --- |
| `docs/spec/CANONICAL-BRIEF.md` | Durable project facts, constraints, accepted decisions, and unresolved questions |
| `tickets/manifest.json` | Machine queue state and registered artifact metadata |
| `tickets/BOARD.md` | Derived human queue board |
| `.opencode/state/workflow-state.json` | Transient stage, approval, and process-version state |
| `.opencode/state/artifacts/` plus manifest-backed registration | Canonical stage artifact bodies and registry state |
| `.opencode/meta/bootstrap-provenance.json` | Scaffold provenance, synthesis history, and repair history |
| `START-HERE.md` plus other restart surfaces | Derived restart publication only |

Derived restart surfaces must agree with canonical manifest and workflow state. They do not outrank them.

## Skill boundary reminders

Detailed skill behavior belongs in `skills/*/SKILL.md`. Package-wide reminders:

- `scaffold-kickoff` is the conductor, not a second scaffold engine.
- `spec-pack-normalizer` owns canonical brief creation, not ticketing or scaffold rendering.
- `repo-scaffold-factory` is the single source of truth for managed scaffold assets.
- `project-skill-bootstrap` owns repo-local skill generation.
- `opencode-team-bootstrap` owns project-specific `.opencode/` design.
- `agent-prompt-engineering` owns prompt hardening and contract alignment.
- `ticket-pack-builder` owns backlog and remediation-ticket structure.
- `scafforge-audit` remains read-only and owns diagnosis disposition.
- `scafforge-repair` owns safe managed-surface repair and repair-side routing.
- `scafforge-pivot` owns pivot-state persistence and bounded downstream refresh routing.
- `handoff-brief` owns restart publication from the verified final snapshot.

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

## Maintenance checklist

When changing the package:

1. Verify the skill chain still makes sense end to end.
2. Verify `scaffold-kickoff` still describes the real default workflow.
3. Verify bootstrap-mode ticket generation still happens in the full-cycle path.
4. Verify stack-adapter coverage, bootstrap guidance, and proof-host expectations still match `references/stack-adapter-contract.md`.
5. Verify post-repair verification still uses stack-specific execution and reference-integrity checks where available.
6. Verify audit still produces code-quality findings for non-Python stacks, not only workflow findings.
7. Verify diagnosis, mutation, restart publication, and pivot-state ownership remain single-owner domains.
8. Verify generated-template docs, generated template paths, and runtime/tool assumptions still match package truth in the touched areas.
9. Verify host-side validation hygiene when package skill content changed and validation depends on host-installed skill copies.
10. Verify root docs, references, validators, and touched template docs moved together in the same change set.
11. Verify the package still meets the competence contract in `references/competence-contract.md`.

## Host-side validation hygiene

When package skill content changes and you plan to validate using host-installed skills, refresh the host copies before trusting the result:

- `~/.codex/skills/`
- `~/.copilot/skills/`
- `~/.config/kilo/skills/`

This is local operator hygiene for real validation, not part of the generated package contract and not a reason to reintroduce home-directory sync logic into the core product itself.
