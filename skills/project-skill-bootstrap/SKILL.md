---
name: project-skill-bootstrap
description: Create project-local OpenCode skills populated with actual project data, stack-specific conventions, downstream model operating guidance, and domain-specific procedures. Use after scaffolding to replace generic skill placeholders with real project-aware guidance that helps agents work effectively in this specific repo.
---

# Project Skill Bootstrap

Use this skill to create the repo-local `.opencode/skills/` layer with actual project content.

## Goals

- Make project context easy to reload for any agent or session
- Encode actual stack and domain standards, not generic placeholders
- Reduce ambiguity for weaker models
- Keep prompts short by moving stable procedure into local skills
- Keep project-local skills aligned with ticket tools and workflow state
- Keep repo-local synthesized skills separate from package-level skill evolution

## Operating modes

- **greenfield full pass**: populate the baseline skill pack and all required synthesized skills in one invocation
- **repair or regeneration**: refresh baseline skills and add or revise synthesized skills for an existing repo when needed

## Mode selection

- If this skill is reached from `scaffold-kickoff` during greenfield generation, use the full greenfield pass. Do not split baseline population and synthesis into separate revisits.
- If invoked directly for an existing repo, use repair or regeneration.
- If the repo is missing `.opencode/skills/`, do not start here. Run `../opencode-team-bootstrap/SKILL.md` first so the local skill layer exists before you rewrite it.
- In repair or regeneration mode, refresh required synthesized skills as well as baseline skills. Do not leave an existing synthesized skill untouched when current repo evidence or metadata shows it is required and stale.

## Greenfield full-pass procedure

The base scaffold generates generic skill templates. You must populate them with actual project data.

### 1. Read the canonical brief

Read `docs/spec/CANONICAL-BRIEF.md` for project facts, stack decisions, and constraints.

### 2. Populate baseline skills

For each baseline skill in `.opencode/skills/`, rewrite the SKILL.md with actual project content:

**project-context** — Replace generic reading order with actual project-specific context:
- Actual project summary (what this project is)
- Actual canonical doc paths
- Current project state
- Key architectural decisions from the brief

**repo-navigation** — Replace generic paths with actual project structure:
- Actual directory layout (as generated)
- Key files and what they contain
- Common queries agents will need

**stack-standards** — Replace the `__STACK_LABEL__` placeholder with REAL rules:
- Actual framework/language conventions (e.g., "Use React functional components with TypeScript")
- Actual testing commands (e.g., "Run tests with `pnpm test`")
- Actual linting/formatting rules
- Actual code-quality gate commands for review and QA (build, lint, type-check, reference-integrity)
- Stack-specific execution commands surfaced by the generated adapter and environment bootstrap flow
- Target-completion or release-proof commands when the brief declares a platform-specific artifact path such as a Godot Android APK export
- Code style preferences from the brief
- Do not leave placeholder text behind; a baseline skill that still says "Replace this file..." is invalid
- Pull framework-specific rules from the canonical brief, repo instructions, and current code evidence
- For FastAPI repos, include concrete dependency-injection guidance when the repo evidence shows specific patterns or prior failures

**model-operating-profile** — Write model-profile-specific operating guidance:
- instruction style that matches the selected downstream model profile
- formatting expectations that make responses easier for weaker models to follow
- blocker behavior and evidence standards
- example-shaped output expectations where helpful

