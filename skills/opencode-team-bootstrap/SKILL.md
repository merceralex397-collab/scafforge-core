---
name: opencode-team-bootstrap
description: Design and generate a project-specific OpenCode agent team with specialized agents, tools, plugins, commands, and skills tailored to the project type and stack. Use after the base scaffold exists to customize the generic agent templates into project-aware specialists.
---

# OpenCode Team Bootstrap

Use this skill to design the agent team for the project. This is creative work — you analyze the project and customize the agents, tools, and plugins to match.

## Mode selection

- If this skill is reached from `scaffold-kickoff` after a fresh scaffold render, use the design path for a new project-specific team.
- If the repo already exists and the goal is to add or repair the `.opencode/` operating layer, use the retrofit path.
- If it is unclear whether the user wants a fresh team design pass or repair of an existing operating layer, ask the user before choosing a mode.

## Context

The `repo-scaffold-factory` script generates a base set of generic agent templates. `project-skill-bootstrap` then creates the repo-local skill pack those agents are allowed to use. In retrofit mode, this skill restores `.opencode/` first so `project-skill-bootstrap` has a concrete local skill layer to rewrite. Your job is to read the canonical brief, use the already-generated local skills when they exist, and customize the agents to be project-specific.

## Procedure

### 1. Read the canonical brief

Read `docs/spec/CANONICAL-BRIEF.md` to understand:
- What kind of project this is (web app, API, MCP server, CLI tool, library, etc.)
- What stack/framework is being used
- What domains the project spans (UI, backend, database, infrastructure, etc.)
- What the acceptance criteria are

### 2. Plan the agent team

Decide which agents this project needs. Start from the baseline and add/modify based on project type.

**Baseline agents (always present):**
- `team-leader` — the single visible coordinator, delegates to specialists
- `lane-executor` — hidden write-capable worker for lease-bound parallel work
- `planner` — turns tickets into implementation plans
- `plan-review` — approves/rejects plans before implementation
- `implementer` — implements the approved plan (at least one, may have multiple)
- `reviewer-code` — code review for correctness and regressions
- `reviewer-security` — security review for trust boundaries and secrets
- `tester-qa` — QA validation and closeout readiness
- `docs-handoff` — closeout artifact synchronization
- `backlog-verifier` — re-checks completed tickets after a workflow or process upgrade
- `ticket-creator` — creates guarded follow-up tickets only from verifier proof

**Project-specific agents (add based on project type):**

For UI/frontend projects:
- Additional implementer for component work (e.g., `implementer-ui`)
- Accessibility reviewer
- Visual regression agent

For API projects:
- API implementer with schema awareness
- Contract validation agent

For MCP server projects:
- Protocol implementer with MCP spec knowledge
- Tool definition specialist

For database-heavy projects:
- Migration specialist
- Schema reviewer

For CLI/library projects:
- API surface reviewer
- Documentation specialist

For game or asset-heavy projects:
- Read `.opencode/meta/asset-pipeline-bootstrap.json` if it exists before finalizing the agent set.
- If the seeded routes include `blender-mcp`, add a dedicated `blender-asset-creator` implementer/subagent scoped to Blender-MCP work.
- If the seeded routes include `free-open`, consider an `asset-sourcer` specialist for license-aware sourcing and import prep.
- If the repo relies on Godot-native finish work, ensure at least one implementer prompt explicitly owns theme/VFX/import polish under the repo's asset pipeline.

You may create multiple implementer-type agents for different domains within a single project, but keep the total agent count conservative unless the canonical brief proves genuinely disjoint domains.

Default to one visible team leader with a shallow hidden specialist topology. Keep `lane-executor` as the default hidden worker for bounded parallel implementation. Only introduce a manager or section-leader hierarchy when the canonical brief shows strong non-overlapping domains that justify the extra coordination layer. Treat that hierarchy as advanced project-specific customization, not as a first-class scaffold profile.

**Utility agents (include based on need):**
- `utility-explore` — repo evidence gathering
- `utility-github-research` — GitHub-focused research
- `utility-shell-inspect` — read-only shell commands
- `utility-summarize` — evidence compression
- `utility-ticket-audit` — ticket/state consistency
- `utility-web-research` — external technical research

Omit utility agents that aren't useful for the project.

### 3. Customize agent prompts

For EVERY agent, rewrite the generic prompt to be project-specific:

