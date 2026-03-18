---
name: skill-provenance
description: >-
  Record origin, authorship, evidence basis, and encoded assumptions for a skill
  to establish trust and traceability. Use when someone asks "where did this skill
  come from?", "document this skill's origin", or "audit skill trustworthiness".
  Do not use for quality assessment (use skill-evaluation), lifecycle state tracking
  (use skill-lifecycle-management), or safety audits (use skill-safety-review).
license: Apache-2.0
compatibility:
  clients: [opencode, copilot, codex, gemini-cli, claude-code]
---

# Purpose

Produce a provenance record for a skill—answering "where did this come from, why was it written this way, and can we trust it?" Prevents skills from becoming untraceable prompt blobs.

# When to use

- User asks "where did this come from?", "document origin", "add provenance"
- Publishing a skill to a shared registry that requires attribution
- Importing a skill from an external source that needs trust assessment
- A skill encodes non-obvious assumptions that future editors must understand

# When NOT to use

- Git history alone provides sufficient provenance for internal-only skills
- You need quality evaluation → `skill-evaluation`
- You need lifecycle state tracking → `skill-lifecycle-management`
- You need safety or security audit → `skill-safety-review`

# Procedure

## 1. Document origin
- If adapted: source URL, percentage original vs adapted
- If created from scratch: state "created", note the motivating requirement
- If derived from multiple sources: list all, note which informed which sections

## 2. Record authorship
- Original author(s) with identifiers
- Adapter(s) if modified, with date of adaptation
- Reviewer(s) if peer-reviewed

## 3. Document evidence basis
- Which documentation informed the procedure steps?
- Which standards or best practices were referenced?
- Which expert knowledge was encoded and by whom?
- Which failure patterns were learned from?

## 4. Catalog encoded assumptions
- Runtime environment requirements (OS, tool versions, runtimes)
- Expected conventions (file layout, naming, package manager)
- Implicit dependencies not declared in frontmatter

## 5. Assess trust level

| Level | Criteria |
|-------|----------|
| **High** | Known author, peer-reviewed, tested, actively maintained |
| **Medium** | Known source, partial testing, no formal review |
| **Low** | Unknown or unverified source, untested |
| **Untrusted** | External import, not yet reviewed |

Assign one level. Write a one-sentence rationale.

# Output contract

Produce exactly two artifacts:

**1. Frontmatter patch** — merge into the skill's existing YAML metadata:
```yaml
metadata:
  provenance:
    origin: "https://... or created"
    adaptation_pct: 30  # omit if 0
    trust: high | medium | low | untrusted
    evidence: ["URL or short citation", ...]
```

**2. PROVENANCE.md** — co-located next to SKILL.md:
```markdown
# Provenance: [skill-name]

## Origin
- **Source**: [URL or "created"]
- **Author**: [name/handle]
- **Adapted by**: [name] on [YYYY-MM-DD]

## Evidence Basis
- [source] — informed [which sections]

## Encoded Assumptions
- [assumption with specifics]

## Trust Level: [High|Medium|Low|Untrusted]
**Rationale**: [one sentence]
```

If the skill is too trivial for a full record, produce the frontmatter patch only and skip PROVENANCE.md. Note the decision in the commit message.

# Failure handling

| Scenario | Action |
|----------|--------|
| Origin unknown | Set `origin: "unknown"`, trust to `low`, add `## Gaps` section listing what is missing |
| Author unreachable | Document what is known, mark authorship as "unverified" in PROVENANCE.md |
| Assumptions undeterminable | Set trust to `low` with rationale "assumptions undocumented—treat as fragile" |
| Multiple conflicting sources | List all sources with which takes precedence and why |
