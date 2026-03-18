---
name: skill-refinement
description: Make targeted, surgical fixes to an existing skill based on observed failure modes — tightening vague language, fixing routing misses, removing bloat, or covering missed edge cases. Use this when a skill produces inconsistent output, triggers incorrectly, or real usage revealed problems not covered. Do not use for complete rewrites (use skill-authoring), trigger-only fixes (use skill-trigger-optimization), adapting to a different context (use skill-adaptation), or when the skill is working correctly.
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-refinement
  maturity: draft
  risk: low
  tags: [skill, refinement]
---

# Purpose
Iteratively improves an existing skill based on observed failure modes, user feedback, or eval results. Focuses on surgical fixes—tightening vague language, fixing routing misses, removing bloat, clarifying edge cases—not rewrites.

# When to use this skill
Use when:
- User says "this skill isn't working right", "improve this skill", "the skill is too verbose/vague"
- Skill exists but produces inconsistent or low-quality output
- Eval results show specific failure patterns to address
- Skill triggers incorrectly (over/under firing)
- Real usage revealed edge cases not covered

Do NOT use when:
- Skill needs complete rewrite (use `skill-authoring`)
- Only description field needs work (use `skill-description-optimizer`)
- Skill needs different context (use `skill-adaptation`)
- Skill is working correctly—no change needed

# Operating procedure
1. **Collect evidence of the problem**:
   - What specific output was wrong?
   - What input triggered it?
   - How does expected differ from actual?
   - Is this routing problem or output quality problem?
2. **Categorize the failure mode**:
   - **Routing miss**: Skill didn't trigger when should → fix description
   - **Routing false positive**: Triggered when shouldn't → fix description, add "Do NOT use when"
   - **Wrong output format**: Structure off → fix Output defaults
   - **Missing edge case**: Scenario not handled → add to Operating procedure
   - **Vague instructions**: Procedure not specific → tighten language
   - **Scope creep**: Doing things outside job → add constraints
   - **Bloat**: Unnecessary steps → remove
3. **Make targeted fix**:
   - Change only what addresses the specific failure
   - Preserve everything working
   - Add test case for failure to evals/ if exists
4. **Verify fix doesn't break existing behavior**:
   - Run existing evals if available
   - Walk through known good cases mentally
   - Check routing changes don't cause new false positives/negatives
5. **Document the change**: What failure mode, what changed, date and evidence source

# Output defaults
```
## Refinement Summary

**Skill**: [name]
**Failure mode**: [category]
**Evidence**: [what went wrong]

### Change
**Section**: [which section]
**Before**: [original]
**After**: [new]
**Rationale**: [why this fixes it]

### Verification
- [ ] Existing evals still pass
- [ ] Known good cases still work
- [ ] Failure case now handled
```

# References
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skill structure
- https://developers.openai.com/codex/skills — Codex skill format
- The skill being refined and its eval results
- `skill-anti-patterns` checklist for structural issues

# Failure handling
- **No clear failure mode**: Don't refine speculatively—ask for specific example of what went wrong
- **Multiple failure modes**: Address one at a time, verify, then next
- **Failure suggests fundamental design problem**: Recommend `skill-authoring` for rewrite
- **Can't reproduce failure**: Get exact input that caused it before attempting fix
