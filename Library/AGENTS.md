# AGENTS.md

This repository is a skill library — it contains 350 agent skills organized into 17 categories. It is **not** a runnable application.

## For AI Agents Working in This Repo

### What this repo is
A collection of SKILL.md files and supporting materials (references, evals, overlays) that can be installed into any compatible AI coding agent. Each skill is a self-contained playbook for a specific task domain.

### Repository structure
```
skilllibrary/
├── 01-package-scaffolding/       # 20 skills — scaffolding, Scafforge flow
├── 02-generated-repo-core/       # 32 skills — core engineering patterns
├── 03-meta-skill-engineering/    # 18 skills — skill creation and maintenance
├── 04-planning-review-and-critique/ # 18 skills — thinking techniques
├── 05-agentic-orchestration-and-autonomy/ # 20 skills — multi-agent patterns
├── 06-agent-role-candidates/     # 16 skills — specialized agent roles
├── 07-mcp/                       # 20 skills — Model Context Protocol
├── 08-web-frontend-and-design/   # 26 skills — frontend frameworks
├── 09-backend-api-and-data/      # 20 skills — backend patterns
├── 10-cli-systems-and-ops/       # 20 skills — CLI and systems
├── 11-ai-llm-runtime-and-integration/ # 28 skills — LLM runtime
├── 12-ai-llm-training-architecture-and-research/ # 23 skills — ML training
├── 13-game-engines-and-creative-tech/ # 17 skills — game development
├── 14-cloud-platform-devops/     # 19 skills — cloud and deployment
├── 15-docs-artifacts-media/      # 33 skills — document generation
├── 16-business-research-and-optional-domains/ # 12 skills — business
├── 17-external-reference-seeds/  # 8 skills — research and evaluation
├── skill-improver/               # The skill improvement tool
├── taskfiles/                    # Source specifications and manifests
├── official-docs-by-skill-library-category.md  # Reference doc index
├── README.md                     # User-facing documentation
├── AGENTS.md                     # This file
└── opusworkedonlibrary.md        # Change log for skill improvements
```

### How to work with skills in this repo

**Reading a skill**: Each skill lives in `XX-category/skill-name/SKILL.md`. The frontmatter contains routing metadata; the body contains the operating procedure.

**Improving a skill**: Use the skill-improver methodology (see `skill-improver/skill-improver/SKILL.md`). Diagnose → improve → verify. Don't bloat.

**Adding a new skill**: Follow the format in `taskfiles/ideal-agent-skills-architecture-spec-v2-templates.md`. Place in the appropriate category folder.

**Evaluating quality**: Check for: specific trigger phrases in description, concrete numbered steps in procedure, named failure modes, DO NOT USE boundaries with alternatives.

### Rules for agents
- Do not install skills from this repo into the system — this is a library, not an installer
- When editing skills, preserve the frontmatter schema
- Keep skills focused — one job per skill
- Reference official documentation, not blog posts or tutorials
- Test description changes mentally: would a router select this skill correctly?

### Key reference files
- `official-docs-by-skill-library-category.md` — canonical documentation URLs per category
- `taskfiles/ideal-agent-skills-architecture-spec-v2-templates.md` — SKILL.md template and description-writing rules
- `taskfiles/MANIFEST.md` — original 315-skill manifest with categories and priorities
