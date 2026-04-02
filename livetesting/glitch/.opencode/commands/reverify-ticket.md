---
description: Restore trust on a completed ticket using linked remediation evidence
agent: glitch-team-leader
model: minimax-coding-plan/MiniMax-M2.7
---

Resolve the historical ticket, confirm the linked remediation evidence, and use the reverification flow to restore trust only when the evidence closes the original defect.

Rules:

- Treat this slash command as a human entrypoint only.
- Use `ticket_reverify` rather than editing trust fields manually.
- Require current evidence from the same ticket or a linked follow-up ticket before restoring trust.
- Link any remediation evidence back to the historical ticket before claiming the defect is closed.
