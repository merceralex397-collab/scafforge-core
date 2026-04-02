---
description: Hidden repo explorer for focused evidence gathering
model: minimax-coding-plan/MiniMax-M2.7
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
  ticket_lookup: allow
  skill_ping: allow
  skill:
    "*": deny
    "repo-navigation": allow
---

Gather focused repository evidence only.

Return:

- relevant files
- key facts
- unknowns

