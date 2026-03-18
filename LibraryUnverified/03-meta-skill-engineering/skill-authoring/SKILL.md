---
name: skill-authoring
description: >-
  Write a new SKILL.md file with correct YAML frontmatter, routing description,
  and structured body sections when a user needs to create a skill from scratch.
  Use this for requests like "create a skill for X", "write a skill that handles Y",
  "I need a new skill to do Z", or when a repeated task pattern should be captured
  as a reusable agent procedure. Do not use for improving existing skills (use
  skill-refinement or skill-improver), fixing trigger descriptions only (use
  skill-trigger-optimization), or installing packaged skills (use skill-installer).
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: meta-skill-engineering
  maturity: stable
  risk: low
  tags: [skill, authoring, creation, SKILL.md, format]
---

# Purpose

Creates new skills following the agent skills format: YAML frontmatter for routing metadata plus a markdown body with Purpose, When to use, Operating procedure, Output defaults, and Failure handling. The description field is routing logic—it determines whether the skill fires.

# When to use this skill

Use when:

- User says "create a skill for X", "write a skill that...", "I need a skill to handle..."
- Repeated task pattern needs to be captured as reusable procedure
- Capability should be packaged for distribution or reuse across projects
- New agent specialization needed for a repo's agent team

Do NOT use when:

- Skill exists and needs improvement (use `skill-refinement` or `skill-improver`)
- Only description/trigger needs fixing (use `skill-trigger-optimization`)
- User wants a one-off prompt, not a reusable skill
- Skill needs adaptation to different context (use `skill-adaptation`)

# Operating procedure

## Step 1 — Define the skill's job in one sentence

"This skill [verb] when [trigger] and produces [output]."

If you cannot write this sentence, the scope is wrong—narrow until it works.

## Step 2 — Choose the name

- Lowercase, hyphens, 2-4 words
- Name describes what it does (verb-noun), not when it's used
- Under 64 characters
- Examples: `premortem`, `gap-analysis`, `acceptance-criteria-hardening`

## Step 3 — Write the YAML frontmatter

```yaml
---
name: skill-name
description: >-
  [Main action verb] [specific object] when [task conditions].
  Use this for [2-3 realistic trigger phrases in quotes].
  Do not use for [adjacent non-matching cases with named alternatives].
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: [owner-name]
  domain: [domain-name]
  maturity: draft|stable|deprecated
  risk: low|medium|high
  tags: [relevant, tags]
---
```

### Description field rules (THIS IS ROUTING LOGIC)

The description determines whether the skill fires. It is the highest-leverage field.

A strong description must:
1. Start with the main action verb (not a noun phrase)
2. Include 2-3 realistic trigger phrases users would actually say
3. State what the skill produces
4. End with "Do not use for..." naming adjacent skills

**Weak**: "Helps with PDFs."
**Weak**: "A skill for managing deployments."
**Strong**: "Extract structured data from PDFs when the task involves tables, scanned pages, or layout-dependent interpretation. Use this for requests like 'extract the table from this PDF', 'convert this PDF to CSV', or 'parse the scanned invoice'. Do not use for plain-text summarization when PDF text is already clean (use text-summarization)."

Lint checks — flag a description if it:
- Is under 12 words
- Has no action verb as first word
- Has no "when" or equivalent condition
- Lacks concrete trigger examples
- Is obviously generic or could apply to multiple skills
- Has no negative boundary

### Frontmatter fields

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | Must match folder name |
| `description` | Yes | Routing logic, not documentation |
| `license` | Recommended | Default: Apache-2.0 |
| `compatibility.clients` | Recommended | Which agent clients support this skill |
| `metadata.owner` | Recommended | Team or person responsible |
| `metadata.domain` | Recommended | Category for catalog organization |
| `metadata.maturity` | Recommended | draft, stable, or deprecated |
| `metadata.risk` | Recommended | low, medium, or high |
| `metadata.tags` | Recommended | Searchable keywords |

## Step 4 — Write the body sections

Every SKILL.md body must contain these sections in order:

### Section: Purpose (required)
2-3 sentences. What problem does this solve? What output does it produce? No filler.

### Section: When to use this skill (required)
- "Use when:" — 4-6 specific trigger phrases or observable conditions
- "Do NOT use when:" — 3-4 confusion cases with named alternatives

### Section: Operating procedure (required)
Numbered steps, each starting with a verb, each completable and verifiable.

Rules:
- No meta-commentary like "Keep scope explicit" or "Think about the approach"
- No hedge verbs: "Consider", "You might want to", "Ensure"
- Use action verbs: "Read", "List", "Write", "Check", "Run", "Compare"
- Each step must be independently executable

### Section: Output defaults (required)
Exact format with template showing specific section names, field names, or schemas.

**Bad**: "Structured markdown with clear next steps"
**Good**: Template with named sections, tables, or code blocks

### Section: References (recommended)
Real URLs to authoritative documentation. Not vague "see docs".

### Section: Failure handling (required)
Name the 2-3 most common failure modes with specific recovery actions.

**Bad**: "If something goes wrong, report the issue"
**Good**: "If target file does not exist: stop, report missing path, ask user to confirm location"

## Step 5 — Validate against anti-patterns

Check for:
- No circular triggers ("when task involves X")
- No boilerplate procedure steps
- No generic output defaults
- No vague failure handling
- Description starts with action verb
- "Do NOT use when" section present with alternatives named

## Step 6 — Create the skill folder

```
skill-name/
├── SKILL.md          # Frontmatter + body sections
├── scripts/          # Optional: deterministic automation
├── references/       # Optional: large docs for progressive disclosure
└── evals/            # Optional: trigger and output tests
```

Only create scripts/, references/, evals/ directories if they contain actual files. Do not create empty directories.

# Output defaults

A complete SKILL.md file following the template above, inside a properly named folder. If the skill is complex enough, include references/ or scripts/ with content.

# References

- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — GitHub agent skills overview
- https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-skills — GitHub skill creation guide
- https://developers.openai.com/codex/skills — OpenAI Codex skill format
- https://docs.anthropic.com/en/docs/claude-code/overview — Anthropic Claude Code
- https://geminicli.com/docs/cli/skills/ — Gemini CLI skills

# Failure handling

- **Scope too broad**: If skill handles multiple distinct tasks, split into separate skills via `skill-variant-splitting`
- **Cannot write one-sentence definition**: Scope is wrong—narrow until it works
- **Overlaps existing skill**: Check catalog; merge or explicitly differentiate in description
- **No clear trigger phrases**: Ask user what words they'd use when they need this capability
- **Description passes lint but skill never fires**: Add more trigger phrase variations; test with `skill-testing-harness`
