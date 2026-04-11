---
name: repo-scaffold-factory
description: Generate the base repository file structure including README, AGENTS.md, docs layout, ticket templates, and the full OpenCode scaffold with agents, tools, plugins, commands, and skills. Use when creating a greenfield repo foundation. This generates a generic starting structure that other skills then customize.
---

# Repo Scaffold Factory

Use this skill to generate the initial repository file tree. This is a TWO-PHASE process.

## Mode selection

- If this skill is reached from `scaffold-kickoff` for a new repo, use the full scaffold path (`--scope full`).
- If the user explicitly wants only the OpenCode operating layer for an existing repo, use `--scope opencode`.
- If the destination already contains code or curated project files and the user has not made clear whether to overwrite the full repo or add only the operating layer, ask the user before choosing the scope.

## Phase A: Generate the base scaffold (script-assisted)

The Python script handles deterministic mechanical work: copying 100+ template files, substituting placeholders, and generating metadata. This is better done by a script than by hand.

### Locate the script

The script is at `scripts/bootstrap_repo_scaffold.py` relative to this skill's directory.

### Run the script

```
python3 scripts/bootstrap_repo_scaffold.py \
  --dest <destination-path> \
  --project-name "<Project Name>" \
  --model-provider "<provider>" \
  --planner-model "<planner-model-string>" \
  --implementer-model "<implementer-model-string>"
```

Optional flags:
- `--project-slug <slug>` — override the auto-generated slug
- `--agent-prefix <prefix>` — override the agent filename prefix (defaults to slug)
- `--model-tier <weak|standard|strong>` — tune prompt density for generated guidance without changing workflow fidelity
- `--utility-model <model>` — set a different model for utility agents (defaults to planner model)
- `--stack-label <label>` — stack label for generated docs (defaults to "framework-agnostic")
- `--scope opencode` — generate only the .opencode/ layer (for retrofit)
- `--force` — overwrite existing files

### What the script generates

The script copies files from `assets/project-template/` and substitutes these placeholders:
- `__PROJECT_NAME__` → project name
- `__PROJECT_SLUG__` → URL-safe slug
- `__AGENT_PREFIX__` → prefix for agent filenames
- `__MODEL_PROVIDER__` → provider label
- `__MODEL_TIER__` → prompt-density tier
- `__PLANNER_MODEL__` → planner/reviewer model string
- `__IMPLEMENTER_MODEL__` → implementer model string
- `__UTILITY_MODEL__` → utility agent model string
- `__STACK_LABEL__` → stack/framework label

Output includes: README.md, AGENTS.md, START-HERE.md, docs/, tickets/, opencode.jsonc, .opencode/ (agents, tools, plugins, commands, skills, config, state), and .opencode/meta/bootstrap-provenance.json.

For Godot Android game stacks, the script also seeds the base asset-pipeline surfaces so later skills start from a real repo layout instead of prose-only guidance:
- `assets/pipeline.json`
- `assets/PROVENANCE.md`
- `assets/briefs/`, `assets/models/`, `assets/sprites/`, `assets/audio/`, `assets/fonts/`, `assets/themes/`
- `.opencode/meta/asset-pipeline-bootstrap.json`

The generated workflow layer includes the stack adapter registry inside `environment_bootstrap`, so generated bootstrap guidance should reflect the detected stack instead of assuming a Python-only repo.

### Derive script arguments from the canonical brief

The arguments should come from the canonical brief and user decisions:
- `--project-name` from the brief's Project Summary
- `--model-provider` from the brief's Tooling/Model Constraints
- `--planner-model` and `--implementer-model` from user decisions
- `--stack-label` from the brief's Constraints (or "framework-agnostic" if unresolved)
- When the brief describes a game/content pipeline, pass the Product Finish Contract fields (`deliverable_kind`, `placeholder_policy`, `content_source_plan`, `licensing_or_provenance_constraints`, `finish_acceptance_signals`) so the seeded asset-pipeline metadata is specific on first render.

## Phase B: Customize with project-specific content (agent-driven)

After the script generates the base files, you MUST customize them with actual project content in the same session. Phase B is mandatory completion work, not an optional revisit. The generated files contain generic placeholder text that must be replaced before handoff.

### Files to customize

1. **README.md** — Replace the generic template sections with actual project description, setup instructions, and architecture overview from the canonical brief.

2. **AGENTS.md** — Populate with actual project rules, conventions, and the truth hierarchy specific to this project.

3. **docs/spec/CANONICAL-BRIEF.md** — This should already contain the normalized brief from `spec-pack-normalizer`. If it contains template placeholders, replace them with the actual brief content.

4. **docs/process/workflow.md** — Customize the workflow description if the project has specific process requirements.

5. **START-HERE.md** — `handoff-brief` will publish the final restart surface, but the surrounding repo surfaces it depends on must already contain real project content.

6. **Agent prompts** — Will be customized by `opencode-team-bootstrap`. Leave for now.

7. **Project-local skills** — Will be customized by `project-skill-bootstrap`. Leave for now.

## What NOT to customize at this stage

- Tools (.opencode/tools/) — these are standard workflow tools, keep as generated
- Plugins (.opencode/plugins/) — these are standard enforcement plugins, keep as generated
- Config (.opencode/config/) — stage-gate config is standard
- State files (.opencode/state/) — bootstrap state is correct

## Hard rules

- Keep Phase A deterministic and script-driven.
- Complete Phase B in the same session as the scaffold render.
- No generic placeholder text or template filler may remain in any handoff surface by the time generation reaches `handoff-brief`.
- A fresh scaffold must already expose one legal first move while bootstrap proof is missing: `environment_bootstrap`, then a fresh `ticket_lookup`.
- Generated process docs and workflow tools must name repo-local versus host-global prerequisites clearly enough that later audit and repair can classify environment blockers instead of silently skipping verification.
- Generated workflow surfaces must preserve the contract that explicit ticket acceptance smoke commands are canonical smoke scope for `smoke_test`, not optional hints that can be replaced by heuristic pytest selection.

## After this step

Before continuing into project-specific specialization, run the early bootstrap-lane proof:

```sh
python3 scripts/verify_generated_scaffold.py <repo-root> --verification-kind bootstrap-lane --format both
```

That early gate must prove one canonical bootstrap ticket, one valid bootstrap status, and one aligned bootstrap-first route across restart, workflow, and tool surfaces before `project-skill-bootstrap` begins.

The final verifier now also rejects placeholder residue, invalid canonical JSON or JSONC, broken generated agent references, project-name drift across key handoff surfaces, and missing asset-pipeline starter surfaces for generated game repos.

Then continue to `../project-skill-bootstrap/SKILL.md` for the full greenfield local-skill pass, and later use `scripts/verify_generated_scaffold.py` again with the default verification kind as the final immediate-continuation gate before handoff.

## References

- `references/layout-guide.md` for the intended repo shape
- `references/workflow-guide.md` for the ticketed lifecycle
- `references/community-skill-audit.md` for notes on external skill patterns
- `assets/project-template/` for the template source
