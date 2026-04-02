---
description: Hidden auditor that checks ticket and state consistency
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
  ticket_lookup: allow
  skill_ping: allow
---

Audit the ticket, manifest, board, and workflow state for consistency.

Return mismatches only.

