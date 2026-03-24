# Reference Update Inventory

## Purpose

This file records the package files and references that need updating if Scafforge adopts the following direction:

- replace `repo-process-doctor` with `scafforge-audit` and `scafforge-repair`
- fold `pr-review-ticket-bridge` into the audit flow by default
- remove the package CLI and stop treating Scafforge as an npm-facing product
- remove the standalone refinement route
- keep the generated repo-local `review-audit-bridge` under `project-skill-bootstrap`
- add explicit post-audit/post-repair ticket follow-up
- write diagnosis outputs into the subject repo's `diagnosis/` folder

This is a planning inventory only. It does not change product files.

## Structural Clarifications

### Expected renames

- `repo-process-doctor` -> `scafforge-audit` and `scafforge-repair`

### Expected removals or fold-ins

- package CLI surface
- npm-facing product framing
- standalone `refinement` route
- `pr-review-ticket-bridge` as a standalone primary host-side workflow, unless a narrow PR-only helper is intentionally retained

### Expected ownership clarifications

- generated repo-local `review-audit-bridge` remains generated-repo functionality, not a Scafforge core skill
- ownership for that generated skill sits under `project-skill-bootstrap`
- larger guidance for that generated skill should live in its `references/` subfolder if needed
- diagnosis artifacts move to the subject repo's `diagnosis/` folder as the sole intentional file-creation exception during diagnosis

## Top-Level Package Files

### [AGENTS.md](C:/Users/PC/Documents/GitHub/Scafforge/AGENTS.md)

Needs updates for:

- default scaffold spine naming
- canonical workflow contract references
- managed repair and review flow wording
- `repo-process-doctor` boundary text
- `pr-review-ticket-bridge` boundary text
- removal of any standalone refinement route wording

### [README.md](C:/Users/PC/Documents/GitHub/Scafforge/README.md)

Needs updates for:

- product framing around diagnosis/repair
- package skill list and descriptions
- PR bridge references
- generated review-skill framing
- removal of all CLI installation and usage guidance
- removal of npm-facing framing where it no longer reflects product direction

### [package.json](C:/Users/PC/Documents/GitHub/Scafforge/package.json)

Needs updates for:

- removal of package CLI exposure
- removal or rewrite of CLI-related scripts
- removal of stale validation or repair command references if they assume the CLI remains

### [bin/scafforge.mjs](C:/Users/PC/Documents/GitHub/Scafforge/bin/scafforge.mjs)

Needs updates for:

- full removal if the CLI is removed
- otherwise, complete deprecation planning before deletion

### [scripts/validate_scafforge_contract.py](C:/Users/PC/Documents/GitHub/Scafforge/scripts/validate_scafforge_contract.py)

Needs updates for:

- renamed skill paths
- renamed flow-manifest expectations
- CLI-removal expectations
- removal of standalone refinement-route expectations
- added diagnosis/report/ticket-follow-up contract checks
- diagnosis output location expectations for repo-local `diagnosis/`

### [scripts/smoke_test_scafforge.py](C:/Users/PC/Documents/GitHub/Scafforge/scripts/smoke_test_scafforge.py)

Needs updates for:

- renamed skill/script paths
- removal of CLI assumptions
- new diagnosis-pack smoke coverage
- new ticket-follow-up smoke coverage where applicable
- no-refinement-route expectations if currently baked into flow validation

## Routing and Orchestration Files

### [skills/scaffold-kickoff/SKILL.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/scaffold-kickoff/SKILL.md)

Needs updates for:

- route classification for diagnosis vs repair
- replacement of `repo-process-doctor`
- routing into `scafforge-audit` and `scafforge-repair`
- completion criteria and required outputs
- removal of standalone refinement-route behavior

### [skills/skill-flow-manifest.json](C:/Users/PC/Documents/GitHub/Scafforge/skills/skill-flow-manifest.json)

Needs updates for:

- split of one doctor entry into audit and repair entries
- removal or folding of `pr-review-ticket-bridge`
- updated sequence descriptions
- updated optional-extension inventory
- removal of refinement-routing entries

### [skills/agent-prompt-engineering/SKILL.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/agent-prompt-engineering/SKILL.md)

Needs updates for:

- references to post-hardening audit/repair flow

### [skills/agent-prompt-engineering/references/prompt-contracts.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/agent-prompt-engineering/references/prompt-contracts.md)

Needs updates for:

- any flow references that still point at the old doctor or refinement model

### [skills/handoff-brief/SKILL.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/handoff-brief/SKILL.md)

Needs updates for:

- validation-status references to the old doctor step
- closeout wording when diagnosis/repair naming changes

## Doctor-to-Audit/Repair Internal Tree

### [skills/repo-process-doctor/SKILL.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-process-doctor/SKILL.md)

