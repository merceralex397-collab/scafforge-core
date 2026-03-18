---
name: skill-catalog-curation
description: Audit and organize a skill library as a whole — detect duplicates, enforce category consistency, mark deprecation candidates, and ensure discoverability. Use this when the library has grown large enough that overlaps and inconsistencies emerge, before major releases, after bulk imports, or for periodic maintenance. Do not use for improving individual skills (use skill-refinement) or creating new skills (use skill-authoring).
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-catalog-curation
  maturity: draft
  risk: low
  tags: [skill, catalog, curation]
---

# Purpose
Reviews skill library as a whole: identifies duplicates/overlaps, enforces category consistency, assigns quality gates, marks deprecated skills, and ensures catalog remains navigable as it grows.

# When to use this skill
Use when:
- User says "audit the library", "clean up skills", "organize catalog"
- Library grown large enough that overlaps/inconsistencies emerge
- Periodic maintenance (recommend: monthly for active libraries)
- Before major release
- After bulk import

Do NOT use when:
- Working on single skill
- Installing/packaging skills
- Creating new skills (use `skill-authoring`)
- Library small (<20) and well-organized

# Operating procedure
1. **Generate inventory**:
   - List all skills: name, category, maturity, last modified
   - Count per category
   - Identify uncategorized/miscategorized
2. **Detect duplicates/overlaps**:
   - Compare descriptions for similarity
   - Flag >70% overlap
   - Flag same name, different paths
   - Recommend: merge, differentiate, or keep
3. **Audit category assignments**:
   - List all categories
   - Check each skill's category matches function
   - Categories with 1-2 skills → consider merging
   - Categories with >15 skills → consider splitting
4. **Apply quality gates**:
   - **Draft**: Missing evals, incomplete, new
   - **Stable**: Has evals, complete, tested
   - **Deprecated**: Superseded, has replacement
   - Flag mismatched maturity
5. **Check discoverability**:
   - Descriptions clear and searchable?
   - Trigger phrases present?
   - Would user find when needed?
6. **Mark deprecation candidates**:
   - No usage (if metrics available)
   - Superseded by better alternative
   - For obsolete tools
7. **Generate report**:
   - Summary stats
   - Action items by priority
   - Recommendations

# Output defaults
```
## Catalog Curation Report

### Summary
- Total: 47 skills
- Maturity: 12 draft, 30 stable, 5 deprecated
- Categories: 8

### Duplicates/Overlaps
| A | B | Similarity | Action |
|---|---|------------|--------|
| api-testing | api-test | 85% | Merge |

### Category Issues
| Issue | Skills | Action |
|-------|--------|--------|
| Miscategorized | X | Move to Y |

### Quality Violations
| Skill | Current | Issue | Action |
|-------|---------|-------|--------|
| skill-a | stable | No evals | Demote |

### Deprecation Candidates
| Skill | Reason | Replacement |
|-------|--------|-------------|
| old-api | Deprecated | new-api |

### Actions (Priority Order)
1. [High] Merge duplicates
2. [Medium] Add missing evals
3. [Low] Reorganize categories
```

# References
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skills structure
- https://developers.openai.com/codex/skills — Codex skill format for consistency checks
- Library index/catalog files

# Failure handling
- **Can't determine similarity**: Manual review for edge cases
- **Conflicting categories**: Propose unified scheme
- **No usage metrics**: Base on age + last modified
- **Too many issues**: Prioritize by impact, create phases
