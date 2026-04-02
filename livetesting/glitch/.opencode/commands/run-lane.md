---
description: Run one bounded write-capable lane through the lease-based workflow
agent: glitch-team-leader
model: minimax-coding-plan/MiniMax-M2.7
---

Choose one ready ticket lane, claim the required coordinator-owned lease, delegate bounded implementation under that lease, then return control to the team leader for synthesis.

Rules:

- Treat this slash command as a human entrypoint only.
- The team leader owns `ticket_claim` and `ticket_release` for write-capable lane ownership.
- only Wave 0 setup work may claim a write-capable lease before bootstrap is ready.
- Delegated specialists work only inside the already-claimed lease; they do not claim or release their own ticket leases.
- Prefer `glitch-lane-executor` for bounded parallel implementation.
- Do not overlap write-capable work across lanes with conflicting paths or dependencies.