Needs updates for:

- replacement by new audit/repair skill contracts
- removal of mixed-mode wording
- removal of CLI examples
- updated required outputs
- audit-side four-report contract
- repair-side ticket follow-up and provenance contract

### [skills/repo-process-doctor/agents/openai.yaml](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-process-doctor/agents/openai.yaml)

Needs updates for:

- split or regeneration for new skill names
- refreshed display metadata and prompts

### [skills/repo-process-doctor/references/process-smells.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-process-doctor/references/process-smells.md)

Needs updates for:

- audit-only ownership if retained under the new audit skill
- plain-English naming for execution-related findings where appropriate

### [skills/repo-process-doctor/references/repair-playbook.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-process-doctor/references/repair-playbook.md)

Needs updates for:

- repair-only ownership if retained under the new repair skill
- removal of CLI wording
- explicit ticket follow-up path after audit/repair

### [skills/repo-process-doctor/references/safe-stage-contracts.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-process-doctor/references/safe-stage-contracts.md)

Needs updates for:

- terminology aligned with the repair skill

### [skills/repo-process-doctor/scripts/audit_repo_process.py](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-process-doctor/scripts/audit_repo_process.py)

Needs updates for:

- rename or re-home under the audit skill
- help text and headers aligned with the new audit identity
- cross-platform interpreter discovery fixes
- startup-import and test-run fixes
- less opaque user-facing finding names

### [skills/repo-process-doctor/scripts/apply_repo_process_repair.py](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-process-doctor/scripts/apply_repo_process_repair.py)

Needs updates for:

- rename or re-home under the repair skill
- help text aligned with the new repair identity
- provenance text updated for the new naming
- explicit follow-up ticket routing

## Ticket-System Surfaces

### [skills/ticket-pack-builder/SKILL.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/ticket-pack-builder/SKILL.md)

Needs updates for:

- explicit post-audit/post-repair remediation-oriented follow-up
- guidance on guarded ticket creation instead of raw manifest edits where tools exist
- clear status/verification expectations for remediation tickets
- removal of any standalone refinement-route framing that survives only as a route name rather than a contained capability

### [skills/repo-scaffold-factory/assets/project-template/tickets/README.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/tickets/README.md)

Needs updates for:

- documented post-audit/post-repair ticket path
- proof and source-finding requirements

### [skills/repo-scaffold-factory/assets/project-template/tickets/manifest.json](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/tickets/manifest.json)

Needs review for:

- status and queue expectations that may drift when audit/repair and remediation tickets become explicit

### [skills/repo-scaffold-factory/assets/project-template/tickets/templates/TICKET.template.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/tickets/templates/TICKET.template.md)

May need updates for:

- optional remediation context fields or sections if audit-origin tickets should carry richer structured context

### [skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts)

Needs review for:

- whether current guardrails already cover the desired remediation-ticket flow
- whether audit/repair should emit structured inputs that this tool can consume directly

### [skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts)

Needs review for:

- workflow-state assumptions tied to current doctor, review, or ticket-follow-up behavior
- any support needed for diagnosis-origin remediation tickets or process logs

### [skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-ticket-creator.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-ticket-creator.md)

Needs review for:

- whether its current narrow backlog-verifier framing must broaden for audit/repair-origin remediation tickets

## PR Review and Generated Review Surfaces

### [skills/pr-review-ticket-bridge/SKILL.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/pr-review-ticket-bridge/SKILL.md)

Needs updates for:

- retirement, folding, or sharp narrowing into an optional PR-only helper

### [skills/pr-review-ticket-bridge/references/review-contract.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/pr-review-ticket-bridge/references/review-contract.md)

Needs updates for:

- retirement, folding, or narrowing that matches the parent skill decision

### [skills/project-skill-bootstrap/SKILL.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/project-skill-bootstrap/SKILL.md)

Needs updates for:

- explicit ownership of the generated repo-local `review-audit-bridge`
- generation or repair of that repo-local skill and its `references/` tree
- expectations for repo-local review logs explaining what went wrong in the live project process

### [skills/project-skill-bootstrap/references/local-skill-catalog.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/project-skill-bootstrap/references/local-skill-catalog.md)

Needs updates for:

- generated local review-skill naming and description
- reference to process-log output expectations if added

### [skills/repo-scaffold-factory/assets/project-template/.opencode/skills/review-audit-bridge/SKILL.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/skills/review-audit-bridge/SKILL.md)

Needs updates for:

- ownership wording that keeps it clearly repo-local rather than core-package
- scope around self-review, poor-implementation ticket recommendations, and process-log output

### [skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md)

Needs updates for:

- references to `review-audit-bridge`

### [skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-security.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-security.md)

Needs updates for:

- references to `review-audit-bridge`

