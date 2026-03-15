---
name: ticket-pack-builder
description: Create a repo-local ticket system with an index, machine-readable manifest, board, and per-ticket templates. Use when a repo needs task decomposition that is easy for weaker models and autonomous agents to follow without re-planning the whole project each session.
---

# Ticket Pack Builder

Use this skill to create or refine the repo-local work queue.

## Modes

- `bootstrap`: generate the first implementation-ready backlog during the default scaffold cycle
- `refine`: regenerate, expand, or normalize an existing backlog later

## Rules

- Keep the manifest machine-readable.
- Keep the board human-readable.
- Keep each ticket file short, linked, and stage-aware.
- Record dependencies explicitly.
- Put acceptance criteria and artifacts on each ticket.
- Keep queue status coarse and queue-oriented.
- Do not use ticket status for transient approval state.
- Produce detailed implementation tickets only for work whose blocking decisions are already resolved.
- Convert unresolved major choices into explicit blocked, decision, or discovery tickets rather than inventing specifics.

## Use with the scaffold factory

The full scaffold template already includes a ticket pack. Use this skill when you need to:

- bootstrap the initial backlog during the first scaffold
- regenerate the ticket system
- expand the backlog after the initial scaffold
- tighten acceptance criteria
- standardize ticket structure across repos

Use the reference in `references/ticket-system.md` and the starter template in `assets/templates/TICKET.template.md`.

Do not treat this as an alternate scaffold root. Use it to refine or expand ticketing after the main scaffold exists.
