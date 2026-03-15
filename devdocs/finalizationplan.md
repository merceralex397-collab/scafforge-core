# Scafforge Finalization Plan

Status: Draft finalization plan with user-approved scope expansions incorporated

This plan is the final release-hardening roadmap for taking Scafforge from “implemented baseline” to “safe to move into live usage”.

It is based on:

- `opusreview.md`
- `opussuggestions.md`
- `nextsteps.md`
- `devdocs/history/scafforge-architecture-analysis.md`
- `devdocs/history/scafforge-critical-issues.md`
- `devdocs/history/scafforge-improvements.md`
- `devdocs/worklog.md`
- `devdocs/scafforge-implementation-plan.md`
- direct inspection of the current repository state

The plan is deliberately split into:

1. verified release blockers
2. verified hardening work that should be done before live usage
3. suggestions that are useful but change product behavior, scope, or release shape enough that they need user confirmation

---

## 1. Finalization goal

Scafforge should be considered ready for live usage only when all of the following are true:

- it generates an OpenCode-oriented output that is structurally correct against current OpenCode conventions
- the generated runtime does not leak legacy naming, contradictory state, or silent workflow bypasses
- the package is installable and understandable from the intended host CLIs:
  - GitHub Copilot CLI
  - Codex
  - Claude Code / Claude CLI
- the core wrapper and scripts are publishable or clearly marked as pre-publish
- the validation harness catches the defects that matter most before release
- repo docs, template docs, and generated runtime surfaces tell one coherent story

This is not a plan to expand Scafforge into a different product.

This is a plan to finish the current product properly.

---

## 2. Evidence-based audit summary

### 2.1 Claims I verified as real defects or real release blockers

These are not speculative. I confirmed them directly in the current repo.

1. Root `.gitignore` is still missing.
   - confirmed: there is no top-level `.gitignore`
   - impact: the repo is not cleanly maintainable or publishable

2. Python bytecode is present in the repo.
   - confirmed:
     - `skills/repo-scaffold-factory/scripts/__pycache__/bootstrap_repo_scaffold.cpython-314.pyc`
     - `skills/repo-process-doctor/scripts/__pycache__/audit_repo_process.cpython-314.pyc`
     - `skills/opencode-team-bootstrap/scripts/__pycache__/bootstrap_opencode_team.cpython-314.pyc`
   - impact: accidental binary artifacts remain in source control scope

3. Legacy `CODEXSETUP` managed markers are still live in generated output.
   - confirmed in:
     - `skills/repo-scaffold-factory/assets/project-template/START-HERE.md`
     - `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts`
   - impact: generated repos still leak the old branding and the validator does not catch it

4. `validate_scafforge_contract.py` does not currently ban `CODEXSETUP`.
   - confirmed by direct inspection of the disallowed list
   - impact: release validation misses a known legacy leakage pattern

5. `context_snapshot.ts` mutates workflow state in memory without persisting it.
   - confirmed:
     - it changes `active_ticket`, `stage`, and `status` when `ticket_id` is passed
     - it never calls `saveWorkflowState`
   - impact: the written snapshot can disagree with `workflow-state.json`

6. The smoke test does not check for unreplaced placeholders.
   - confirmed in `scripts/smoke_test_scafforge.py`
   - impact: a broken replacement map can still produce a passing smoke test

7. `template_commit()` has no timeout.
   - confirmed in `bootstrap_repo_scaffold.py`
   - impact: low-frequency but real CI and automation hang risk

8. `package.json` is still `"private": true` while adapter docs describe installable package flows.
   - confirmed in `package.json` and `adapters/manifest.json`
   - impact: the documented install path is not currently truthful for public package usage

9. The adapter manifest currently lacks the required Claude host lane and mixes host-layer vs generated-runtime semantics.
   - confirmed:
     - manifest contains `github-copilot`, `codex`, `gemini-cli`, and `opencode`
     - `opencode` entry describes operating the generated repo, not installing/running Scafforge
     - there is no `claude` / `claude-code` adapter entry
   - impact: the package is not yet correctly documented for the target CLI set the user specified

