---
name: model-operating-profile
description: Apply the MiniMax 2.7 operating profile selected for Glitch when shaping prompts, delegation packets, and evidence requests.
---

# Model Operating Profile

Before reading anything else, call `skill_ping` with `skill_id: "model-operating-profile"` and `scope: "project"`.

Selected runtime profile:

- model tier: `weak`
- provider: `minimax-coding-plan`
- team lead / planner / reviewers: `minimax-coding-plan/MiniMax-M2.7`
- implementer: `minimax-coding-plan/MiniMax-M2.7`
- utilities, docs, and QA helpers: `minimax-coding-plan/MiniMax-M2.7`
- operating profile: `Weak-tier evidence-first profile`
- prompt density: `full checklists, explicit examples, and repeated truth-source reminders`

Use this profile when drafting:

- task prompts
- delegation briefs
- review requests
- handoff expectations

Profile guidance:

`Use the most explicit prompt density. Include full stop conditions, concrete examples, truth-source reminders, and named blocker paths so weaker models have one legal next move.`

Required rules:

- include explicit stop conditions and escalation triggers in every coordinating prompt
- spell out verification checklists instead of implying them
- name the canonical truth surfaces before acting on mutable or derived views
- use example-shaped outputs when they remove ambiguity
- keep each ask focused on one bounded goal at a time
- stop on blockers instead of guessing or silently filling gaps

Preferred output shape:

```text
Goal
Constraints
Required evidence
Expected artifact
Blockers
```
