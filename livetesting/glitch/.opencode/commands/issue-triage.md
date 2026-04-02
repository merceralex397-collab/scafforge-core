---
description: Triage a defect discovered after prior ticket completion
agent: glitch-team-leader
model: minimax-coding-plan/MiniMax-M2.7
---

Collect the source ticket, evidence artifact, and defect classification, then route the issue through the canonical post-completion defect flow.

Rules:

- Treat this slash command as a human entrypoint only.
- Use `issue_intake` to choose between no action, follow-up, reopen, or rollback-required routing.
- Do not edit historical ticket or artifact history directly.
- Require current evidence before proposing remediation follow-up, and route canonical ticket changes through the guarded ticket workflow.
- If new evidence eventually restores trust on historical completion, route reverification with `ticket_reverify`.