10. The generated stage gate still allows any `.opencode/` path before plan approval.
    - confirmed in `stage-gate-enforcer.ts`
    - impact: implementation-stage writes can be routed through raw file edits under `.opencode/`

11. `handoff_publish.ts` cannot tell callers whether `START-HERE.md` actually merged.
    - confirmed:
      - `mergeStartHere()` returns the existing file unchanged if markers are missing
      - `handoff_publish.ts` always returns success-shaped output without a merge result
    - impact: silent handoff no-op risk

12. Generated `opencode.jsonc` still allows global `sed *`.
    - confirmed in the template config
    - impact: over-broad mutation surface and future audit inconsistency

13. `workflow-state.json` and `tickets/manifest.json` start in inconsistent initial stage/status values.
    - confirmed:
      - workflow state starts at `planning` / `ready`
      - manifest ticket starts at `scaffold` / `todo`
    - impact: contradictory startup state in a freshly generated repo

14. The conformance checklist is incomplete.
    - confirmed:
      - `docs/process/agent-catalog.md` exists and is referenced in template guidance
      - it is not currently in `required_files`
      - `docs/process/tooling.md` is also a candidate for explicit inclusion
    - impact: validation can miss a genuinely required generated file

15. `README.md` and `REVIEW-NOTES.md` still contain invisible citation artifacts.
    - confirmed by non-ASCII search hits showing the citation markers
    - impact: dirty published docs and confusing hidden characters

16. `TASKS.md` still leaves some now-implemented items visually open in the body.
    - confirmed for T-019 and T-020
    - impact: documentation contradiction remains even though a status note was added

17. `package.json` still lacks `engines`.
    - confirmed
    - impact: Node runtime expectations are undocumented for an ESM CLI wrapper

18. There is still no contributor/developer setup guide.
    - confirmed: no root `CONTRIBUTING.md`
    - impact: live usage and ongoing maintenance remain harder than necessary

### 2.2 Claims I accept as real hardening needs, but not strict “bugs”

These are valid issues, but I would classify them as release hardening rather than broken behavior today.

1. `bin/scafforge.mjs` command dispatch should be refactored away from independent `if` blocks.
   - today it works because `runPython()` exits
   - it is still brittle and should be cleaned before release

2. `bootstrap_repo_scaffold.py` does not literally overwrite existing files without `--force`, but it can still partially merge into a non-empty destination.
   - the review’s wording is somewhat overstated
   - the actual issue is lack of a non-empty destination preflight warning

3. `docs/process/tooling.md` not being explicit in `opencode.jsonc` instructions is a compatibility hardening point.
   - it may be loaded through the glob already
   - but relying on glob behavior alone is weaker than listing it directly

4. Windows-specific paths in `devdocs/` are not a generated-output bug.
   - they are still an active-context hygiene problem
   - they should be quarantined or explicitly marked as historical/non-operational

5. Lack of a doctor-zero-findings test against the freshly generated scaffold is a release hardening gap.
   - the template may look fine today
   - the missing test means future regressions can slip through

### 2.3 Claims I refute or downgrade

These should not be treated as core release blockers in the same way.

1. “Non-chained `if` statements” in the CLI wrapper are not a current runtime bug.
   - they are maintainability debt
   - they become a bug only if dispatch behavior is refactored later

2. “Silent overwrite without `--force`” is inaccurate as stated.
   - file collisions are blocked today
   - the real problem is ambiguous partial scaffolding into an already-populated directory

3. Some suggestions in `opussuggestions.md` and `scafforge-improvements.md` are good product ideas, but they are not required to conclude baseline development.
   - examples:
     - `scafforge init`
     - complexity profiles
     - compaction-preservation plugin
     - configurable stage-gate paths
   - these need user choice before becoming part of the release target

---

## 3. Cross-check against the earlier implementation plan and worklog

### 3.1 What the earlier implementation plan and worklog did complete

The prior implementation pass genuinely completed the broad architectural baseline:

- product contract hardening
- truth hierarchy definition
- one-cycle flow contract
- explicit model/provider arguments
- artifact registry architecture
- default local skill pack lanes
- flow manifest
- contract validator
- smoke-test harness
- adapter/package surface beginnings
- worklog and roadmap cross-check

