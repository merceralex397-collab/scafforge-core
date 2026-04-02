---
name: glitch-design-guardrails
description: Keep Glitch mechanics fair, readable, and on-theme when implementing hazards, movement changes, and simulation-corruption events.
---

# Glitch Design Guardrails

Before using this skill, call `skill_ping` with `skill_id: "glitch-design-guardrails"` and `scope: "project"`.

Use this skill when a ticket touches:

- physics glitches
- platform glitches
- hazard timing changes
- camera or visual corruption effects
- checkpoint or rule-mutation systems

Guardrails:

- major state changes need telegraphing
- early-game glitches should not produce unavoidable instant deaths
- recovery space matters as much as surprise
- visual corruption must not hide collision-critical information
- do not stack multiple uncontrollable states unless the ticket explicitly targets late-game escalation
- narrative framing should reinforce the idea of simulation instability rather than random gimmicks
