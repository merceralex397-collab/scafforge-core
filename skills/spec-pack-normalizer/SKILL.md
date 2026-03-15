---
name: spec-pack-normalizer
description: Normalize one or more source specs, notes, pasted chats, and Markdown planning documents into a single canonical brief, decision packet, and constraints summary. Use when a host agent is given messy or multi-file project requirements and needs to turn them into a clean source of truth before scaffolding, ticketing, or implementation.
---

# Spec Pack Normalizer

Use this skill to convert source material into a deterministic brief that weaker models can follow safely.

## Workflow

1. Scan the input opportunistically: primary specs first, then supporting notes, chats, and fragmented docs.
2. Extract only durable facts, constraints, desired outcomes, explicit non-goals, and clearly stated preferences.
3. Resolve obvious duplication and contradiction by preferring the most specific or latest source, but do not smooth over meaningful disagreements.
4. Produce a canonical brief, source-of-truth map, batched decision packet, and backlog-readiness summary.
5. Keep the brief structured and signposted so it can be used by scaffolding, ticketing, and OpenCode agents without rereading the entire source pack.

## Output shape

Use the schema in `references/brief-schema.md`.

Minimum sections:

- Project summary
- Goals
- Non-goals
- Constraints
- Repo/output requirements
- Tooling/model constraints
- Canonical truth map
- Blocking decisions
- Non-blocking open questions
- Backlog readiness
- Acceptance signals
- Assumptions

## Rules

- Prefer opportunistic intake over rigid required input structure.
- Separate facts from assumptions explicitly.
- Do not hide contradictions; call them out in the decision packet or open questions.
- Keep the final brief concise enough to be loaded by weaker models.
- Preserve exact product names, provider strings, and model identifiers when they are specified.
- Do not invent implementation-ready detail for work that depends on unresolved major choices.
- Mark backlog readiness explicitly so downstream ticket generation knows whether it can detail the first execution wave or must stop and ask.
