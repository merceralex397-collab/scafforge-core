# Scafforge — Architecture Analysis

A plain-English breakdown of what the project does, how every major component relates to every other, where the design is strong, and where structural tensions exist. Aimed at someone who wants to understand the whole system before making changes.

---

## What Scafforge Actually Is

Scafforge is a **code generator for autonomous coding agents**. Its job is not to write application code. Its job is to take a messy description of a software project and produce a well-structured repository that an AI agent can operate inside without needing a human to constantly re-explain the rules.

The generated repository is not the point. The operating layer *inside* the repository is the point: the agents, the tools, the plugins, the workflow state files, the ticket queue, the skill files. All of those together form what the plan calls an "operating framework" — a set of rails that keep an AI agent on track through a multi-stage delivery cycle.

The primary target for that operating framework is **OpenCode**, a terminal-based AI coding assistant that understands a specific set of conventions (AGENTS.md, SKILL.md, opencode.jsonc, .opencode/ directories). The generator itself is designed to be runnable from any capable CLI host.

---

## The Two Layers

Understanding Scafforge requires holding two distinct things in mind simultaneously.

### Layer 1: The Generator Package (this repository)

This is what you are reading. It contains:
- Skills that orchestrate the scaffold generation process
- Python scripts that actually write files to a destination
- Reference docs and templates
- Validation scripts
- The CLI wrapper (`bin/scafforge.mjs`)

This layer runs *before* a project exists. Its inputs are messy notes, specs, and decisions. Its outputs are a directory full of files.

### Layer 2: The Generated Repo (what gets produced)

This is the OpenCode-oriented project directory that Scafforge creates. It contains:
- TypeScript tools that agents call at runtime
- TypeScript plugins that enforce workflow rules automatically
- Markdown agent definitions
- Markdown skill files
- A ticket queue with manifest and board
- Workflow state JSON files
- Documentation

This layer runs *after* the project exists. Its inputs are tickets and workflow state. Its outputs are implemented software plus audit artifacts.

A common source of confusion in the codebase (and the documentation) is conflating these two layers. Several skills describe both generating the framework *and* using the framework. The team leader agent prompt, for example, is a file in Layer 1 (the generator's template) but it describes how to behave in Layer 2 (the generated repo's runtime).

---

## The Skill Chain

Skills are the units of orchestration in the generator. Each is a Markdown file with YAML frontmatter plus instructions for what a host agent should do. They are not code — they are instructions to an AI. The actual file-writing happens in the Python scripts those instructions point to.

The full-cycle flow reads:

```
User input (messy spec)
       ↓
scaffold-kickoff          ← decides greenfield vs retrofit, sequences everything
       ↓
spec-pack-normalizer      ← extracts facts, flags ambiguities, produces canonical brief
       ↓
repo-scaffold-factory     ← runs bootstrap_repo_scaffold.py, writes template to disk
       ↓
ticket-pack-builder       ← creates the ticket queue from the brief
       ↓
project-skill-bootstrap   ← generates local SKILL.md files for the new repo
       ↓
agent-prompt-engineering  ← hardens agent prompts if needed
       ↓
repo-process-doctor       ← audits the result, applies safe repairs
       ↓
handoff-brief             ← refreshes START-HERE.md and restart surface
```

The flow manifest (`skills/skill-flow-manifest.json`) is the machine-readable version of this chain. The validator (`scripts/validate_scafforge_contract.py`) checks that the manifest's greenfield sequence contains all required steps.

---

## The Template System

The heart of Layer 1 is the template directory:
```
skills/repo-scaffold-factory/assets/project-template/
```

This is a complete, runnable example of a generated repo. The bootstrap script (`bootstrap_repo_scaffold.py`) copies it to a destination, performs string replacement on placeholder tokens (`__PROJECT_NAME__`, `__PLANNER_MODEL__`, etc.), and writes provenance metadata.

### How the Template Works

The template contains files with placeholder tokens where project-specific values should go. The Python script's `replacements` dictionary maps each token to a value derived from command-line arguments. Every `.md`, `.json`, `.ts`, and related file is processed through `render_text()`.

**Key design decision:** The template is the single source of truth for scaffold assets. The `opencode-team-bootstrap` skill is explicitly documented as "a thin wrapper" that calls the same template with `--scope opencode`. Nothing in the downstream skills is allowed to duplicate template logic.

**Consequence:** Any change to the generated output must be made in the template, not in downstream skill files. This is a good constraint but must be communicated clearly — it is not currently in any user-facing documentation.

---

## The Runtime Tooling (Layer 2)

When a generated repo is running, the agents interact with the project's state through six key tools. These are TypeScript files in `.opencode/tools/`.

### `ticket_lookup.ts`
Read-only. Resolves the active ticket from `tickets/manifest.json` and returns the full ticket plus a summary of which stage artifacts exist. Every agent session should start here.