**What to customize:**
- **Description**: mention the actual project and what the agent does for it
- **First instruction**: state the agent's role in the context of THIS project
- **Tool permissions**: adjust based on what the agent actually needs
- **Skill allowlists**: reference project-specific skills
- **Skill allowlists**: reference only repo-local skills that already exist
- **Task allowlists**: reference the actual agents that exist (including any new ones)
- **Bash allowlists**: add project-specific commands (e.g., `cargo test*` for Rust, `flutter test*` for Flutter)
- When asset-pipeline metadata exists, delegation briefs must mention the seeded asset surfaces and route-specific ownership instead of generic "art/content" wording.

**Inject stack-specific implementation notes:**
- Rewrite the implementer template's `Stack-specific notes` block so it no longer contains scaffold placeholder text.
- The rewritten notes must cover: how to build this stack, how to run a basic verification for this stack, common stack pitfalls to avoid, and which configuration files need special care.
- Synthesize these notes from `docs/spec/CANONICAL-BRIEF.md`, the actual repo layout, and the selected stack rather than pasting generic catalog text.
- Use the following stacks as a reference catalog when synthesizing project-specific guidance: Godot, Java/Android, C/C++, .NET, Node.js, Python, Rust, and Go.
- Ensure the team leader's project-specific delegation briefs include stack-aware build and verification commands instead of generic "make sure it works" wording.
- Keep the generated delegation chain in `docs/AGENT-DELEGATION.md` aligned with the detected stack adapters and their canonical verification commands.

**What NOT to change:**
- Model assignments (`__PLANNER_MODEL__`, etc. are already substituted by the script)
- Hidden/visible settings (only team-leader should be visible)
- The fundamental stage-gate workflow (`planning -> plan_review -> implementation -> review -> qa -> smoke-test -> closeout`)

**Example customization for a React web app:**

The generic planner says: "You produce decision-complete plans for a single ticket."

Customize to: "You produce decision-complete plans for a single ticket in the Example App React frontend. Plans must specify which components are affected, what state management changes are needed, and what test scenarios to cover. Reference the component tree in docs/spec/CANONICAL-BRIEF.md."

### 4. Write agent files

Write each agent to `.opencode/agents/<prefix>-<role>.md` with proper YAML frontmatter.

Verify:
- Every agent has `description`, `model`, `mode`, `hidden`, `temperature`, `top_p`
- Tool permissions are explicit (deny by default, allow specifically)
- Skill allowlists reference only skills that already exist in `.opencode/skills/`
- Task allowlists reference only agents that exist in `.opencode/agents/`
- When `.opencode/meta/asset-pipeline-bootstrap.json` exists, the generated agent set and delegation doc agree with its route hints instead of ignoring them.
- Read-only agents (planner, reviewers, QA) have `write: false, edit: false`
- Only implementer and docs-handoff have `write: true, edit: true`
- The team leader resolves `ticket_lookup.transition_guidance` before changing lifecycle state
- The team leader treats bootstrap-not-ready state as a hard gate and routes `environment_bootstrap` before normal lifecycle work
- The team leader stops on repeated lifecycle-tool contradictions instead of probing alternate stage or status values
- The team leader does not author planning, implementation, review, QA, or smoke-test artifact bodies on behalf of specialists
- The team leader prompt includes explicit stop conditions, contradiction-resolution rules, ownership boundaries, and verdict-checking rules that match the generated workflow tools
- The implementer prompt includes rewritten stack-specific notes instead of leaving scaffold placeholder text behind
- Agents do not instruct themselves to use slash commands as internal workflow steps

Also generate `docs/AGENT-DELEGATION.md` as a derived project-specific document.
It must document:
- the actual generated agent team for this repo
- the delegation chain from team leader through implementation, review, QA, smoke-test, and closeout
- what each agent can and cannot do
- the escalation path when an agent is blocked or tool state contradicts itself
- the restart procedure: read `START-HERE.md`, run `ticket_lookup`, identify the active ticket, then resume from canonical state

Treat `docs/AGENT-DELEGATION.md` as derived from the actual agent set you created in `.opencode/agents/`, not as a generic boilerplate file.

### 5. Review project-specific tools

