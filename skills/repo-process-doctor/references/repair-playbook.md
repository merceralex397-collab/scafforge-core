# Repair Playbook

## Target architecture

- manifest: machine-readable queue state
- board: derived human board
- ticket files: detailed ticket content
- workflow-state: transient approval, current stage, and active process-version / post-migration verification state
- artifact-write tool: writes canonical stage artifact bodies
- registered artifacts: proof for stage transitions
- bootstrap provenance: canonical workflow-contract version, managed-surface ownership, and repair history

## Managed-surface replacement contract

When a repo has an older or conflicting OpenCode operating layer, replace these deterministic workflow-engine surfaces together:

- `opencode.jsonc`
- `.opencode/tools/`
- `.opencode/plugins/`
- `.opencode/commands/`
- scaffold-managed foundation entries under `.opencode/skills/`, while preserving clearly project-authored local skills
- `docs/process/workflow.md`
- `docs/process/tooling.md`
- `docs/process/model-matrix.md`
- `docs/process/git-capability.md`
- the managed block inside `START-HERE.md`

Then repair or regenerate these project-specific follow-up surfaces only when audit evidence shows they drifted:

- `.opencode/agents/`
- `docs/process/agent-catalog.md`

Preserve these durable project surfaces unless a specific finding proves they are malformed:

- `docs/spec/CANONICAL-BRIEF.md`
- `tickets/manifest.json`
- `tickets/*.md`
- registered artifact bodies under `.opencode/state/`
- repo code and project docs outside the managed workflow layer

After replacement:

- append a repair entry to `.opencode/meta/bootstrap-provenance.json`
- update `.opencode/state/workflow-state.json` with the new process version metadata
- source the canonical process version from `.opencode/meta/bootstrap-provenance.json` under `workflow_contract.process_version`
- set `pending_process_verification: true`
- route completed-ticket rechecks through the backlog verifier before permitting guarded follow-up ticket creation

## Migration order

1. simplify ticket status vocabulary
2. add workflow-state and ticket tools
3. remove raw-file stage control from prompts and commands
4. split artifact writing from artifact registration and unify canonical artifact paths
5. keep workflow-state synchronized only from the active ticket
6. preserve curated START-HERE content during handoff publication
7. harden read-only shell agents
8. add artifact proofs for planning, implementation, review, and QA
9. rerun the audit
10. leave post-migration verification pending when the process contract materially changed

## Safe-repair boundary

Safe repairs usually include:

- regenerating derived docs from canonical state
- aligning queue, workflow-state, and artifact contracts to the current scaffold model
- removing raw-file stage control where a tool-backed path already exists
- normalizing contradictory status semantics into the current coarse queue contract
- replacing the deterministic workflow-engine surfaces when audit evidence shows the repo is on an older Scafforge contract and curated project sources will be preserved

Escalate instead of auto-applying when a repair would:

- change project scope or product intent
- choose between unresolved stack or runtime options
- change provider or model choices
- delete or rewrite curated human project decisions rather than derived views
- replace ambiguous or mixed-ownership surfaces without clear evidence that they are still Scafforge-managed
- collapse a repo-specific pattern that is not clearly broken

## DeepHat-style migration notes

- replace `planned` and `approved` ticket statuses with coarse queue status
- move plan approval into workflow state
- replace manual board/manifest synchronization language with ticket-tool language
- write full artifacts through a dedicated artifact-write tool and keep `artifact_register` register-only
- align all artifact guidance on the stage-specific artifact directories plus `.opencode/state/artifacts/registry.json`
- update workflow-state from the active ticket only; background ticket edits must not rewrite active stage/status
- merge managed START-HERE handoff blocks instead of overwriting curated repo-specific content
- remove mutating shell loopholes from inspection roles
- narrow preflight commands so they stop at the intended stage
- record the process version change and leave a verification trail when managed surfaces were replaced

## EXEC repair actions (EXEC001 / EXEC002 / EXEC003)

EXEC findings mean source-layer bugs exist that the Scafforge process failed to catch before tickets were closed. The repair is two-part: **sync the agent process layer** so agents enforce execution proof going forward, and **create remediation tickets** so OpenCode agents fix the source bugs.

### Part 1 — Sync agent execution-enforcement rules

The implementer and tester-qa agent prompts in the repo may pre-date the PR6 execution-enforcement rules. Check whether the following lines are present in every `*-implementer*.md` and `*-tester-qa.md` agent under `.opencode/agents/`:

**Implementer agents must contain:**
```
- before creating the implementation artifact, run at minimum:
  - a compile or syntax check on all new or modified source files
  - an import check for the primary module
  - the project test suite if it exists
- include the command output in the implementation artifact
- do not create an implementation artifact for code that fails these checks
```

**Tester-QA agent must contain:**
```
- "code inspection" alone is not validation — you must execute tests or compile checks
- run the project test suite and report pass/fail counts with command output
- if no test suite exists, run compile or syntax checks and import verification on all source files
- include raw command output in the QA artifact
- if the QA artifact does not contain command output, it will be rejected by the team leader
- a QA artifact under 200 bytes is almost certainly insufficient — add more evidence or return a blocker
```

If any of these lines are absent, add them. This is a safe repair — it enforces the existing scaffold contract, it does not change project intent. Reference the current template at `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/` for the authoritative wording.

### Part 2 — Create remediation tickets for source-layer bugs

Do **not** fix source code directly. Instead, create one ticket per EXEC finding in the repo's `tickets/manifest.json` and as a ticket file. Each ticket must:

- have a unique ID (e.g. `EXEC-001`, `EXEC-002`)
- status: `ready`
- stage: `planning`
- wave: next available wave number
- lane: `bugfix`
- title: a precise description of the specific error (include file and line if known)
- description: include the error message verbatim from the audit evidence, the safer pattern from the audit finding, and the acceptance criterion: "service imports cleanly and `pytest tests/` exits 0"
- `parallel_safe: yes` (execution fixes are typically independent)
- `overlap_risk: high` (imports affect the whole service)

After creating tickets, update `tickets/BOARD.md` to show the new entries, and set `pending_process_verification: true` in workflow-state so the backlog verifier lane re-checks previously completed tickets against the repaired process.

### What counts as resolved

Re-run `audit_repo_process.py` after the repair agent completes the tickets. EXEC findings are resolved only when:
- `from src.<pkg>.main import app` exits 0 for every main package
- `pytest tests/` exits 0 with 0 failures and 0 collection errors
