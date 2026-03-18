---
name: skill-installer
description: Install skills into an agent client environment from a curated registry, GitHub repository, local folder, or packaged bundle. Use this when the user says "install this skill", "add skill from GitHub", "list available skills", "set up skill X", or asks about installable skills. Handles listing available skills, downloading, extracting, verifying integrity, and registering with the target client. Do not use for creating new skills (use skill-authoring or skill-creator), packaging skills for distribution (use skill-packaging), or improving existing installed skills (use skill-refinement).
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: meta-skill-engineering
  maturity: stable
  risk: low
  tags: [skill, installation, installer, registry, codex]
---

# Purpose

Installs skill packages into a local environment or agent client configuration. Handles listing available skills, downloading from registries or GitHub, extraction, integrity verification, client-specific placement, and registration so the skill is discoverable and usable.

# When to use this skill

Use when:

- User says "install this skill", "add skill from X", "set up skill", "list skills"
- Installing from a curated registry (e.g., `npx skills add skill-name`)
- Installing from GitHub: `npx skills add owner/repo` or `--url https://github.com/...`
- Installing from local tarball, zip, or folder
- Listing available skills from curated or experimental collections
- Linking a local folder for skill development

Do NOT use when:

- Creating or authoring a skill (use `skill-authoring` or `skill-creator`)
- Packaging a skill for distribution (use `skill-packaging`)
- Skill already installed and just needs configuration
- Uninstalling or removing a skill

# Operating procedure

## Listing available skills

1. Run `scripts/list-skills.py` to show curated skills with install status
2. For experimental skills: `scripts/list-skills.py --path skills/.experimental`
3. For JSON output: `scripts/list-skills.py --format json`
4. Present results as numbered list with "(already installed)" annotations
5. Ask user which skills they want installed

## Installing from curated registry or GitHub

1. **Identify source**:
   - Curated: `scripts/install-skill-from-github.py --repo openai/skills --path skills/.curated/<name>`
   - Experimental: `scripts/install-skill-from-github.py --repo openai/skills --path skills/.experimental/<name>`
   - Any GitHub repo: `scripts/install-skill-from-github.py --repo <owner>/<repo> --path <path/to/skill>`
   - By URL: `scripts/install-skill-from-github.py --url https://github.com/<owner>/<repo>/tree/<ref>/<path>`
2. **Download**: Scripts default to direct download for public repos; fall back to git sparse checkout on auth errors
3. **Install**: Skills install to `$CODEX_HOME/skills/<skill-name>` (default: `~/.codex/skills`)
4. **Verify**: Confirm folder exists with SKILL.md
5. **Report**: Tell user "Restart Codex to pick up new skills"

## Installing from local source

1. **Local folder**: Verify SKILL.md exists at path
2. **Tarball/zip**: Extract to temp, verify contents
3. **Verify integrity**: Check manifest.yaml if present; verify SHA-256 checksum
4. **Copy to target location** based on client:
   - Codex: `$CODEX_HOME/skills/<name>/`
   - GitHub Copilot (VS Code): `.github/skills/<name>/` or `.vscode/skills/<name>/`
   - Claude Code: project `.claude/skills/<name>/` or user `~/.claude/skills/<name>/`
   - Gemini CLI: `.gemini/skills/<name>/`
5. **Register**: Update any config files or skill indexes
6. **Verify**: Skill discoverable by client

## Script reference

All scripts require network access — request sandbox escalation when running.

| Script | Purpose |
|--------|---------|
| `scripts/list-skills.py` | List available skills with install annotations |
| `scripts/install-skill-from-github.py` | Install from any GitHub location |

Options for install script:
- `--repo <owner>/<repo>` — GitHub repository
- `--path <path>` — Path within repo (multiple allowed)
- `--url <url>` — Full GitHub URL
- `--ref <ref>` — Git ref (default: main)
- `--dest <path>` — Custom install destination
- `--method auto|download|git` — Download method
- `--name <name>` — Override skill name

# Output defaults

```
## Installation Complete

**Skill**: skill-name
**Location**: ~/.codex/skills/skill-name/
**Source**: [registry/GitHub/local]

### Verification
- [x] Files extracted
- [x] SKILL.md present
- [x] Registered

### Next Step
Restart Codex to pick up new skills.
Triggers on: [description summary]
```

# References

- https://developers.openai.com/codex/skills — Codex skill format and installation
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — GitHub agent skills
- https://docs.anthropic.com/en/docs/claude-code/overview — Claude Code skill placement
- https://geminicli.com/docs/cli/skills/ — Gemini CLI skills
- Curated skills: https://github.com/openai/skills/tree/main/skills/.curated
- Experimental skills: https://github.com/openai/skills/tree/main/skills/.experimental

# Notes

- System skills at https://github.com/openai/skills/tree/main/skills/.system are preinstalled. If asked, explain this. If user insists, download and overwrite.
- Private GitHub repos accessible via git credentials or `GITHUB_TOKEN`/`GH_TOKEN`
- Git fallback tries HTTPS first, then SSH
- Installation aborts if destination directory already exists (prevents accidental overwrites)

# Failure handling

- **Checksum mismatch**: Do not install — report "Integrity verification failed, package may be corrupted or tampered with"
- **Auth/permission error on download**: Fall back to git sparse checkout; if that fails, suggest user set GITHUB_TOKEN
- **Destination already exists**: Ask user: overwrite, skip, or install as different version?
- **Incompatible client**: Report which clients are supported, suggest manual placement
- **Missing SKILL.md in source**: Abort — "Not a valid skill package: no SKILL.md found"
- **Network unavailable in sandbox**: Request sandbox escalation for network access
