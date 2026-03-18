---
name: skill-reference-extraction
description: >-
  Extract large reference material (schemas, examples, lookup tables, API docs) from a
  bloated SKILL.md into a references/ directory for progressive disclosure. Use when a
  SKILL.md exceeds 500 lines or 10KB, contains large code blocks or schemas not needed
  every invocation, or the user says "this skill is too long", "slim it down", or
  "extract references". Do not use for skills already concise under 200 lines (use
  skill-improver for general tightening), when the candidate material is core procedure
  rather than reference (use skill-improver), or when the total extractable content is
  under 50 lines (not worth the indirection).
license: Apache-2.0
compatibility:
  clients: [opencode, copilot, codex, gemini-cli, claude-code]
---

# Purpose

Split large reference material out of a SKILL.md into a `references/` directory so the core skill stays concise and detail is available on demand.

# When to use

- SKILL.md exceeds 500 lines or 10 KB
- Contains code examples, schemas, or lookup tables over ~20 lines that are not needed every invocation
- User says "this is too long", "extract references", "slim down"
- Multiple skills could share the same reference material

# When NOT to use

- Skill is already under 200 lines — use **skill-improver** for general tightening
- Candidate material is core procedure, not reference — use **skill-improver**
- Total extractable content is under 50 lines — indirection cost exceeds benefit
- Extraction would break the skill's procedural flow

# Procedure

1. **Identify candidates** — scan for blocks that are reference, not procedure:
   - Code examples > 20 lines
   - Schema definitions or lookup tables
   - API documentation excerpts
   - Configuration templates
   - Extended case studies

2. **Classify each block**:
   - Needed every invocation → keep inline
   - Lookup / reference material → extract
   - Shared across skills → extract to a shared location

3. **Create `references/` directory** with descriptive filenames:
   ```
   skill-name/
   ├── SKILL.md
   └── references/
       ├── README.md          ← index table
       ├── schema.json
       └── examples.md
   ```

4. **Extract** — move each block, preserve formatting, name files by content not sequence.

5. **Add inline pointers** in SKILL.md — replace each extracted block with a one-line summary and a path reference:
   ```
   Full schema: see references/schema.json
   ```

6. **Write `references/README.md`** — a table mapping each file to its contents and when an agent should read it.

7. **Verify**:
   - SKILL.md is understandable without reading any reference file
   - All procedure steps remain inline
   - Every reference file is signposted from SKILL.md

# Output contract

Produce a summary in this format:

```
## Reference Extraction: [skill-name]

### Extracted
| Block | Original location | Destination | Size |
|-------|-------------------|-------------|------|

### Reduction
- Before: [lines], [KB]
- After: [lines], [KB]
- Reduction: [%]

### Verification
- [ ] Procedure intact
- [ ] All references signposted
- [ ] references/README.md created
```

# Failure handling

- **Cannot decide whether material is procedure or reference** → keep it inline; false-negative extraction is safer than breaking the skill
- **Extraction would fragment a coherent procedure section** → leave inline, note in summary
- **Circular cross-references between extracted files** → flatten into a single reference file
- **Two skills want the same reference** → create a skill-specific copy; shared references are fragile
