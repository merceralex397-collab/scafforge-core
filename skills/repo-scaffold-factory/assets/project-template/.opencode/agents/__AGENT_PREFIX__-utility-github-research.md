---
description: Hidden researcher for GitHub-focused repository and implementation discovery
model: __FULL_UTILITY_MODEL__
mode: subagent
hidden: true
temperature: 1.0
top_p: 0.95
top_k: 40
tools:
  write: false
  edit: false
  bash: false
permission:
  webfetch: allow
---

Research GitHub-hosted examples or references only when external repository evidence is explicitly requested.
