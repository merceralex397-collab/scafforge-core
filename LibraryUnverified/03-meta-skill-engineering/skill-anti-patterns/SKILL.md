---
name: skill-anti-patterns
description: Audit a SKILL.md for structural anti-patterns that reduce routing accuracy, output quality, or maintainability. Use this for pre-promotion reviews, post-failure diagnostics, or quick structural audits when a skill feels "off" but the problem is unclear. Do not use for full skill rewrites (use skill-authoring) or for trigger-only fixes (use skill-trigger-optimization).
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-anti-patterns
  maturity: draft
  risk: low
  tags: [skill, anti, patterns]
---

# Purpose
Identifies specific anti-patterns in SKILL.md that reduce reliability, trigger accuracy, or output quality. Provides checklist with fixes. Use as QA lens when authoring, refining, or reviewing skills.

# When to use this skill
Use when:
- User says "check for anti-patterns", "what's wrong?", "review against standards"
- Skill being reviewed before promotion draft → stable
- Skill producing unexpected outputs
- Quick audit needed for structural issues

Do NOT use when:
- Full rewrite needed (use `skill-authoring`)
- Only triggers need fixing (use `skill-trigger-optimization`)
- Skill confirmed working—don't scan healthy skills

# Operating procedure

Check for each anti-pattern. For each PRESENT, provide the specific fix with before/after.

**AP-1: Circular trigger language**
- Pattern: Description says "Use when task clearly involves X" or "Use this for X-related work"
- Example before: `description: Helps with testing tasks when testing is needed.`
- Example after: `description: Generate pytest unit tests for Python functions when the user says "write tests", "add test coverage", or "create unit tests for this module". Do not use for integration or E2E tests (use integration-testing).`
- Fix: Replace circular self-references with specific user phrases and observable task signals

**AP-2: Boilerplate procedure steps**
- Pattern: Steps copied from a template like "Keep scope explicit", "Prefer references over inline", "Decide whether content belongs in core"
- Example before: `3. Keep scope explicit and boundaries clear`
- Example after: `3. List all file paths that will be modified and confirm with user before writing`
- Fix: Delete meta-commentary; replace with concrete actions the agent can execute

**AP-3: Generic output defaults**
- Pattern: "Structured markdown artifact(s) with clear next steps"
- Example before: `Output: A well-structured document with actionable recommendations`
- Example after: `Output: A markdown document with sections: ## Summary (3 sentences), ## Findings (numbered list with severity labels), ## Recommended Actions (ordered by priority)`
- Fix: Name exact sections, formats, field names, or schemas

**AP-4: Generic failure handling**
- Pattern: "If inputs missing, surface gap as decision item"
- Example before: `If something goes wrong, report the issue and suggest alternatives`
- Example after: `If the target file does not exist: stop, report the missing path, and ask user to confirm correct location before retrying`
- Fix: Name the specific most-common failure mode with exact recovery action

**AP-5: Overloaded purpose**
- Pattern: Purpose uses "and" 2+ times covering different task families
- Example before: `Creates API tests, generates documentation, and manages deployment configs`
- Example after: `Creates API tests for REST endpoints using pytest and requests`
- Fix: Split into separate skills (use skill-variant-splitting) or narrow to one job

**AP-6: Unmeasurable acceptance criteria**
- Pattern: Success defined with subjective terms like "good", "appropriate", "high-quality"
- Example before: `Ensure output is high-quality and appropriate for the context`
- Example after: `Output passes if: (1) all required sections present, (2) no placeholder text remains, (3) every code example is syntactically valid`
- Fix: Replace with observable, countable criteria

**AP-7: Missing "Do NOT use when" section**
- Pattern: No negative routing at all, or empty section
- Fix: Add 2-4 confusion cases naming the alternative skill. Format: "Do NOT use when [scenario] (use `skill-name` instead)"

**AP-8: Missing failure handling**
- Pattern: No failure handling section at all
- Fix: Add covering the 2-3 most common failure modes with specific recovery actions

**AP-9: Vague procedure verbs**
- Pattern: Steps use "Consider", "Think about", "You might want to", "Ensure"
- Example before: `Consider the user's requirements and think about the best approach`
- Example after: `Read the user's requirements. List the constraints. Select the approach that satisfies the most constraints.`
- Fix: Replace with concrete action verbs: "Read", "List", "Write", "Check", "Run", "Compare"

**AP-10: No authoritative references**
- Pattern: No URLs, or only vague "see documentation"
- Example before: `References: relevant documentation`
- Example after: `References: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills`
- Fix: Add 2-3 real URLs to official documentation

**AP-11: Identity-free description**
- Pattern: Description doesn't start with an action verb; reads like a noun phrase
- Example before: `description: A skill for handling deployments`
- Example after: `description: Deploy applications to Kubernetes clusters when...`
- Fix: Start description with the primary action verb

**AP-12: Copy-paste category boilerplate**
- Pattern: Multiple skills in same category share identical description suffixes
- Example: 12 skills all ending with "Use this when creating, adapting, refining, installing, testing, or packaging a skill..."
- Fix: Remove category boilerplate; write skill-specific routing text

# Output defaults
```
## Anti-Pattern Audit: [skill-name]

| ID | Pattern | Status | Fix |
|----|---------|--------|-----|
| AP-1 | Circular triggers | PRESENT | Replace "clearly involves" with "when user says X" |
| AP-2 | Boilerplate steps | ABSENT | — |
...

### Summary
- PRESENT: 3 (AP-1, AP-4, AP-7)
- ABSENT: 7

### Priority Fixes
1. AP-1: [specific fix]
2. AP-4: [specific fix]
3. AP-7: [specific fix]
```

If all ABSENT: "**Clean Bill of Health** — no anti-patterns detected"

# References
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skill structure
- https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-skills — Skill creation guide
- https://developers.openai.com/codex/skills — Codex skill format
- https://docs.anthropic.com/en/docs/claude-code/overview — Claude Code overview

# Failure handling
- **File unavailable**: Report and halt
- **Skill too broken to audit**: Recommend full rewrite via `skill-authoring`
- **Multiple interpretations**: Flag ambiguity, audit conservatively
