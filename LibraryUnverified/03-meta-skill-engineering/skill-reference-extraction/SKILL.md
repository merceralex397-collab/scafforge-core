---
name: skill-reference-extraction
description: Extract large reference material (schemas, examples, lookup tables, API docs) from a bloated SKILL.md into a references/ directory for progressive disclosure. Use this when a SKILL.md exceeds 500 lines or 10KB, contains large code examples or schemas not needed every invocation, or the user says "this skill is too long" or "slim it down". Do not use for skills already concise under 200 lines, when the material is core procedure (not reference), or when extraction would break the skill's flow.
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-reference-extraction
  maturity: draft
  risk: low
  tags: [skill, reference, extraction]
---

# Purpose
Extracts large reference material (docs, schemas, examples, tables) from SKILL.md into references/ directory. Keeps core skill concise while making detail available on demand—progressive disclosure.

# When to use this skill
Use when:
- SKILL.md >500 lines or >10KB
- Contains large code examples, schemas, lookup tables
- User says "this is too long", "extract references", "slim down"
- Detailed appendix not needed every invocation
- Multiple skills could share reference material

Do NOT use when:
- Skill already concise (<200 lines)
- "Reference" is actually core procedure
- Material small (<50 lines)
- Extraction would break flow

# Operating procedure
1. **Identify extraction candidates**:
   - Code examples >20 lines
   - Schema definitions
   - Lookup tables/mappings
   - API documentation excerpts
   - Configuration templates
   - Extended case studies
2. **Assess each**:
   - Needed every invocation? → Keep inline
   - Reference/lookup material? → Extract
   - Shared across skills? → Extract to shared location
3. **Create references/ structure**:
   ```
   skill-name/
   ├── SKILL.md
   └── references/
       ├── README.md
       ├── schema.json
       ├── examples/
       │   ├── basic.md
       │   └── advanced.md
       └── api-docs.md
   ```
4. **Extract each piece**:
   - Move to appropriate file
   - Name descriptively
   - Preserve formatting
5. **Add pointers in SKILL.md**:
   - "See references/schema.json for full schema"
   - Or: `<!-- @include references/schema.json -->`
   - Keep 1-2 line summary
6. **Create references/README.md**:
   ```markdown
   # References
   | File | Contents | When to use |
   |------|----------|-------------|
   | schema.json | API schema | Validating responses |
   ```
7. **Verify completeness**:
   - Skill understandable without references?
   - Procedure steps present?
   - References signposted?

# Output defaults
```
## Reference Extraction: [skill]

### Extracted
| Content | From | To | Size |
|---------|------|-----|------|
| Schema | L150-300 | references/schema.json | 5KB |

### Reduction
- Before: 850 lines, 25KB
- After: 280 lines, 8KB
- Reduction: 67%

### Verification
- [x] Procedure intact
- [x] References signposted
- [x] README created
```

# References
- https://developers.openai.com/codex/skills — Codex skill format including progressive disclosure
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skill structure
- Progressive disclosure design principles for context window management

# Failure handling
- **Can't determine what to extract**: If doubt, keep inline
- **Would break skill**: Material is procedural—leave inline
- **Circular references**: Flatten structure
- **Shared conflict**: Create skill-specific copy