### [skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-tester-qa.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-tester-qa.md)

Needs updates for:

- references to `review-audit-bridge`

### [skills/review-audit-bridge/agents/openai.yaml](C:/Users/PC/Documents/GitHub/Scafforge/skills/review-audit-bridge/agents/openai.yaml)

Needs review for:

- whether this is stale package-level material that should be removed or relocated once the generated repo-local ownership is clarified

### [skills/repo-scaffold-factory/references/opencode-conformance-checklist.json](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/references/opencode-conformance-checklist.json)

Needs updates for:

- generated review-skill name/path expectations

## Template and Generated-Repo Documentation Fallout

### [skills/repo-scaffold-factory/assets/project-template/README.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/README.md)

Needs updates for:

- diagnosis, audit, repair, and ticket-follow-up wording exposed to generated repos

### [skills/repo-scaffold-factory/assets/project-template/AGENTS.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/AGENTS.md)

Needs updates for:

- generated workflow backbone wording if audit/repair naming or review-skill ownership changes

### [skills/repo-scaffold-factory/assets/project-template/START-HERE.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/START-HERE.md)

Needs updates for:

- restart guidance that references review, audit, repair, or diagnosis outputs

### [skills/repo-scaffold-factory/assets/project-template/docs/process/workflow.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/docs/process/workflow.md)

Needs updates for:

- generated workflow descriptions if audit/repair naming or ticket follow-up changes

### [skills/repo-scaffold-factory/assets/project-template/docs/process/tooling.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/docs/process/tooling.md)

Needs updates for:

- tooling guidance related to diagnosis artifacts, review skill use, or ticket follow-up

### [skills/repo-scaffold-factory/assets/project-template/docs/process/agent-catalog.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/docs/process/agent-catalog.md)

Needs updates for:

- reviewer/tester references if they route through the generated review skill

### [skills/repo-scaffold-factory/assets/project-template/docs/process/git-capability.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/docs/process/git-capability.md)

Needs review for:

- any workflow references affected by diagnosis output or review/repair boundary changes

### [skills/repo-scaffold-factory/assets/project-template/docs/process/model-matrix.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/docs/process/model-matrix.md)

Needs review for:

- any model-role guidance that references the old review or doctor naming

### [skills/repo-scaffold-factory/assets/project-template/.opencode/commands/issue-triage.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/commands/issue-triage.md)

Needs updates for:

- remediation-ticket and review-flow wording if old doctor/bridge terms remain

### [skills/repo-scaffold-factory/assets/project-template/.opencode/commands/reverify-ticket.md](C:/Users/PC/Documents/GitHub/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/commands/reverify-ticket.md)

Needs updates for:

- verification wording if old doctor/bridge terms remain

## Planning and Existing Task Docs

### [Tasks/SCAFFORGE-PLAN-REVIEW-REPORT.md](C:/Users/PC/Documents/GitHub/Scafforge/Tasks/SCAFFORGE-PLAN-REVIEW-REPORT.md)

Needs review for:

- stale assumptions about current skill names, routes, or CLI surface

### [Tasks/SCAFFORGE-REMEDIATION-PLAN.md](C:/Users/PC/Documents/GitHub/Scafforge/Tasks/SCAFFORGE-REMEDIATION-PLAN.md)

Needs review for:

- stale assumptions about current skill names, routes, or ticket follow-up behavior

### [Tasks/SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md](C:/Users/PC/Documents/GitHub/Scafforge/Tasks/SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md)

Needs review for:

- stale assumptions about route naming, doctor ownership, or CLI framing

## Planning and Support Docs Under `out/`

The planning docs also need to stay internally consistent:

- [DIAGNOSIS-4-REPORT-PLAN.md](C:/Users/PC/Documents/GitHub/Scafforge/out/DIAGNOSIS-4-REPORT-PLAN.md)
- [DIAGNOSIS-ARCHITECTURE-AND-NAMING-PROPOSAL.md](C:/Users/PC/Documents/GitHub/Scafforge/out/DIAGNOSIS-ARCHITECTURE-AND-NAMING-PROPOSAL.md)
- [DIAGNOSIS-PLAN-ADDENDUM.md](C:/Users/PC/Documents/GitHub/Scafforge/out/DIAGNOSIS-PLAN-ADDENDUM.md)
- [DIAGNOSIS-EVIDENCE-AND-NON-TAINT-RULES.md](C:/Users/PC/Documents/GitHub/Scafforge/out/DIAGNOSIS-EVIDENCE-AND-NON-TAINT-RULES.md)

## Implementation Notes

- If the package creates new skills rather than renaming in place, use the local `skill-creator` guidance during implementation.
- This inventory should be treated as a working migration checklist, not a complete line-by-line patch plan.
