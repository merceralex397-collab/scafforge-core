---
name: scaffold-kickoff
description: Orchestrate the full Scafforge kickoff flow for greenfield, retrofit, pivot, managed-repair, or diagnosis/review work. Use when asked to scaffold a new repo, add the OpenCode operating layer to an existing repo, apply a midstream feature or design change, repair a Scafforge-managed workflow contract, or diagnose an in-progress project. This is the single public entrypoint and routes to the correct downstream skills automatically.
---

# Scaffold Kickoff

This is the default public entrypoint. When a user asks you to scaffold, retrofit, repair, refresh, or diagnose a Scafforge-managed project, start here and route internally.

## Decision tree

Before starting, classify the run type:

1. **Greenfield** — No repo exists yet, or the repo contains only specs, plans, or notes. Follow the full workflow below.
2. **Retrofit** — A repo with code already exists but is missing the current OpenCode operating layer. Run `spec-pack-normalizer` first if the project lacks a canonical brief, route to `opencode-team-bootstrap` to add or repair `.opencode/`, then run `project-skill-bootstrap`, continue through ticket repair as needed, and finish with `scafforge-audit`.
3. **Pivot** — A Scafforge-managed or OpenCode-oriented repo needs a midstream feature, design, architecture, or workflow change that updates canonical truth and ticket lineage. Route to `scafforge-pivot`, let it continue through only the affected downstream refresh steps, and finish with `handoff-brief`.
4. **Managed repair / update** — A Scafforge-managed or OpenCode-oriented repo already exists but needs workflow-contract repair, upgrade, or managed-surface replacement. Route directly to `scafforge-repair`, let it continue through any required project-specific regeneration or ticket follow-up, and finish with `handoff-brief`.
5. **Diagnosis / review** — An in-progress or claimed-complete repo needs full non-mutating diagnosis, codebase review, report generation, or evidence validation. Route to `scafforge-audit`.

If the repo state and the user's request do not make the run type clear, ask the user before proceeding. Do not silently choose between greenfield, retrofit, pivot, managed repair, and diagnosis/review when that choice would materially change scope.

## Full greenfield workflow

Follow these steps in order. Each step references a sibling skill. Read it at the relative path shown.

Greenfield generation has no further user-selectable submodes. After the blocking-decision round is resolved, you must complete every downstream generation skill in the same session. Do not route the initial generation pass into `scafforge-audit` or `scafforge-repair`.

### Step 1: Normalize the spec pack

Read `../spec-pack-normalizer/SKILL.md` and follow its procedure.

Scan the workspace for project inputs:
- look for `*.md` files, `docs/`, `specs/`, `plans/`, `requirements/`, `notes/`, `design/` directories
- look for pasted chats, informal notes, architecture docs, and API specs
- read everything you find

Produce a canonical brief at `docs/spec/CANONICAL-BRIEF.md` with the required schema.

### Step 2: Resolve ambiguities

Before proceeding, present the user with a batched decision packet for blocking ambiguities:
- project name, slug, and destination path
- agent prefix for generated agents
- model provider and model choices
- stack or framework choices
- any other materially divergent decision

Do not guess at blocking choices. Do not proceed until they are resolved.

### Step 3: Generate the base scaffold

Read `../repo-scaffold-factory/SKILL.md` and follow its procedure.

This has two phases:
- Phase A: run the Python script to generate the template file tree with placeholder substitution
- Phase B: customize the generated files with project-specific content from the canonical brief

### Step 4: Bootstrap project-local skills

Read `../project-skill-bootstrap/SKILL.md` and follow its greenfield procedure.

Populate the repo-local skill pack in one pass:
- rewrite the baseline skills with actual project content
- create any required synthesized skills from project evidence
- write the downstream model operating profile skill for the selected model profile

### Step 5: Design and customize the agent team

Read `../opencode-team-bootstrap/SKILL.md` and follow its procedure.

The scaffold creates generic agent templates. You must now customize them:
- rewrite agent prompts to be project-specific
- add or remove agents based on project type
- keep the topology conservative unless the brief proves disjoint domains
- reference only repo-local skills that already exist

### Step 6: Harden agent prompts

Read `../agent-prompt-engineering/SKILL.md` and follow its procedure.

This is a required same-session hardening pass in the standard greenfield scaffold flow.

### Step 7: Build the ticket backlog

Read `../ticket-pack-builder/SKILL.md` and follow its procedure in bootstrap mode.

Create implementation-ready tickets only after local skills, team topology, and prompt hardening are finalized:
- break work into implementation waves
- keep each ticket small enough for one agent session
- convert unresolved major decisions into blocked or decision tickets instead of guesses

### Step 8: Verify immediate continuation before handoff

Before you begin the handoff step, run one same-session immediate-continuation verification gate across the generated workflow surfaces:

```sh
python3 ../repo-scaffold-factory/scripts/verify_generated_scaffold.py <repo-root> --format both
```

- `docs/process/workflow.md`
- `docs/process/tooling.md`
- `tickets/README.md`
- `.opencode/tools/ticket_lookup.ts`
- `.opencode/tools/ticket_update.ts`
- `.opencode/tools/smoke_test.ts`
- `.opencode/tools/handoff_publish.ts`
- `.opencode/skills/ticket-execution/SKILL.md`
- the generated team-leader prompt

