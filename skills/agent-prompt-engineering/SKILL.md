---
name: agent-prompt-engineering
description: Design and harden agent, command, workflow, and tool prompts for reliable execution across different AI models. Use when creating or revising repo-local agents to apply model-specific prompting techniques, tighten scope, and prevent common agent failure modes like doom loops, status-over-evidence routing, and impossible read-only delegation.
---

# Agent Prompt Engineering

Use this skill when prompt wording controls how agents coordinate, route work, and use tools.
Use [../../references/competence-contract.md](../../references/competence-contract.md) as the package-level target: prompts should leave weaker models with one clear legal next move, not a maze of plausible interpretations.

During standard greenfield scaffolding, this is a required same-session pass after `opencode-team-bootstrap` and before `ticket-pack-builder`. The pass may be light or heavy depending on the chosen models and project-specific coordination risk, but it should not be skipped.

## Procedure

### 1. Analyze existing prompts

Read the existing prompt, command, or process doc and identify:
- Authority (what the agent owns)
- Scope (what the agent does NOT own)
- Tool surface (what tools it can use)
- Stage transitions (what stages it moves between)
- Delegation boundaries (who it can delegate to)

### 2. Apply prompt contracts

Read `references/prompt-contracts.md` for the target prompt type:
- Team leader: resolve state from tools first, treat `ticket_lookup.transition_guidance` as the canonical next-step summary, verify artifacts before routing, and stop on repeated lifecycle contradictions instead of probing alternate stage or status values
- Planner: decision-complete plans for one ticket only
- Implementer: follow the approved plan, stop on missing requirements
- Reviewers/QA: stay read-only, return findings first
- Utility: stay narrow and bounded

### 3. Remove anti-patterns

Read `references/anti-patterns.md` and eliminate:
- Status-over-evidence routing (routing based on labels instead of actual artifacts)
- Raw-file stage control (editing files directly instead of using tools)
- Impossible read-only delegation (telling read-only agents to write files)
- Broad command follow-on (commands that silently continue the whole workflow)
- Eager skill loading (loading skills before resolving state)
- Workflow thrash loops (repeating the same rejected lifecycle transition instead of reading the contract)
- Unsupported stage probing (trying values like `todo` to see what passes)
- Evidence-free PASS claims (writing implementation, QA, or smoke-test success without executed command output)
- Slash-command self-use (agents treating human `/commands` as autonomous workflow tools)

### 4. Apply model-specific techniques

Before choosing prompt density, read the scaffold's selected model tier from `.opencode/meta/bootstrap-provenance.json` or the generated `.opencode/skills/model-operating-profile/SKILL.md`. If the tier is missing, default to `weak` to preserve the weaker-model-first contract.

Different models have different prompting best practices. When hardening prompts for a specific model:

**Step A: Check package-side model notes**
Look in `references/model-notes/` for existing documentation on the chosen model. Treat these notes as read-only package reference material.

**Step B: Research if needed**
If no local docs exist for the chosen model, web search for:
- "[model name] prompting best practices"
- "[model name] system prompt guidelines"
- "[model name] prompting guide official documentation"

**Step C: Apply model-specific techniques**
Common model-specific differences:
- Some models work better with stricter markdown or tagged structure
- Some models need clearer output formatting requirements
- Some models respond better when the purpose of each instruction is stated explicitly
- Some models benefit from example-led instructions for expected outputs
- Some models need bounded single-goal asks instead of broad parallel asks
- Some models have specific tool-use or context-window considerations

**Step C1: Match prompt density to the configured model tier**
- `weak`: include full stop conditions, explicit verification checklists, concrete truth-source hierarchy, named blocker paths, and short examples for every section that would otherwise be ambiguous
- `standard`: include stop conditions and verification checklists, link back to canonical truth sources, and use examples only where the repo has historically shown confusion
- `strong`: keep stop conditions explicit, reference local checklist and truth-source docs instead of repeating them in full, and use minimal examples