The base scaffold generates these standard tools (keep them all):
- `artifact_write.ts` — write canonical artifacts
- `artifact_register.ts` — register artifact metadata
- `context_snapshot.ts` — generate context snapshots
- `environment_bootstrap.ts` — install and verify project/toolchain/test prerequisites
- `handoff_publish.ts` — publish START-HERE handoff
- `issue_intake.ts` — route post-completion defects through reopen or follow-up flow
- `skill_ping.ts` — record skill invocations
- `ticket_claim.ts` — claim a lease for lane-bound write work
- `ticket_create.ts` — guarded follow-up or remediation ticket creation
- `ticket_lookup.ts` — resolve tickets from manifest
- `ticket_release.ts` — release a lease after write work completes
- `ticket_reopen.ts` — reopen a ticket when original accepted scope is no longer true
- `ticket_reverify.ts` — restore trust on historical completion after new evidence
- `ticket_update.ts` — update ticket state with stage gates
- `.opencode/lib/workflow.ts` — shared types and utilities

Consider whether the project needs additional tools:
- Database projects might need a migration status tool
- API projects might need a schema validation tool
- Component projects might need a component scaffolding tool

If additional tools are warranted, create them following the patterns in `.opencode/lib/workflow.ts`.

### 6. Review plugins

The base scaffold generates these standard plugins (keep them all):
- `invocation-tracker.ts` — audit logging
- `session-compactor.ts` — context preservation on compaction
- `stage-gate-enforcer.ts` — blocks unsafe operations before plan approval
- `ticket-sync.ts` — records ticket state changes
- `tool-guard.ts` — blocks dangerous operations

These are generic and work for any project. Only add project-specific plugins if genuinely needed.

### 7. Review commands

The base scaffold generates:
- `kickoff.md` — start the autonomous planning cycle
- `resume.md` — resume from the latest state
- `bootstrap-check.md` — verify environment bootstrap readiness
- `issue-triage.md` — route defects found after prior completion
- `reverify-ticket.md` — restore trust on historical completion
- `plan-wave.md` — choose safe parallel candidates for the next wave
- `run-lane.md` — run one bounded lane through lease-based execution
- `join-lanes.md` — reconcile completed parallel lanes into one foreground path

Customize these to reference project-specific agents and skills.
If the generated repo includes stack-specific bootstrap or verification entrypoints, make those references match the detected adapter family instead of a generic default.

## Output contract

Before leaving this skill, confirm all of these are true:
- `.opencode/agents/` contains only the intended project-specific agent set for this repo
- every agent allowlist references only skills and agents that actually exist in the generated repo
- the team leader owns routing and lease control, while specialists stay within their bounded write or read-only roles
- commands reference current agents and current workflow surfaces without becoming autonomous internal workflow steps
- `docs/AGENT-DELEGATION.md` matches the actual generated agent set and restart flow for this repo

## Repair follow-on artifact

When this skill runs as a `scafforge-repair` follow-on regeneration pass, read `.opencode/meta/repair-follow-on-state.json` and, after the agent team, commands, and related prompt surfaces are actually refreshed for the current repair cycle, write:

- `.opencode/state/artifacts/history/repair/opencode-team-bootstrap-completion.md`

Use this minimal shape so the public repair runner can auto-recognize `opencode-team-bootstrap` completion for the current repair cycle on the next run:

```md
# Repair Follow-On Completion

- completed_stage: opencode-team-bootstrap
- cycle_id: <cycle_id from .opencode/meta/repair-follow-on-state.json>
- completed_by: opencode-team-bootstrap

## Summary

- Regenerated the project-specific OpenCode agent team and related command/tool routing for the current repair cycle.
```

Do not emit this artifact speculatively. Only write it once the agent-team regeneration work is actually complete for the current repair cycle.

## Team design principles

- One visible team leader, all specialists hidden
- Keep the default topology shallow: one visible coordinator plus hidden specialists, with `lane-executor` as the default bounded parallel write worker
- Keep total agent count conservative unless the brief proves disjoint domains
- No `ask` permissions — agents don't prompt the user
- Explicit `permission.task` allowlists — agents can only delegate to named agents
- Commands are for humans only
- Agents must not use `/kickoff`, `/resume`, or other `.opencode/commands/` files as internal workflow workarounds
- Tools/plugins handle autonomous internal flow
- Workflow state and ticket tools for stage control, not raw file edits
- Lease-based write execution should be operational, not just described in prompt prose

## After this step

Continue to `../agent-prompt-engineering/SKILL.md` as directed by `../scaffold-kickoff/SKILL.md`.

## References

- `references/agent-system.md` for the team structure
- `references/tools-plugins-mcp.md` for the tool/plugin/command layer
- `../repo-scaffold-factory/assets/project-template/` for the base templates
- `../agent-prompt-engineering/SKILL.md` for prompt hardening rules
