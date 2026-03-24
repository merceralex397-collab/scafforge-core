---
name: scaffold-kickoff
description: Orchestrate the full Scafforge kickoff flow for greenfield, retrofit, managed-repair, or diagnosis/review work. Use when asked to scaffold a new repo, add the OpenCode operating layer to an existing repo, repair a Scafforge-managed workflow contract, or diagnose an in-progress project. This is the single public entrypoint and routes to the correct downstream skills automatically.
---

# Scaffold Kickoff

This is the default public entrypoint. When a user asks you to scaffold, retrofit, repair, refresh, or diagnose a Scafforge-managed project, start here and route internally.

## Decision tree

Before starting, classify the run type:

1. **Greenfield** — No repo exists yet, or the repo contains only specs, plans, or notes. Follow the full workflow below.
2. **Retrofit** — A repo with code already exists but is missing the current OpenCode operating layer. Run `spec-pack-normalizer` first if the project lacks a canonical brief, then route to `opencode-team-bootstrap`, continue through ticket and local-skill repair as needed, and finish with `scafforge-audit`.
3. **Managed repair / update** — A Scafforge-managed or OpenCode-oriented repo already exists but needs workflow-contract repair, upgrade, or managed-surface replacement. Route directly to `scafforge-repair`, then run any targeted follow-up skills it reveals and finish with `handoff-brief`.
4. **Diagnosis / review** — An in-progress or claimed-complete repo needs read-only diagnosis, codebase review, report generation, or evidence validation. Route to `scafforge-audit`.

If the repo state and the user's request do not make the run type clear, ask the user before proceeding. Do not silently choose between greenfield, retrofit, managed repair, and diagnosis/review when that choice would materially change scope.

## Full greenfield workflow

Follow these steps in order. Each step references a sibling skill. Read it at the relative path shown.

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

### Step 4: Design and customize the agent team

Read `../opencode-team-bootstrap/SKILL.md` and follow its procedure.

The scaffold creates generic agent templates. You must now customize them:
- rewrite agent prompts to be project-specific
- add or remove agents based on project type
- create multiple implementer-type agents if the project spans different domains

### Step 5: Build the ticket backlog

Read `../ticket-pack-builder/SKILL.md` and follow its procedure in bootstrap mode.

Create implementation-ready tickets from the canonical brief:
- break work into implementation waves
- keep each ticket small enough for one agent session
- convert unresolved major decisions into blocked or decision tickets instead of guesses

### Step 6: Bootstrap project-local skills

Read `../project-skill-bootstrap/SKILL.md` and follow its procedure.

- foundation mode: populate baseline skills with actual project data
- synthesis mode: create stack- or domain-specific skills from project evidence and external research

### Step 7: Harden agent prompts

Read `../agent-prompt-engineering/SKILL.md` and follow its procedure.

This pass is required in the standard greenfield scaffold flow.

### Step 8: Audit the generated repo

Read `../scafforge-audit/SKILL.md` and follow its procedure.

Run the audit against the freshly generated repo. If the audit identifies Scafforge package defects, stop after the diagnosis pack, have the user manually carry that pack into the Scafforge dev repo, implement the package changes there, then return to the generated repo before routing to `../scafforge-repair/SKILL.md`. Escalate intent-changing issues to the user.

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
- a clean audit from `scafforge-audit`

## Diagnosis / review flow

When the task is diagnosis or review of an existing project:

1. read `../scafforge-audit/SKILL.md`
2. run the audit and any requested evidence-validation review work
3. produce the four-report diagnosis pack when requested
4. if the audit identifies Scafforge package work, have the user manually copy the diagnosis pack into the Scafforge dev repo and complete those package changes first
5. route to `../scafforge-repair/SKILL.md` only after the required package changes exist and the audit still recommends repair
6. finish with `../handoff-brief/SKILL.md` when a restart surface or closeout is needed

## Required outputs

- a canonical brief that separates facts, assumptions, and open questions
- a decision packet that records blocking versus non-blocking ambiguities
- a scaffolded repo with README.md, AGENTS.md, START-HERE.md, docs, and tickets
- a structured truth hierarchy with clear ownership for facts, queue state, transient workflow state, artifacts, provenance, and handoff
- the OpenCode agent, command, tool, plugin, and local-skill layer customized for the specific project
- a process audit confirming the generated repo is clean or clearly routed to repair
- a diagnosis pack when the run type is diagnosis/review
- a handoff surface that another machine or session can resume from

## Rules

- Prefer this umbrella flow for greenfield work instead of manually starting with lower-level skills.
- Keep generated docs and prompts weak-model friendly: short sections, explicit steps, obvious source-of-truth files.
- Keep `scaffold-kickoff` as the human entrypoint even when the repo already exists; route internally to `opencode-team-bootstrap`, `scafforge-audit`, `scafforge-repair`, or another downstream skill instead of asking the user to pick the lower-level entry.
- If a Scafforge-managed repo needs workflow correction or contract upgrade, prefer `scafforge-repair` and let it escalate only intent-changing decisions.
- When the stack is still unknown, keep the scaffold framework-agnostic and record unresolved choices in the canonical brief.
- Do not let `ticket-pack-builder` fabricate implementation detail for unresolved major decisions.
- Preserve exact model/provider strings and project names when the source material specifies them.
- Do not skip `agent-prompt-engineering` during the standard greenfield flow.
- Do not ship a repo-local workflow until an audit pass confirms it is clean or explicitly routes to repair.
- Do not reintroduce a standalone package-level refinement route.

## Review and QA

Leave implementation review and QA procedure to the generated repo-local skills and review lanes after the scaffold is complete.
