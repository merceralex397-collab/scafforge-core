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

## Operating modes

- **greenfield full pass**: populate the baseline skill pack and all required synthesized skills in one invocation
- **repair or regeneration**: refresh baseline skills and add or revise synthesized skills for an existing repo when needed

## Mode selection

- If this skill is reached from `scaffold-kickoff` during greenfield generation, use the full greenfield pass. Do not split baseline population and synthesis into separate revisits.
- If invoked directly for an existing repo, use repair or regeneration.
- If the repo is missing `.opencode/skills/`, do not start here. Run `../opencode-team-bootstrap/SKILL.md` first so the local skill layer exists before you rewrite it.

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
- Tell agents to stop on repeated lifecycle errors instead of probing alternate stage or status values
- Define stage-artifact ownership by specialist
- State that `smoke_test` is the only legal producer of smoke-test artifacts
- State that if execution or validation cannot run, the agent must return a blocker instead of manufacturing PASS evidence
- State that missing host prerequisites such as `uv`, `pytest`, `rg`, git identity, or service binaries are blockers that must be classified explicitly instead of worked around
- Clarify that slash commands are human entrypoints, not internal autonomous workflow tools

**review-audit-bridge** — Keep this generated skill repo-local and advisory-only, then add project-specific review and QA expectations:
- Repo-specific review commands, validation commands, and artifact paths
- Security-sensitive areas that need explicit attention
- Approval vs blocker rules for code review, security review, and QA
- Explicit blocker behavior when required validation commands cannot run
- Guidance for writing a repo-local process log under `diagnosis/` or the generated repo's chosen review-log path when workflow misuse or weak implementation quality needs to be explained
- Guidance for recommending remediation or reverification tickets without becoming the canonical ticket owner itself

**docs-and-handoff** — Add project-specific doc paths and conventions

**workflow-observability** — Keep as-is (generic is fine for observability)

**research-delegation** — Keep as-is (generic is fine for research patterns)

**local-git-specialist** — Add project-specific branch conventions if specified in brief

**isolation-guidance** — Keep as-is unless brief specifies isolation requirements

### 3. Analyze synthesis needs

From the canonical brief, generated repo structure, and local references, identify whether the project needs additional stack- or domain-specific skills beyond the baseline pack.

### 4. Review reference patterns

Use project documentation, framework documentation, package references, and other external research as reference material only. Review patterns that match the selected stack and workflow, then synthesize repo-specific procedure from that evidence.

Do not install external skills directly. Use external material as reference only.

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
- Every synthesized skill must have proper YAML frontmatter
- Every synthesized skill description must be concrete and selection-specific
- Do not use vague descriptions such as "help with this stack" or "general project guidance"
- No generated local skill may retain scaffold placeholder text after greenfield generation or repair/regeneration

### 7. Write updated skills

Write each updated skill to `.opencode/skills/<name>/SKILL.md`.
Each skill MUST have YAML frontmatter with `name` and `description`.
If `review-audit-bridge` needs heavier examples or review policy detail, place that material in `.opencode/skills/review-audit-bridge/references/` rather than bloating the skill body.

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

## References

- `references/local-skill-catalog.md` for the baseline skill list
- `assets/templates/SKILL.template.md` for the skill file template