**ticket-execution** — Keep the standard lifecycle but add project-specific notes:
- Make it the canonical state-machine explainer for the generated repo
- State the exact stage order: `planning -> plan_review -> implementation -> review -> qa -> smoke-test -> closeout`
- Tell agents to read `ticket_lookup.transition_guidance` before calling `ticket_update`
- Tell agents that bootstrap readiness is a pre-lifecycle gate: when `ticket_lookup.bootstrap.status` is not `ready`, the next required action is `environment_bootstrap`, then a fresh `ticket_lookup`
- State that only Wave 0 setup work may claim a write-capable lease before bootstrap is ready
- State that the team leader owns `ticket_claim` and `ticket_release`, while specialists write only inside the already-active lease
- Tell agents to stop on repeated lifecycle errors instead of probing alternate stage or status values
- Define stage-artifact ownership by specialist
- State that `smoke_test` is the only legal producer of smoke-test artifacts
- State that smoke-test scope comes from the ticket acceptance criteria when they already name executable smoke commands
- State that process-remediation and reverification tickets must keep smoke-test scope limited to commands that are valid at the repo's current backlog state instead of broadening into product boot checks that are expected to fail while prerequisite feature tickets remain unfinished
- State that if execution or validation cannot run, the agent must return a blocker instead of manufacturing PASS evidence
- State that missing host prerequisites such as `uv`, `pytest`, `rg`, git identity, or service binaries are blockers that must be classified explicitly instead of worked around
- Include an explicit `Failure recovery paths` section covering review, QA, and smoke-test FAIL / REJECT / BLOCKED / unclear-verdict routing
- State that when `ticket_lookup.transition_guidance.recovery_action` is present, agents must follow that recovery path instead of the normal happy-path transition
- State that `smoke_test` is the only stage that may produce passing smoke evidence and that agents must not fabricate expected-results-as-PASS artifacts
- Clarify that slash commands are human entrypoints, not internal autonomous workflow tools
- Add remediation closeout rules: tickets created from audit or review findings must record `finding_source`, rerun the original failing check before closeout, and refuse closure when the finding-specific check still fails
- Preserve the canonical ticket-execution structure from the scaffold template; extend it with repo-specific command expectations instead of replacing it with a thinner summary

**review-audit-bridge** — Keep this generated skill repo-local and advisory-only, then add project-specific review and QA expectations:
- Repo-specific review commands, validation commands, and artifact paths
- Repo-specific code-quality commands for review and QA: build, lint, type-check, reference-integrity, and test-collection or smoke checks
- Repo-specific rerun guidance for original finding-producing commands when a remediation ticket carries `finding_source`
- Security-sensitive areas that need explicit attention
- Approval vs blocker rules for code review, security review, and QA
- Explicit blocker behavior when required validation commands cannot run
- Guidance for writing a repo-local process log under `diagnosis/` or the generated repo's chosen review-log path when workflow misuse or weak implementation quality needs to be explained
- Guidance for recommending remediation or reverification tickets without becoming the canonical ticket owner itself
- Guidance that review or QA verdicts must be FAIL when required build, lint, or reference-integrity commands fail, and that remediation reviews must rerun the original finding-producing command before approval

**docs-and-handoff** — Add project-specific doc paths and conventions

**workflow-observability** — Keep as-is (generic is fine for observability)

**research-delegation** — Keep as-is (generic is fine for research patterns)

**local-git-specialist** — Add project-specific branch conventions if specified in brief

**isolation-guidance** — Keep as-is unless brief specifies isolation requirements

### 3. Analyze synthesis needs

From the canonical brief, generated repo structure, and local references, identify whether the project needs additional stack- or domain-specific skills beyond the baseline pack.

When the canonical brief includes a Product Finish Contract (section 13) that forbids placeholder output in the final product, identify whether a finish-pipeline skill is warranted. This skill should encode:
- the stack-specific content pipeline for the repo (asset formats, tooling, import conventions)
- the finish acceptance signals from the canonical brief
- guidance on what constitutes placeholder versus real output for this project's stack
- any licensing or provenance gates that must be verified before content is committed

Do not synthesize a finish-pipeline skill when the finish contract explicitly allows placeholder or procedural output as final output.

When `.opencode/meta/asset-pipeline-bootstrap.json` exists, treat it as the canonical machine-readable summary of the repo's seeded asset routes and asset-truth surfaces. Use it to decide whether the repo needs synthesized skills such as:
- `asset-description`
- `blender-mcp-workflow`
- a stack-specific finish-pipeline or game-content skill