That means the repo is not starting from scratch.

It is now in the “release hardening and consistency closure” phase.

### 3.2 What was still left open after that pass

The remaining work is concentrated, not sprawling:

- release hygiene
- output-brand cleanup
- state consistency
- stronger validation coverage
- host adapter completion
- packaging truthfulness
- documentation cleanup

### 3.3 Conclusion from the cross-check

The previous implementation should be treated as:

- baseline architecture: complete enough
- release polish and correctness closure: not complete yet

So the finalization plan should not reopen the entire project.

It should finish the last mile.

---

## 4. Non-negotiable finalization principles

1. No expansion of generated output beyond OpenCode.
   - user already fixed this
   - the output target stays OpenCode-only

2. Host portability must be about running Scafforge, not changing the generated runtime model.
   - Copilot, Codex, and Claude are host paths into the generator
   - they are not alternate generated output profiles

3. Any change that significantly alters behavior or scope must be confirmed with the user before implementation.
   - examples:
     - interactive init wizard
     - multiple complexity profiles
     - changing default skill-count strategy
     - adding new optional plugin families

4. “Perfectly functioning” means both:
   - no known release blocker remains
   - the repo can prove its own claims with validation and install documentation

5. OpenCode correctness must be checked as a release gate, not merely described.

---

## 5. Finalization roadmap

## Workstream A - Release hygiene and repository correctness

### A1. Add root `.gitignore`

Files:

- `.gitignore`

Precise fix:

- add ignores for Python cache, Node dependencies, editor files, OS clutter, temporary test output
- include at minimum:
  - `__pycache__/`
  - `*.pyc`
  - `node_modules/`
  - `.env`
  - `.DS_Store`
  - `Thumbs.db`
  - `.idea/`
  - `.vscode/`

Why:

- this is a basic release-readiness requirement
- it also fixes the current bytecode leakage problem at the root cause

### A2. Remove committed `.pyc` / `__pycache__` artifacts from repository state

Files/paths:

- the three currently present Python bytecode paths

Precise fix:

- remove tracked bytecode files and cache directories
- make sure future validation or contributor docs mention they must stay untracked

Why:

- the repo should not ship machine-specific compiled artifacts

### A3. Add release metadata to `package.json`

Files:

- `package.json`

Precise fix:

- add `engines.node >= 18`
- add a `repository` field
- decide whether `private: true` remains temporarily or is removed as part of publication readiness

Why:

- the wrapper is ESM and should declare runtime expectations
- install docs must match the actual package state

### A4. Add `CONTRIBUTING.md`

Files:

- `CONTRIBUTING.md`

Precise fix:

- explain prerequisites
- explain validation commands
- explain how to modify template surfaces safely
- explain how to run the doctor
- explain definition of done for core changes

Why:

- live usage includes future maintenance, not just initial generation

---

## Workstream B - Generated output correctness and runtime safety

### B1. Remove legacy `CODEXSETUP` markers everywhere they are operational

Files:

- template `START-HERE.md`
- `_workflow.ts`
- validator disallowed list

Precise fix:

- rename to Scafforge-owned managed markers
- make the comment self-explanatory enough that users know not to remove it casually
- update any merge logic or marker lookups
- add `CODEXSETUP` to validator disallowed text

Why:

- generated output should not leak legacy package-era names
- current validation misses this known problem

### B2. Fix `context_snapshot.ts` policy explicitly

Files:

- `.opencode/tools/context_snapshot.ts`
- possibly `_workflow.ts` and/or docs

Precise fix:

- choose one policy and document it:
  - preferred: snapshot the true active ticket only and remove the in-memory mutation
  - alternative: if `ticket_id` is intended to retarget the active context, persist the change with `saveWorkflowState`

Why:

- contradictory workflow surfaces are unacceptable in a system built around explicit state

### B3. Align initial generated state between manifest and workflow state

Files:

- template `tickets/manifest.json`
- template `.opencode/state/workflow-state.json`
- possibly startup docs if wording depends on the chosen initial state

Precise fix:

