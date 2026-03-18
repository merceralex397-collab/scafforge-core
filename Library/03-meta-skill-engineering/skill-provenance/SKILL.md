---
name: skill-provenance
description: Document the origin, authorship, evidence basis, and encoded assumptions of a skill to establish trust and traceability. Use this when publishing a skill to a shared registry, importing from an external source, auditing library trustworthiness, or when a skill encodes non-obvious assumptions that need documentation. Do not use for evaluating skill quality (use skill-evaluation), tracking lifecycle states (use skill-lifecycle-management), or when git history alone provides sufficient provenance.
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-provenance
  maturity: draft
  risk: low
  tags: [skill, provenance]
---

# Purpose
Documents origin, authorship, evidence basis, and assumptions of a skill. Provenance prevents skills from becoming mysterious prompt blobs—answers "where did this come from, why written this way, can we trust it?"

# When to use this skill
Use when:
- User says "where did this come from?", "document origin", "add provenance"
- Creating official skill for sharing/publishing
- Auditing library for trust and traceability
- Skill imported from external source needs attribution
- Skill encodes non-obvious assumptions needing documentation

Do NOT use when:
- Skill is trivial and provenance overkill
- Just need git history (built-in)
- Want skill evaluation (use `skill-evaluation`)

# Operating procedure
1. **Document origin**:
   - Source URL if adapted
   - "created" if from scratch
   - If derived: % original vs adapted
2. **Record authorship**:
   - Original author(s)
   - Adapter(s) if modified
   - Reviewer(s) if reviewed
   - Dates
3. **Document evidence basis**:
   - What documentation informed procedure?
   - What best practices referenced?
   - What expert knowledge encoded?
   - What failures learned from?
4. **Catalog assumptions**:
   - What must be true for skill to work?
   - What environment/context assumed?
   - What tool versions targeted?
   - What conventions expected?
5. **Assess trust level**:
   - **High**: Official, reviewed, tested, maintained
   - **Medium**: Known source, some testing
   - **Low**: Unknown source, unreviewed
   - **Untrusted**: External, not reviewed
6. **Record change history**:
   - Major revisions with rationale
   - Breaking changes
   - Deprecation of approaches
7. **Update frontmatter**

# Output defaults
In SKILL.md frontmatter:
```yaml
metadata:
  provenance:
    origin: "https://..."
    adaptation: 30%
    trust: high
```

PROVENANCE.md:
```markdown
# Provenance

## Origin
- **Source**: [URL or "created"]
- **Author**: [name]
- **Adapted by**: [name] on [date]

## Evidence Basis
- [URL] — informed steps 1-3
- [guide] — informed format

## Assumptions
- Unix environment
- Node.js 18+
- npm as package manager

## Trust Level: [High]
Rationale: [why]

## Change History
| Date | Change | Author | Why |
|------|--------|--------|-----|
```

# References
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skill metadata structure
- https://developers.openai.com/codex/skills — Codex skill format
- Git history for change tracking
- Original source documentation when skill is adapted

# Failure handling
- **Source unknown**: Mark "unknown", trust Low, recommend review
- **Assumptions undocumentable**: Flag risk
- **Multiple sources**: Document all, note precedence
- **Author unreachable**: Document what's known, mark gaps
