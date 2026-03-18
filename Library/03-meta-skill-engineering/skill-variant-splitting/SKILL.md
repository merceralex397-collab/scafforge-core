---
name: skill-variant-splitting
description: Determine when a broad skill should be split into focused variants and execute the split — creating specialized skills by stack, platform, scope, or domain axis. Use this when a skill has multiple disjoint "For X" / "For Y" sections, triggers on unrelated inputs, or its procedure is full of conditional branches. Do not use for focused skills that work well, minor variations handled by overlays, or trigger-only problems (use skill-trigger-optimization).
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-variant-splitting
  maturity: draft
  risk: low
  tags: [skill, variant, splitting]
---

# Purpose
Determines when a skill has grown too broad and should be split into focused variants. A skill trying to do too many things has vague triggers, bloated procedures, and mediocre output. Splitting creates specialized variants that route precisely and perform excellently.

# When to use this skill
Use when:
- User says "this skill does too much", "split this skill", "create variants"
- Skill has multiple disjoint sections ("For Python:" / "For JavaScript:")
- Skill triggers on unrelated inputs (routing confusion)
- Procedure has many "if X then Y, else Z" branches
- Description >2 sentences trying to cover all cases
- Refinement keeps adding exceptions

Do NOT use when:
- Skill is focused and working well
- Variations minor (use overlays instead)
- Problem is just description (use `skill-description-optimizer`)
- Skill genuinely handles one coherent task

# Operating procedure
1. **Identify splitting signals**:
   - Count distinct "modes" (if/else, "For X:" sections)
   - Count distinct non-overlapping trigger clusters
   - Does output format vary by case?
   - Do different contexts need different behaviors?
2. **Determine split axis**:
   - **Stack**: skill-testing-python, skill-testing-javascript
   - **Platform**: skill-deploy-aws, skill-deploy-gcp
   - **Scope**: skill-review-quick, skill-review-thorough
   - **Domain**: skill-api-rest, skill-api-graphql
3. **Define variants**:
   - Each passes "one sentence" test
   - Each has distinct, non-overlapping triggers
   - Each has focused, linear procedure
4. **Extract shared core**:
   - What's common across all?
   - Consider: base with extensions, or fully independent
5. **Write each variant**:
   - Name: original-[variant]
   - Focused description
   - Simplified procedure
   - Variant-specific examples
6. **Update routing**:
   - Each "Do NOT use when" references siblings
   - "Do NOT use for GraphQL (use `api-testing-graphql`)"
7. **Verify coverage**:
   - All original cases covered
   - No gaps
   - No overlaps
8. **Deprecate original** (if fully replaced)

# Output defaults
```
## Variant Split: [original]

### Split Axis
[Stack | Platform | Scope | Domain]: [reasoning]

### Variants
| Variant | Scope | Triggers |
|---------|-------|----------|
| skill-a | [scope] | "phrase 1" |
| skill-b | [scope] | "phrase 2" |

### Shared Core
[What's common or "None - independent"]

### Coverage
- [x] Case 1 → variant A
- [x] Case 2 → variant B
- [x] No gaps/overlaps

### Migration
Original: [deprecate | keep as router | keep for general]
```

# References
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skill structure for variant organization
- https://developers.openai.com/codex/skills — Codex skill naming and organization
- Original skill being split
- Similar splits in the catalog for precedent

# Failure handling
- **Can't find clean axis**: May be unified; don't force split
- **Variants overlap**: Rethink axis or accept ambiguity
- **Too many (>5)**: Consider hierarchy or umbrella router
- **Core larger than variants**: Don't split—redundant
