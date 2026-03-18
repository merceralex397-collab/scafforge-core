---
name: skill-improver
description: Improve existing agent skills when the user asks to refine, audit, harden, repair, restructure, or extend a skill package or SKILL.md. Use this whenever the request is effectively “improve this skill”, “audit this SKILL.md”, “make this skill trigger better”, “add references/scripts/evals to this skill”, or “turn this weak skill into a robust one,” even if the user does not say “skill improver.” Do not use for creating a brand-new skill from nothing when a skill-authoring or skill-creator workflow would be a better fit.
license: Apache-2.0
compatibility:
  clients: [opencode, codex, gemini-cli, github-copilot]
metadata:
  owner: project-local
  domain: meta-skill
  maturity: stable
  risk: low
  tags: [skills, refactoring, routing, evaluation, packaging, meta]
allowed-tools:
  - file_search
  - python
  - container
---

# Purpose

Use this skill to improve an existing skill package, not to invent an unrelated new one.

A skill is a reusable operating manual for an agent. Improving a skill means improving four things together:

1. **Routing** — whether the right tasks activate it.
2. **Execution** — whether the body tells the agent what to do in a concrete, repeatable way.
3. **Support layers** — whether references, scripts, examples, evals, and manifests exist where they actually help.
4. **Maintainability** — whether the skill stays narrow, understandable, and worth activating.

Preserve the skill's core purpose unless the user explicitly asks to reposition it.

# When to use this skill

Use this skill when:

- the user provides a `SKILL.md` and wants it improved,
- the user says a skill feels weak, vague, generic, bloated, or under-specified,
- the user wants better triggering, better structure, better examples, or better supporting files,
- the user wants to know whether a skill needs `references/`, `scripts/`, `evals/`, `manifest.yaml`, or overlays,
- the user wants one skill upgraded from a thin prompt into a durable package,
- the user wants an existing skill adapted for a different repo, stack, runtime, or agent environment.

Do not use this skill when:

- the user is creating a brand-new skill from scratch and there is no meaningful existing draft or workflow to improve,
- the task is actually a repo review, architecture review, or product planning exercise rather than a skill-improvement exercise,
- the user only wants installation help for an existing packaged skill,
- another narrower skill already covers the exact domain and this skill would only add meta-process overhead.

# Working posture

Treat the skill as a product surface, not just a prompt blob.

That means you should think in layers:

- **description/frontmatter** for routing,
- **SKILL.md body** for procedure and decisions,
- **references** for optional depth,
- **scripts** for repeated mechanics,
- **evals** for proof the skill helps,
- **manifest/packaging** for maintainability and portability.

Start lean. Add weight only where it buys reliability.

# Improvement modes

Choose the lightest mode that solves the real problem.

## Mode 1 — Surgical edit

Use when the skill is broadly sound and mainly needs:

- better trigger wording,
- clearer steps,
- stronger output contract,
- a few anti-patterns or examples,
- removal of fluff or duplication.

Output:

- updated `SKILL.md`,
- concise change summary,
- optional small eval refresh.

## Mode 2 — Structural refactor

Use when the skill has the right goal but poor execution. Typical signs:

- vague description,
- no phases,
- no decision rules,
- no failure handling,
- too much content in one file,
- repeated examples or mixed concerns.

Output:

- rewritten `SKILL.md`,
- new `references/` files if justified,
- anti-patterns and examples,
- eval stubs or updated evals,
- manifest if the package is meant to be maintained.

## Mode 3 — Package upgrade

Use when the skill should become a first-class package. Typical signs:

- reusable across multiple projects or users,
- likely to be installed/shared,
- needs baseline comparisons,
- needs scripts for repeated mechanics,
- needs overlays or validation.

Output:

- improved `SKILL.md`,
- manifest,
- evals,
- references,
- scripts only where deterministic,
- changelog/update notes.

# Workflow

Follow these phases in order unless the user clearly wants a lighter pass.

## Phase 1 — Understand the current skill

Identify:

- the skill's current purpose,
- the user problem it is meant to solve,
- the current activation boundary,
- the main failure mode,
- whether the skill is draft, internal, project-local, or intended for reuse.

Read the existing skill package before editing. If the conversation already provides enough context, extract it instead of re-asking basic questions.

## Phase 2 — Diagnose the actual weakness

Score the skill informally against these dimensions:

- routing quality,
- procedural clarity,
- decision support,
- support-layer quality,
- evaluation readiness,
- maintainability.

Name the primary failure mode explicitly before rewriting. Common failure modes include:

- **undertriggering** — description too timid or generic,
- **overtriggering** — scope too broad or missing negatives,
- **prompt-blob syndrome** — lots of prose, little procedure,
- **missing branching** — no decision rules for common variants,
- **resource mismatch** — needed references/scripts absent, or unnecessary ones added,
- **no proof** — no evals or no obvious way to test improvement,
- **package rot** — no manifest/changelog/ownership for a skill that is meant to persist.

## Phase 3 — Decide what to improve

Improve the description first, then the body, then supporting layers.

Use this order:

1. clarify purpose,
2. tighten routing description,
3. add or improve workflow phases,
4. add decision rules,
5. add output contract and failure handling,
6. decide whether references are warranted,
7. decide whether scripts are warranted,
8. decide whether evals are warranted,
9. decide whether manifest/packaging metadata is warranted.

## Phase 4 — Rewrite with restraint