Those synthesized skills must reference the actual seeded repo surfaces (`assets/requirements.json`, `assets/pipeline.json`, `assets/manifest.json`, `assets/workflows/`, `assets/qa/`, `assets/PROVENANCE.md`, `assets/briefs/`) instead of re-describing a hypothetical directory layout.
When the metadata's `required_skills` includes one of these synthesized skills, that skill is mandatory output for the current generation or repair pass.
When the metadata's `suggested_skills` includes one of these synthesized skills, treat it as required output unless newer repo evidence proves the route no longer applies.

### 3a. Keep package and repo-local skill boundaries separate

- Solve repo-specific stack, domain, and workflow guidance in repo-local skills.
- If the gap would change Scafforge behavior across multiple repos, do not invent a new Scafforge package skill from inside this repo generation pass. Route that evidence through `../../references/skill-evolution-policy.md` instead.
- Prefer extending an existing repo-local skill when the same owner and trigger already exist. Create a new synthesized skill only when it gives this repo a genuinely distinct workflow.

When synthesizing **`blender-mcp-workflow`** for repos that route assets through `blender-agent`, treat `Scafforge/skills/asset-pipeline/SKILL.md` and `Scafforge/skills/asset-pipeline/agents/blender-asset-creator.md` as the authoritative operating contract. The generated local skill must:
- describe Blender mutating calls as **stateless** unless the repo evidence explicitly proves a different execution model
- require `output_blend` on every mutating call and require the next mutating call to reuse the returned `persistence.saved_blend` as `input_blend`
- tell agents to stop and retry the same step when a mutating response is ephemeral, omits `output_blend`, or returns no `persistence.saved_blend`
- require a first-chain proof before any repo declares a Blender-MCP bridge defect: `project_initialize` must save a `.blend`, the next mutating call must reuse that saved path as `input_blend`, and `.blender-mcp/audit/*.jsonl` must show non-null `input_blend` / `output_blend` on the recorded `job_start`
- use the seeded repo asset surfaces (`assets/briefs/`, `assets/models/`, `assets/workflows/`, `assets/manifest.json`, `assets/qa/`, `assets/PROVENANCE.md`) and the actual MCP tool names present in the repo
- tell agents to use the repo's configured `blender_agent` MCP entry from `opencode.jsonc` rather than inventing an ad hoc launch command when the managed MCP surface already exists
- classify inline Python as a blocker unless `environment_probe` or current config evidence shows it is enabled
- avoid invented session-based guidance such as `blender_session_*` tools unless those tools are actually present and documented in the repo

### 4. Review reference patterns

Use project documentation, framework documentation, package references, and other external research as reference material only. Review patterns that match the selected stack and workflow, then synthesize repo-specific procedure from that evidence.

Do not install external skills directly. Use external material as reference only.
Do not copy external skill bodies verbatim into repo-local output; distill the useful concept into repo-specific guidance.

### 5. Synthesize project-specific skills

Create only the synthesized skills the project actually needs.

Examples:
- For a React project: `component-patterns` with the repo's component conventions
- For an API project: `api-contracts` with the repo's schema format and validation rules
- For a database project: `migration-safety` with the repo's DB engine specifics
- For a testing-heavy project: `test-patterns` with the repo's test runner and fixture conventions
- For a deployment project: `deploy-safety` with the repo's deployment path

### 6. Quality rules for synthesized skills

- Each synthesized skill must be repo-specific, not generic paraphrasing of docs
- Prefer procedure over reference dumping
- Each synthesized skill must justify its existence
- Keep total skill count manageable
- Merge overlapping candidates instead of generating two skills that share the same owner and trigger
- Every synthesized skill must have proper YAML frontmatter
- Every synthesized skill description must be concrete and selection-specific
- Do not use vague descriptions such as "help with this stack" or "general project guidance"
- No generated local skill may retain scaffold placeholder text after greenfield generation or repair/regeneration
- Synthesized `blender-mcp-workflow` skills must preserve the stateless persistence contract exactly; a session-oriented Blender skill that omits `input_blend` / `output_blend` chaining is invalid