Do not let a stronger-model tier remove hard safety boundaries. Tiering changes prompt density, not ownership, artifact, or escalation rules.
Do not let model-tier tuning remove stack-specific bootstrap guidance or proof requirements either; those stay mandatory across all tiers.

**Step D: Record project-specific adaptations**
If the generation run discovers project-specific prompt adaptations worth preserving, write them into the generated repo's local notes or skill surfaces. Do not write back into Scafforge package files during project generation.

### 5. Apply weak-model hardening

Read `references/weak-model-profile.md` and ensure:
- Outputs are short but highly structured
- Exact required sections are stated
- Formatting requirements are clear and specific
- The reason for a requirement is stated when that extra rationale improves compliance
- Example-shaped outputs are included when they materially reduce ambiguity
- Blocker returns are preferred over hidden guesswork
- Proof is required before stage transitions
- Next specialist or action is named explicitly
- Stable procedure lives in tools/skills, not long prose
- Goals are bounded one at a time unless the workflow explicitly supports safe parallel work
- Contradiction handling is explicit: if a lifecycle tool returns the same blocker twice, stop and explain it instead of searching for a workaround
- Missing environment prerequisites are explicit: if `uv`, `pytest`, `rg`, git identity, or another required executable is unavailable, classify it as a blocker instead of inventing a workflow workaround

### 6. Final verification

Re-read the final prompt and ask:
- Could a weaker model execute this without inventing hidden state?
- Are all tool permissions explicit?
- Are all delegation boundaries named?
- Is there a clear stop condition?
- Does the prompt leave exactly one legal next move when the workflow is healthy, and one explicit blocker path when it is not?

## Output contract

Before leaving this skill, confirm all of these are true:
- the team leader prompt treats `ticket_lookup.transition_guidance` as canonical, routes bootstrap failures to `environment_bootstrap`, and does not stop at summary when work remains
- specialist prompts describe the same lease-ownership model, artifact ownership model, and blocker behavior as the workflow tools
- read-only prompts do not tell agents to mutate repo-tracked files
- slash commands are described only as human entrypoints, not as autonomous workflow tools
- prompt density matches the configured model tier without weakening stop conditions, escalation paths, or proof requirements

## Repair follow-on artifact

When this skill runs as a `scafforge-repair` follow-on hardening pass, read `.opencode/meta/repair-follow-on-state.json` and, after the prompt hardening work is actually complete for the current repair cycle, write:

- `.opencode/state/artifacts/history/repair/agent-prompt-engineering-completion.md`

Use this minimal shape so the public repair runner can auto-recognize `agent-prompt-engineering` completion for the current repair cycle on the next run:

```md
# Repair Follow-On Completion

- completed_stage: agent-prompt-engineering
- cycle_id: <cycle_id from .opencode/meta/repair-follow-on-state.json>
- completed_by: agent-prompt-engineering

## Summary

- Hardened the project-specific prompts and delegation rules for the current repair cycle.
```

Do not emit this artifact speculatively. Only write it once the prompt-hardening work is actually complete for the current repair cycle.

## Rules

- Prefer tool-backed state over raw file choreography
- Keep ticket status coarse and queue-oriented
- Put transient approval state in workflow state or explicit artifacts
- Require verification before stage changes
- Require the team leader to route specialist artifact authorship to the owning lane instead of synthesizing those bodies itself
- Keep slash commands human-facing; never rely on them for internal autonomous routing
- Require explicit blocker return paths when material ambiguity remains
- Do not let prompts terminate with a summary when the workflow still has another stage
- Never instruct read-only agents to mutate repo-tracked files
- Never claim a file changed unless a write-capable tool actually wrote it

## After this step

Continue to `../ticket-pack-builder/SKILL.md` for bootstrap ticketing in greenfield generation, or return to `../scaffold-kickoff/SKILL.md` for the next step in the flow.

## References

- `references/prompt-contracts.md` — per-agent-type prompt rules
- `references/anti-patterns.md` — common prompt failures
- `references/examples.md` — before/after prompt improvements
- `references/weak-model-profile.md` — rules for weak-model robustness
- `references/model-notes/` — model-specific prompting documentation used as read-only package reference