- choose one canonical initial state and make both files agree
- recommended:
  - either both start at scaffold/todo
  - or both start at planning/ready
- then reflect that state in `START-HERE.md` wording

Why:

- fresh scaffolds should not start life with contradictory state

### B4. Tighten pre-approval write gates

Files:

- `.opencode/plugins/stage-gate-enforcer.ts`

Precise fix:

- replace “any `.opencode/` path is safe” with a narrower allowlist
- pre-approval writes should allow only:
  - planning docs
  - ticket surfaces
  - approved planning artifact paths
  - configuration/help surfaces intentionally editable during setup
- block:
  - `.opencode/state/implementations/`
  - `.opencode/state/reviews/`
  - `.opencode/state/qa/`
  - other implementation-stage proof paths before approval

Why:

- otherwise the stage gate has a real bypass

### B5. Make handoff publishing detect merge failure

Files:

- `.opencode/tools/handoff_publish.ts`
- `_workflow.ts`
- possibly docs and prompts

Precise fix:

- return a `merged` boolean
- optionally also return a `reason` if merge did not occur
- update docs-handoff behavior so silent no-op becomes an explicit warning/blocker

Why:

- restart surfaces are too important to fail silently

### B6. Remove or narrow global `sed *` bash permission

Files:

- generated `opencode.jsonc`
- possibly individual agents if `sed` is still needed for specific roles

Precise fix:

- remove the blanket global permission
- only grant mutation-capable shell patterns to the specific agent surfaces that need them

Why:

- least privilege is part of making weaker-model workflows safer

### B7. Explicitly include critical generated docs in conformance checks

Files:

- `opencode-conformance-checklist.json`
- possibly validator coverage

Precise fix:

- add:
  - `docs/process/agent-catalog.md`
  - `docs/process/tooling.md`
- then ensure smoke test and validator both observe that checklist

Why:

- required read-order docs must be machine-checked if they are truly required

### B8. Strengthen `START-HERE.md` to be fully operational on its own

Files:

- template `START-HERE.md`
- `_workflow.ts` rendering logic if the runtime-generated version needs the same sections

Precise fix:

- add sections for:
  - active ticket
  - current stage
  - blockers
  - what to do if state surfaces disagree
  - how to refresh stale context
  - next action phrasing that is operational, not vague

Why:

- the user explicitly wants an agent to enter the repo, read the start surface, and continue autonomously

---

## Workstream C - Validation and regression closure

### C1. Add unreplaced-placeholder detection to the smoke test

Files:

- `scripts/smoke_test_scafforge.py`

Precise fix:

- scan generated text files for unresolved `__PLACEHOLDER__` patterns
- fail immediately if any remain

Why:

- this is a direct correctness check for the generator’s main responsibility

### C2. Add doctor-zero-findings validation against a freshly generated scaffold

Files:

- `scripts/smoke_test_scafforge.py`

Precise fix:

- after render, run `audit_repo_process.py` against the scaffold
- require zero findings, or at least a tightly defined zero-blocker threshold if some informational output is unavoidable

Why:

- the template should pass its own process doctor

### C3. Expand contract validation for stale/legacy strings and prompt rails

Files:

- `scripts/validate_scafforge_contract.py`

Precise fix:

- add `CODEXSETUP`
- optionally add detection for invisible citation artifacts
- add static checks for critical prompt rails such as:
  - blocker language
  - approval gating language
  - anti-premature-summary wording

Why:

- if the project claims weak-model hardening, the validator should check for the most critical rails

### C4. Add a reference path validator

Files:

- new validator script or contract-validator extension

Precise fix:

- parse `SKILL.md` references and verify the referenced files exist

Why:

- broken references silently degrade agent behavior

### C5. Add a retrofit-flow smoke test

Files:

- `scripts/smoke_test_scafforge.py`

Precise fix:

- create a fixture that simulates an existing repo
- run the OpenCode-only bootstrap path
- verify it adds the operating layer without clobbering unrelated existing files

Why:

- the product is supposed to support both greenfield and retrofit flows

---

## Workstream D - Packaging, installability, and host adapter completion

### D1. Correct the host adapter model

Files:

- `adapters/manifest.json`
- `adapters/README.md`