Confirm that they agree on:
- lifecycle stage order, especially `plan_review` before implementation and `smoke-test` before closeout
- `ticket_lookup.transition_guidance` as the canonical next-step explainer
- `smoke_test` as the only producer of smoke-test artifacts
- explicit ticket acceptance smoke commands as the canonical smoke scope whenever the ticket already defines an executable smoke command
- one legal first move while bootstrap proof is still missing: `environment_bootstrap`, then a fresh `ticket_lookup`
- commands as human entrypoints only, with autonomous work staying inside agents, tools, plugins, and local skills

If these surfaces disagree, fix the contract before handing off the repo.

### Step 9: Write the handoff surface

Read `../handoff-brief/SKILL.md` and follow its procedure.

Generate `START-HERE.md` with actual project state so the repo can be resumed by another agent or session.

### Step 10: Done

The scaffold is complete when all of these exist:
- `docs/spec/CANONICAL-BRIEF.md` with real project content
- `tickets/manifest.json` with implementation-ready tickets
- `tickets/BOARD.md` showing the work queue
- `.opencode/agents/` with project-specific agent prompts
- `.opencode/tools/`, `.opencode/plugins/`, `.opencode/commands/`
- `.opencode/skills/` with project-specific local skills
- `START-HERE.md` with current project state
- a first-development handoff that is valid without any later audit or repair pass

## Diagnosis / review flow

When the task is diagnosis or review of an existing project:

1. read `../scafforge-audit/SKILL.md`
2. run the audit and any requested evidence-validation review work
3. produce the four-report diagnosis pack on every audit run, redirecting the output directory when the subject repo is outside the current host's writable roots
4. if the audit identifies Scafforge package work, have the user manually copy the diagnosis pack into the Scafforge dev repo and complete those package changes first
5. if repeated diagnosis packs show the same repair-routed findings and there is no newer package or process-version change, stop and route to Scafforge package work instead of rerunning another subject-repo audit
6. route to `../scafforge-repair/SKILL.md` only after the required package changes exist and the audit still recommends repair
7. finish with `../handoff-brief/SKILL.md` when a restart surface or closeout is needed

## Pivot flow

When the task is a midstream feature, design, architecture, or workflow change:

1. read `../scafforge-pivot/SKILL.md`
2. classify the pivot and update canonical brief truth first
3. emit the stale-surface map and route only the affected refresh steps
4. use `../scafforge-repair/SKILL.md` only when managed workflow surfaces also drifted
5. finish with `../handoff-brief/SKILL.md` after post-pivot verification

## Required outputs

- a canonical brief that separates facts, assumptions, and open questions
- a decision packet that records blocking versus non-blocking ambiguities
- a scaffolded repo with README.md, AGENTS.md, START-HERE.md, docs, and tickets
- a structured truth hierarchy with clear ownership for facts, queue state, transient workflow state, artifacts, provenance, and handoff
- the OpenCode agent, command, tool, plugin, and local-skill layer customized for the specific project
- a pivot classification and stale-surface map when the run type is pivot
- a diagnosis pack when the run type is diagnosis/review
- a handoff surface that another machine or session can resume from
- a same-session immediate-continuation verification gate showing docs, tools, prompts, and local workflow skills agree on the first legal move

## Output contract

Before `scaffold-kickoff` is considered complete, the run must leave all of these behind:
- `docs/spec/CANONICAL-BRIEF.md` with resolved blocking decisions and backlog-readiness signal
- the generated repo scaffold plus customized `.opencode/` layer required by the selected run type
- explicit downstream completion or stop status for every required skill in the selected sequence
- `tickets/manifest.json`, `tickets/BOARD.md`, and `.opencode/state/workflow-state.json` aligned on the same foreground ticket
- `START-HERE.md` that is valid for immediate continuation without requiring a later audit or repair pass
- a same-session immediate-continuation verification gate across docs, tools, prompts, and workflow skills for the generated repo

## Rules

- Prefer this umbrella flow for greenfield work instead of manually starting with lower-level skills.
- Keep generated docs and prompts weak-model friendly: short sections, explicit steps, obvious source-of-truth files.
- Keep `scaffold-kickoff` as the human entrypoint even when the repo already exists; route internally to `opencode-team-bootstrap`, `scafforge-audit`, `scafforge-repair`, or another downstream skill instead of asking the user to pick the lower-level entry.
- Route midstream feature and design changes through `scafforge-pivot` instead of hiding them inside generic ticket refinement or repair.
- If a Scafforge-managed repo needs workflow correction or contract upgrade, prefer `scafforge-repair` and let it escalate only intent-changing decisions.
- When the stack is still unknown, keep the scaffold framework-agnostic and record unresolved choices in the canonical brief.
- Do not let `ticket-pack-builder` fabricate implementation detail for unresolved major decisions.
- Preserve exact model/provider strings and project names when the source material specifies them.
- Do not skip `agent-prompt-engineering` during the standard greenfield flow.
- Do not introduce extra greenfield generation branches or user-selectable submodes after kickoff classifies the run as greenfield.
- Do not leave the initial generation pass before `handoff-brief` completes.
- Do not route the initial greenfield generation pass into `scafforge-audit` or `scafforge-repair`.
- Do not reintroduce a standalone package-level refinement route.

## Review and QA

Leave implementation review and QA procedure to the generated repo-local skills and review lanes after the scaffold is complete.
