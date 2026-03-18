---
name: skill-lifecycle-management
description: Manage skills through lifecycle states — draft, beta, stable, deprecated, archived — applying promotion criteria, deprecation rules, and transition tracking. Use this when auditing skill maturity across a library, promoting a tested skill to stable, retiring a superseded skill, or tracking which skills are production-ready. Do not use for authoring new skills (use skill-authoring), improving individual skill quality (use skill-refinement), or curating the library catalog as a whole (use skill-catalog-curation).
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-lifecycle-management
  maturity: draft
  risk: low
  tags: [skill, lifecycle, management]
---

# Purpose
Manages skills through their full lifecycle: draft → beta → stable → deprecated → archived. Ensures library stays coherent, retired skills don't break workflows, and maturity states reflect reality.

# When to use this skill
Use when:
- User says "manage lifecycle", "what state is this?", "how do we retire properly?"
- Library audit produced lifecycle actions needing execution
- Skill being promoted, revised, or retired
- Long-running project needs to track active/deprecated/archived

Do NOT use when:
- Deprecating one specific skill (use `skill-deprecation-manager`)
- Authoring new skill (use `skill-authoring`)
- Library <15 skills—lightweight tracking sufficient

# Operating procedure
1. **Define lifecycle states**:
   - `draft`: Being written, not validated—don't use in production
   - `beta`: Validated for basics, accepting feedback—use with monitoring
   - `stable`: Validated, promoted, default choice
   - `deprecated`: Replaced/not recommended—functional but don't use for new work
   - `archived`: Removed from active, reference only—don't install
2. **Audit current states**:
   - List skills with maturity field
   - Flag: draft >2 cycles, stable with bugs
3. **Apply promotion criteria**:
   - draft → beta: Tested with 3+ real prompts, passed
   - beta → stable: Evaluated with "Promote" verdict
4. **Apply deprecation criteria**:
   - Better replacement exists
   - Unused 3+ cycles
   - Consistently fails evaluation
5. **Execute transitions**:
   - Update `metadata.maturity`
   - Add event to PROVENANCE.md
6. **Notify dependents**:
   - If deprecated referenced in AGENTS.md, commands, skills—flag for update
7. **Update library index**

# Output defaults
```
## Lifecycle Audit

### State Summary
| State | Count | Skills |
|-------|-------|--------|
| draft | 5 | skill-a, skill-b, ... |
| stable | 20 | ... |

### Recommended Transitions
| Skill | Current | Recommended | Reason |
|-------|---------|-------------|--------|
| skill-x | draft | beta | 5 tests passed |
| skill-y | stable | deprecated | Superseded |

### Dependency Impact
| Deprecated | Referenced By | Action |
|------------|---------------|--------|
| skill-y | AGENTS.md L45 | Update reference |

### Actions
1. Promote skill-x to beta
2. Deprecate skill-y, update AGENTS.md
```

# References
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skill structure including maturity fields
- https://developers.openai.com/codex/skills — Codex skill metadata format
- Library index/catalog for current state inventory
- Individual skill frontmatter metadata.maturity fields

# Failure handling
- **Maturity not tracked**: Add `maturity` field to all skills based on evidence before proceeding
- **Circular dependencies on deprecated skill**: Create replacement first
- **Disputed maturity**: Default to more conservative state