Precise fix:

- keep host adapters only for host-layer usage
- remove the current semantic confusion where `opencode` is treated as if it were a host adapter entry but actually describes generated-repo runtime usage
- represent OpenCode as output/runtime documentation, not as a host install adapter

Why:

- the two-layer model must remain clean

### D2. Add the missing target host adapter surfaces

Files:

- adapter docs and manifest entries

Precise fix:

- ensure the supported host set explicitly includes:
  - GitHub Copilot CLI
  - Codex
  - Claude Code / Claude CLI
- for each, document:
  - install flow
  - invocation example
  - how provider/model choices should be passed
  - how the host should hand off into the generated OpenCode repo

Why:

- this is part of the live-usage promise the user explicitly asked for

### D3. Make package publication truthfully staged

Files:

- `package.json`
- adapter docs
- README release/install sections

Precise fix:

- if the package is not yet ready for public npm publishing, mark install docs as local/dev usage only
- if public release is part of this finalization target, remove `private: true` and make docs fully truthfully publishable

Why:

- installation guidance must not promise a mode that the package cannot currently support

### D4. Improve CLI wrapper usability

Files:

- `bin/scafforge.mjs`

Precise fix:

- refactor command dispatch to a map or `switch`
- add:
  - `audit-repo`
  - clearer subcommand help forwarding
- ensure help output remains readable and stable

Why:

- live usage depends on the wrapper being more than a thin technical stub

---

## Workstream E - Documentation and terminology closure

### E1. Remove invisible citation artifacts

Files:

- `README.md`
- `REVIEW-NOTES.md`

Precise fix:

- strip the private-use citation characters and any dead citation strings

Why:

- published docs should not contain hidden AI citation debris

### E2. Close stale or contradictory top-level docs

Files:

- `TASKS.md`
- `README.md`
- potentially `REVIEW-NOTES.md`

Precise fix:

- mark T-019 and T-020 as completed or move them to a completed/history section
- remove or revise any stale “current gaps” wording in README that no longer matches the implemented baseline

Why:

- agents and humans should not have to infer which doc is old and which is current

### E3. Add a terminology glossary

Files:

- either `README.md`, `AGENTS.md`, or a dedicated glossary doc referenced by both

Precise fix:

- define:
  - generator
  - generated repo
  - host
  - output profile
  - canonical brief
  - ticket manifest
  - workflow state
  - artifact
  - handoff
  - safe repair

Why:

- the earlier plan explicitly called for zero ambiguity in terms
- this is still not cleanly concluded

### E4. Quarantine historical devdocs from the active operating context

Files:

- `devdocs/`
- README or AGENTS note about historical status

Precise fix:

- choose one of:
  - mark `devdocs/` as historical/reference-only
  - relocate historical analysis docs
  - sanitize Windows-specific path content where it creates avoidable confusion

Why:

- the generated output is Linux-targeted
- historical planning artifacts should not accidentally become current operating instructions

---

## 6. User-approved scope expansions for this finalization pass

The user explicitly approved the following additions as part of finalization:

1. Make the package npm publish-ready now.
   - this means finalization includes truthful publication readiness, not only local live usage

2. Add `scafforge init` interactive wizard.
   - this is now in scope
   - it should gather the same explicit decisions the scaffold scripts currently require by flags

3. Add a generated `scaffold-manifest.json`.
   - this is now in scope
   - it should inventory the generated operating surfaces clearly

4. Add profile-based scaffold variants.
   - this is now in scope
   - the plan should implement at least a `minimum` and `full` profile contract, with `full` remaining the default unless later changed

5. Add a `compaction-preservation` plugin.
   - this is now in scope
   - it should preserve the key restart signals during context compaction

6. Make stage-gate allowpaths configurable.
   - this is now in scope
   - hardcoded pre-approval path rules should move to a small generated configuration surface with safe defaults

7. Move or quarantine historical `devdocs/` from the active repo surface.
   - this is now in scope
   - historical analysis material should stop competing with active operating documentation

The user did **not** approve `--dry-run` in this pass.

That remains out of scope unless requested later.

---

## 7. Recommended implementation order