### `ticket_update.ts`
The primary state mutation tool. Updates ticket stage, status, and summary. Can activate a different ticket. Enforces all stage transition rules (e.g. cannot move to `in_progress` without an approved plan, cannot move to `done` without a QA artifact). Also writes the changes back to `workflow-state.json`.

This is the most important safety rail in the system. All stage transitions should go through this tool, not through raw file edits.

### `artifact_write.ts`
Writes the full text body of a stage artifact (plan, implementation, review, QA, handoff) to the canonical path. The canonical path is computed by `defaultArtifactPath()` in `_workflow.ts` and is deterministic: `<stage-directory>/<ticket-slug>-<stage>-<kind>.md`.

### `artifact_register.ts`
Registers metadata about an artifact that has already been written. Updates both the ticket entry in `manifest.json` and the global registry in `.opencode/state/artifacts/registry.json`. The critical rule: write first, register second. These are two separate operations.

### `context_snapshot.ts`
Writes a compact human/agent-readable snapshot of current state to `.opencode/state/context-snapshot.md`. Intended to be called before session handoffs so the next session can get up to speed quickly.

### `handoff_publish.ts`
Updates the managed block inside `START-HERE.md` (using the `CODEXSETUP` markers — see BUG-01 in the issues report) and writes a copy to `.opencode/state/latest-handoff.md`. Uses `mergeStartHere()` to preserve any curated content outside the managed block.

### The `_workflow.ts` Shared Module
All tools import from this shared module. It contains all data types, path helpers, JSON read/write utilities, and the rendering functions for the board, context snapshot, and START-HERE. This is sound architecture — a single source of truth for all state manipulation logic.

---

## The Plugin System (Layer 2)

Plugins are TypeScript files in `.opencode/plugins/` that hook into OpenCode's event system. They run automatically without any explicit agent invocation.

### `stage-gate-enforcer.ts`
The most important plugin. Intercepts `tool.execute.before` events and blocks implementation-oriented actions (shell commands, file writes) before the plan is approved. Also blocks ticket status transitions that would violate stage order.

**Current gap:** It allows writes to any `.opencode/` path before approval, which technically includes the implementations directory (see RISK-01 in the issues report).

### `tool-guard.ts`
Blocks reads and writes to `.env` files and dangerous shell commands (rm, git reset, sudo, etc.). Simpler and more general than the stage-gate enforcer.

### `invocation-tracker.ts`
Logs every chat message, command execution, tool call, and tool result to `.opencode/state/invocation-log.jsonl`. This gives the project observability — you can see what the agent actually did, not just what it claimed to do.

### `ticket-sync.ts`
After any of the five key workflow tools complete, writes a summary to `.opencode/state/last-ticket-event.json`. Provides a quick "what just changed" surface without reading the full manifest.

### `session-compactor.ts`
Hooks into OpenCode's experimental compaction event and appends a reminder to refresh the context snapshot. Does not actually protect anything from compaction — see IMP-16 in the improvements document.

---

## The Agent Architecture (Layer 2)

The generated agents follow a strict hierarchy.

### Visible Primary Agent: `team-leader`
The only agent a human interacts with directly. Owns the full ticket lifecycle: reads state, delegates to specialists, enforces stage gates, performs closeout. It does not write code or plans directly.

### Hidden Core Specialists (subagents)
- `planner` — produces decision-complete plans, writes artifacts
- `plan-review` — approves or rejects plans, never implements
- `implementer` — follows the approved plan, writes code and implementation artifacts
- `reviewer-code` — reads the implementation, produces findings, never writes code
- `reviewer-security` — focused subset of code review for trust and secrets
- `tester-qa` — runs validation commands, produces QA artifacts, never writes code
- `docs-handoff` — synchronises closeout artifacts

### Hidden Utility Specialists (subagents)
- `utility-explore` — read-only repo navigation
- `utility-shell-inspect` — read-only shell commands for evidence gathering
- `utility-summarize` — compresses evidence for handoff
- `utility-ticket-audit` — checks ticket/manifest/board consistency
- `utility-github-research` — reads GitHub repos for examples
- `utility-web-research` — external research

**Key architectural constraint:** Only the team leader and the planner/reviewer roles delegate. Implementers do not fan out. Utility agents do not recurse. This prevents delegation explosions.

**Permission model:** Every agent has explicit `permission.task` allowlists that restrict which other agents it can delegate to. This is the structural enforcement of the delegation constraint.

---

## The Ticket and State Architecture

This is the most carefully designed part of the system. There are four distinct state surfaces with different owners.

### `tickets/manifest.json` — Queue State
The authoritative machine-readable source for which tickets exist, their metadata, and which artifacts have been registered. The board is derived from this. The workflow state is derived from the active ticket here.

### `tickets/BOARD.md` — Derived Human Board
Read-only for agents. Written by `saveManifest()` which calls `renderBoard()`. Never edited directly.

### `.opencode/state/workflow-state.json` — Transient Approval State
Stores `active_ticket`, `stage`, `status`, and `approved_plan`. Separate from the manifest because `approved_plan` is not a durable ticket property — it resets every time a new ticket becomes active. Also serves as a fast-read cache so agents do not have to parse the manifest just to know if the plan is approved.

