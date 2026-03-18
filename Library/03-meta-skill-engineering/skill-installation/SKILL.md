---
name: skill-installation
description: "REDIRECTED — This skill has been merged into skill-installer, which handles all skill installation workflows. Use skill-installer instead."
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: meta-skill-engineering
  maturity: deprecated
  risk: low
  tags: [skill, installation, deprecated, redirect]
---

# This skill has been merged into `skill-installer`

The functionality of `skill-installation` (generic client installation workflow) has been consolidated into `skill-installer`, which now covers:

- Installing from curated registries and GitHub
- Installing from local folders, tarballs, and zips
- Client-specific placement (Codex, GitHub Copilot, Claude Code, Gemini CLI)
- Integrity verification and registration

**Use `skill-installer` for all installation tasks.**

The merge was performed because both skills covered the same user intent ("install this skill") with overlapping procedures. `skill-installer` was chosen as the canonical name because it is more concise and already had operational scripts.