### Phase F1 - Must-fix release blockers

Do first:

- `.gitignore`
- remove bytecode
- rename `CODEXSETUP`
- ban `CODEXSETUP` in validator
- fix `context_snapshot`
- align initial state files
- remove invisible citation artifacts
- add `engines`
- correct adapter manifest semantics
- add Claude adapter coverage

### Phase F2 - Safety and validation closure

Do second:

- tighten stage gate
- add handoff merge result reporting
- add placeholder scan
- add doctor-zero-findings smoke test
- add missing conformance files
- remove global `sed *`
- add timeout to `template_commit`

### Phase F3 - Installability and operator usability

Do third:

- decide publication stance for `private: true`
- improve CLI wrapper and add `audit-repo`
- add CONTRIBUTING
- fix stale top-level docs
- add terminology glossary

### Phase F4 - Approved scope expansions

Do after the blocker and release-hardening passes:

- `scafforge init` interactive wizard
- generated `scaffold-manifest.json`
- profile-based scaffold variants
- compaction-preservation plugin
- configurable stage-gate rules
- quarantine or move historical `devdocs/`

---

## 8. Definition of done for finalization

Scafforge is ready to move into live usage when:

1. No verified blocker from section 2.1 remains unresolved.

2. The generator passes:
   - contract validation
   - smoke test
   - doctor-zero-findings scaffold audit
   - retrofit smoke scenario

3. The package has truthful installation guidance for:
   - Copilot CLI
   - Codex
   - Claude Code / Claude CLI

4. Generated repos no longer contain:
   - `CODEXSETUP`
   - contradictory startup state
   - silent context snapshot drift
   - over-broad pre-approval write paths

5. Top-level docs no longer contradict implemented reality.

6. OpenCode-facing generated surfaces are explicitly re-checked against current OpenCode expectations as a final release gate.

7. The newly approved expanded surfaces also work correctly:
   - `scafforge init`
   - profile-based output selection
   - generated `scaffold-manifest.json`
   - configurable stage-gate paths
   - compaction-preservation behavior
   - quarantined historical docs policy

---

## 9. Proposed execution todos

- `finalization-release-hygiene` — Add `.gitignore`, remove bytecode, add package metadata, add contributor guide.
- `finalization-output-correctness` — Fix legacy markers, state inconsistencies, snapshot behavior, handoff merge reporting, and stage-gate loopholes.
- `finalization-validation-hardening` — Expand validator and smoke test coverage, including placeholders, doctor-zero-findings, and retrofit coverage.
- `finalization-host-adapters` — Complete and correct host adapter docs for Copilot, Codex, and Claude, and cleanly separate OpenCode runtime docs from host adapters.
- `finalization-doc-consistency` — Remove citation artifacts, close stale task/doc wording, add glossary, and quarantine historical devdocs.
- `finalization-publish-readiness` — Make `@scafforge/core` actually publish-ready, including truthful metadata, release docs, and install guidance.
- `finalization-init-wizard` — Add `scafforge init` as the guided entrypoint for collecting required scaffold decisions.
- `finalization-scaffold-manifest` — Generate a machine-readable manifest of scaffolded agents, tools, plugins, commands, and skills.
- `finalization-profiles` — Add profile-based scaffold variants while preserving a clear default contract.
- `finalization-compaction` — Add the compaction-preservation plugin and validate its behavior against the generated state model.
- `finalization-stage-gate-config` — Move pre-approval path rules into a safe generated configuration surface and keep enforcement strict by default.
- `finalization-devdocs-quarantine` — Move or quarantine historical devdocs so they no longer act like live operator guidance.

---

## 10. Resolved user decisions now baked into this plan

The user confirmed:

- publication target: make npm publish-ready now
- add `scafforge init`: yes
- add `--dry-run`: no
- add generated `scaffold-manifest.json`: yes
- complexity strategy: add profile-based scaffold variants
- add compaction-preservation plugin: yes
- make stage-gate allowpaths configurable: yes
- historical devdocs policy: move or quarantine them from the active repo surface

This plan should be copied verbatim to `devdocs/finalizationplan.md` for repository-visible tracking.