### Stage-Specific Artifact Directories — Proof Storage
`.opencode/state/plans/`, `implementations/`, `reviews/`, `qa/`, `handoffs/`. Artifact bodies live here. Artifact metadata (path, kind, stage, timestamp, summary) lives on the ticket entry in the manifest and is mirrored into the global registry at `.opencode/state/artifacts/registry.json`.

**Why this split matters:** Without separate artifact storage, agents would have to parse ticket bodies to determine stage completeness. The `artifact_summary` returned by `ticket_lookup.ts` gives a clean boolean summary: `has_plan`, `has_implementation`, `has_review`, `has_qa`. Stage gates enforce these before transitions.

---

## The Audit System

`skills/repo-process-doctor/scripts/audit_repo_process.py` is a standalone Python script that analyses a repository for workflow smells. It is not invoked at runtime — it is a developer/CI tool.

It checks for approximately 20 distinct problems, grouped into categories:
- Status model problems (using stage-like statuses in the ticket queue)
- Missing tool layers (no ticket_lookup, no workflow-state, etc.)
- Artifact architecture drift (wrong paths, wrong separation of write vs register)
- Prompt anti-patterns (eager skill loading, impossible read-only delegation)
- Plugin problems (read-only agents with mutating shell commands)

The doctor is designed to be run against both the Scafforge template itself and against any generated repo that has aged or drifted.

**Gap:** There is no automated test that confirms the doctor produces zero findings against a freshly generated scaffold.

---

## Where the Design Is Strongest

**1. The `_workflow.ts` single shared module**
All state logic in one place. The same rendering functions produce board, snapshot, and start-here content consistently. Path helpers are deterministic. If you need to change how an artifact path is computed, you change it once.

**2. The stage gate plugin**
Automatic enforcement means an agent cannot accidentally implement before approval even if it forgets to check. The plugin does not trust prompts — it intercepts tool calls directly.

**3. The `artifact_write` + `artifact_register` split**
Elegant. The write operation stores content; the register operation stores metadata. They are intentionally decoupled so a register cannot accidentally overwrite a full artifact body with a summary.

**4. The skill permission model**
`permission.task` allowlists mean delegation paths are hard-coded, not inferred from prose. An implementer literally cannot delegate to a planner.

**5. The flow manifest (`skill-flow-manifest.json`)**
Machine-readable description of the orchestration chain. The validator checks it. This is the kind of self-describing architecture that ages well.

---

## Where the Design Has Structural Tensions

**1. Skills describe both generation-time and runtime behaviour**
The team leader's `SKILL.md` (in the generator) and the team leader's agent `.md` file (in the template) are different files for different purposes. But several other skills blur this line — `ticket-execution/SKILL.md` in the template is a runtime skill for generated-repo agents, while `ticket-pack-builder/SKILL.md` is a generation-time skill for the host agent. This layering is correct but not clearly labelled, which leads to confusion when reading.

**2. The doctor checks for patterns it cannot fully verify**
Several audit checks look for the presence or absence of text strings in prompt files. This is a reasonable heuristic but it cannot verify correctness — an agent prompt could contain "approved_plan" as a counter-example (what not to do) and still pass. More structural checks (e.g. verifying that the `stage-gate-enforcer.ts` plugin is actually registered in `opencode.jsonc`) would be more reliable.

**3. The template is the single source of truth but the conformance checklist is a separate file**
If a new file is added to the template, someone must remember to add it to `references/opencode-conformance-checklist.json` as well. There is no automated way to detect that the checklist is out of sync with the template.

**4. `handoff_publish` depends on marker presence for correct operation**
The merge logic only works if the managed markers are present in `START-HERE.md`. If they are accidentally removed, the handoff silently does nothing. This is a fragile dependency on a specific string being present in a file that users are expected to edit.

**5. The Python bootstrap and TypeScript tools share conceptual logic but not code**
`_workflow.ts` has `defaultArtifactPath()`. The Python smoke test and validator have their own path-related logic. The Python doctor has its own understanding of what a valid artifact path looks like. If the canonical path convention changes, it must be updated in three places.

---

## Recommended Reading Order for New Contributors

1. `README.md` — what Scafforge is and its core promise
2. `AGENTS.md` — operating rules for the package itself and skill boundaries
3. `skills/scaffold-kickoff/SKILL.md` — the default flow in one page
4. `skills/skill-flow-manifest.json` — the machine-readable flow
5. `skills/repo-scaffold-factory/assets/project-template/docs/process/workflow.md` — what the generated repo's workflow looks like from the inside
6. `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts` — all runtime state logic in one module
7. `skills/repo-process-doctor/scripts/audit_repo_process.py` — what "a healthy generated repo" looks like, inverted
8. `devdocs/scafforge-implementation-plan.md` — the full design rationale (skip the Windows paths, read the interview questions section)