Write instructions that are:

- specific,
- procedural,
- reusable,
- low-ceremony.

Prefer concrete decisions over generic advice. Explain *why* where that helps the agent adapt. Avoid inflating the skill with policy text that belongs elsewhere.

## Phase 5 — Add support layers only if justified

### Add references when:

- optional deep detail would clutter `SKILL.md`,
- the skill covers multiple variants or subdomains,
- the same heuristics, tables, or examples will be reused,
- the core file is getting too long.

### Add scripts when:

- the same mechanical task will likely recur,
- the work is deterministic or easily validated,
- a script reduces context waste,
- the script can expose a clean CLI contract.

Do **not** add scripts merely to look sophisticated. Judgment-heavy improvement work belongs in the model.

### Add evals when:

- the skill is intended for reuse,
- routing quality matters,
- the skill changes files or produces structured outputs,
- the user wants evidence that the revised skill is better,
- the skill is important enough that regressions matter.

### Add manifest/packaging metadata when:

- the skill is intended to live beyond one session,
- the skill may be shared or installed,
- overlays, validation, or registry-style management are likely.

## Phase 6 — Review your own rewrite

Run a self-review before presenting the result.

Check:

- Does the description clearly say what the skill does and when it should trigger?
- Are there concrete “do not use” boundaries where confusion is likely?
- Is the workflow ordered and branch-aware?
- Is there at least one stop condition, quality gate, or failure path?
- Are examples or anti-patterns included where they materially help?
- Are support files justified rather than ornamental?
- Did you preserve the original purpose instead of silently changing the job?

If any answer is no, revise again.

## Phase 7 — Package the result

Return:

- the improved files,
- a short rationale for each major change,
- any recommended next-step eval prompts.

# Decision rules

## Description rules

The description is routing metadata. Treat it as the highest leverage field.

A strong description should:

- name the main action,
- include realistic trigger phrases or task shapes,
- include likely adjacent phrasings,
- include a negative boundary if near-misses are common.

Weak:

- “Helps with skills.”
- “Improves prompts and workflows.”

Stronger:

- “Improve existing agent skills when the user asks to audit, refine, harden, restructure, or extend a SKILL.md or skill package. Use this for requests like ‘improve this skill’, ‘fix this weak skill description’, or ‘add evals/references/scripts to this skill’. Do not use for creating a brand-new skill from nothing.”

## Workflow rules

If a skill spans multiple use cases, do not dump all cases into one flat list. Add either:

- explicit phases,
- a decision table,
- or separate mode sections.

## Scope rules

Prefer narrower, sharper skills over giant “do everything about X” skills.

If the skill is trying to cover multiple different jobs, either:

- split it,
- move optional depth into references,
- or clearly separate modes and triggers.

## Support-layer rules

Use `references/` for optional depth.
Use `scripts/` for repeated deterministic mechanics.
Use `evals/` to prove the skill helps.
Use `manifest.yaml` and `CHANGELOG.md` when the skill is meant to persist.

# Anti-patterns

Avoid these when improving a skill:

1. **Placeholder upgrades** — replacing one vague paragraph with a longer vague paragraph.
2. **Monolith inflation** — stuffing every idea into `SKILL.md` instead of separating optional depth.
3. **Tool cosplay** — adding scripts that do not solve a repeated mechanical problem.
4. **Checklist fog** — lots of true statements with no ordering or weighting.
5. **Silent repurposing** — changing what the skill is for without telling the user.
6. **Routing negligence** — improving the body while leaving a bad description untouched.
7. **Missing negatives** — no “do not use” guidance where nearby tasks could trigger it incorrectly.
8. **No exit condition** — instructions say how to start but not what “done” looks like.
9. **Unverifiable improvement** — claiming the skill is better with no eval prompts or review path.
10. **Reference dumping** — creating big reference files with no explicit cue for when to read them.

# Output requirements

When presenting an improved skill, use this structure unless the user asks otherwise:

## Improvement summary
- What changed
- Why it changed
- What stayed intentionally unchanged

## Package contents
- list of created or modified files

## Recommended eval prompts
- 2 to 5 realistic prompts that would test the improved skill

## Risks or open questions
- only if something could not be settled cleanly

# Examples

## Example 1 — weak routing only

Input situation:
A skill has a good body but the description is “Helps with MCP servers”.

What to do:
- rewrite the description with concrete task shapes,
- add “do not use” boundaries,
- keep the rest light,
- add trigger evals if the skill is meant to be reused.

## Example 2 — thin skill, broad goal

Input situation:
A skill claims to handle “frontend work” but contains only a few generic bullets.

What to do:
- identify whether the real job is React, UI review, artifact building, or design,
- narrow the skill or split concerns,
- add phases and anti-patterns,
- move optional stack variants into references.

## Example 3 — mature skill with repeated mechanics

Input situation:
A skill is already good, but every use ends up recreating the same JSON scaffolds and package checks.

What to do:
- keep the judgment in the skill body,
- add a small CLI helper for the repeated mechanics,
- document when to call it,
- avoid pretending the helper can judge quality.

# Failure handling

If the current skill is too incomplete to improve cleanly:

- say what is missing,
- preserve what can be salvaged,
- produce the lightest viable improved draft,
- mark any assumptions,
- avoid fabricating package structure that the user did not actually need.

If the user wants a quick, informal pass rather than a full package upgrade, do that. The point is to improve the skill, not force ceremony.
