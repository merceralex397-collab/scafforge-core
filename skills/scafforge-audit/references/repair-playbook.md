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
- change provider or model choices that reflect a newer human decision for this repo rather than removal of deprecated package-managed defaults
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

## BOOT repair actions (BOOT001)

BOOT findings mean the managed bootstrap layer is broken on the current machine. Treat this as a workflow-surface repair first, not as a source ticket.

- refresh the managed bootstrap surfaces, especially `.opencode/tools/environment_bootstrap.ts` and any related bootstrap command docs, through `scafforge-repair`
- replace bare global-pip assumptions with repo-native bootstrap logic (`uv` for uv-managed repos, otherwise repo-local `.venv` plus `.venv/bin/python -m pip`)
- surface missing prerequisites accurately; a failed bootstrap artifact must not report `Missing Prerequisites: None` when `pip` or `uv` is actually missing
- rerun the subject repo's `environment_bootstrap` flow after the managed-surface refresh, then rerun `audit_repo_process.py`; source-layer EXEC tickets should proceed only after `BOOT001` is gone

## Workflow repair actions (WFLOW001 / WFLOW002 / WFLOW003 / SESSION001)

Workflow findings mean the generated repo contract itself is causing or misreporting the deadlock.

- `WFLOW001`: refresh `.opencode/tools/smoke_test.ts` so Python repos prefer explicit project overrides, then `uv run`, then repo-local `.venv`, and only lastly system python
- `WFLOW002`: refresh handoff publication so free-form next-action text cannot claim dependency unblocking or `not a code defect` while the manifest, workflow state, or stage artifacts disagree
- `WFLOW003`: refresh the workflow contract so `plan_review` is distinct from post-implementation `review` across docs, tools, and prompts
- `SESSION001`: when a supplied transcript proves the causal failure, carry that transcript into package-side audit fixes first; do not treat the resulting report as ordinary current-state repo drift

## SKILL repair actions (SKILL001)

SKILL findings mean the repo-local skill layer is still carrying scaffold placeholder text.

- refresh scaffold-managed foundation skills under `.opencode/skills/`, rerun the project-specific local-skill regeneration pass, and continue into agent-team/prompt follow-up when the regenerated skills change allowlists or model guidance
- `stack-standards` must contain concrete framework rules and actual validation commands from the repo, not placeholder filler
- rerun audit and confirm no generated `.opencode/skills/*.md` files still contain template text such as `Replace this file...`

## MODEL repair actions (MODEL001)

MODEL findings mean the repo-local model/profile layer drifted from the current package guidance.

- regenerate `.opencode/skills/model-operating-profile/SKILL.md`
- align `docs/process/model-matrix.md`, `.opencode/meta/bootstrap-provenance.json`, and agent frontmatter on the active runtime model choices
- if the repo is still on a deprecated package-managed MiniMax default, remove `MiniMax-M2.5` surfaces and refresh to the current package default as safe repair
- only treat model drift as protected intent when newer explicit accepted-decision evidence shows the repo was deliberately re-pinned after the package changed
- rerun `../agent-prompt-engineering/SKILL.md` after model-profile changes so delegation and evidence rules match the new model defaults

## Repeated-cycle repair actions (CYCLE001)

CYCLE findings mean a previous diagnosis pack and a later repair history entry exist, but the same workflow-layer findings survived into the next audit.

- compare the latest diagnosis pack against `repair_history` before starting another repair pass
- explain which findings persisted and whether the previous repair skipped regeneration, used stale Scafforge package logic, or misclassified deprecated package-managed drift as protected intent
- treat repeated `BOOT001`, `SKILL001`, or `MODEL001` findings as a repair failure to close, not as a reason to preserve the same surfaces again

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