### 7. Write updated skills

Write each updated skill to `.opencode/skills/<name>/SKILL.md`.
Each skill MUST have YAML frontmatter with `name` and `description`.
If `review-audit-bridge` needs heavier examples or review policy detail, place that material in `.opencode/skills/review-audit-bridge/references/` rather than bloating the skill body.

## Output contract

Before leaving this skill, confirm all of these are true:
- every baseline local skill exists under `.opencode/skills/` and no baseline skill still contains scaffold placeholder text
- `.opencode/skills/model-operating-profile/SKILL.md` exists and matches the selected downstream model profile
- `.opencode/skills/ticket-execution/SKILL.md` matches the current lifecycle contract, lease ownership rules, bootstrap-first routing, repeated-contradiction stop rules, failure recovery paths, smoke ownership rules, and blocker behavior
- every synthesized skill required by `.opencode/meta/asset-pipeline-bootstrap.json` or equivalent repo evidence exists and has been refreshed for the current repair/generation pass
- any synthesized skill is repo-specific, has valid frontmatter, and is justified by project evidence

## Repair follow-on artifact

When this skill runs as a `scafforge-repair` follow-on regeneration pass, read `.opencode/meta/repair-follow-on-state.json` and, after the repo-local skill pack is actually refreshed for the current repair cycle, write:

- `.opencode/state/artifacts/history/repair/project-skill-bootstrap-completion.md`

Use this minimal shape so the public repair runner can auto-recognize `project-skill-bootstrap` completion for the current repair cycle on the next run:

```md
# Repair Follow-On Completion

- completed_stage: project-skill-bootstrap
- cycle_id: <cycle_id from .opencode/meta/repair-follow-on-state.json>
- completed_by: project-skill-bootstrap

## Summary

- Regenerated the repo-local skill pack and removed scaffold placeholder or model drift for the current repair cycle.
```

Do not emit this artifact speculatively. Only write it once the repo-local skill regeneration work is actually complete for the current repair cycle.
When package-managed skill evolution triggered the pass, the `Summary` must say whether the repo-local work was synthesized, repaired, or refreshed and name the repo-local evidence or repair-cycle input that caused it.

## After this step

Continue to `../opencode-team-bootstrap/SKILL.md` as directed by scaffold-kickoff.

## Rules

- Use this after the main scaffold exists — it refines, not replaces
- In retrofit work, use this only after `.opencode/` has been added or repaired
- When creating or revising skills, follow `../agent-prompt-engineering/SKILL.md` rules to avoid anti-patterns
- Start with the smallest useful pack; add only when project evidence justifies it
- Never auto-install external skills — synthesis from reference only
- In greenfield generation, complete baseline population and required synthesis in one invocation
- Keep generated review and diagnosis guidance repo-local; do not promote it into a Scafforge core skill
- Generated workflow skills must agree with the ticket tools and prompts on stage order, artifact ownership, and blocker behavior before generation is complete
- Generated workflow skills should name stack-specific build and verification commands that match the active adapter evidence instead of falling back to generic Python or Node assumptions
- When the brief declares a release target such as Godot Android, generated skills must record the canonical export command and artifact path so weaker models do not treat release proof as optional polish work

## References

- `references/local-skill-catalog.md` for the baseline skill list
- `../../references/skill-evolution-policy.md` for the package-versus-repo skill boundary
- `../../references/external-source-evaluation-rubric.md` for external-source distillation rules
- `assets/templates/SKILL.template.md` for the skill file template
- `references/blender-mcp-workflow-reference.md` when a repo needs synthesized Blender-MCP asset guidance
