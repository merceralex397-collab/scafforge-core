---
name: ticket-pack-builder
description: Create a repo-local ticket system with an index, machine-readable manifest, board, and individual ticket files. Use when a repo needs task decomposition that autonomous agents can follow without re-planning the whole project each session.
---

# Ticket Pack Builder

Use this skill to create or refine the repo-local work queue.

## Modes

- **bootstrap**: generate the first implementation-ready backlog during the initial scaffold
- **refine**: regenerate, expand, or normalize an existing backlog later

## Bootstrap mode procedure

### 1. Read the canonical brief

Read `docs/spec/CANONICAL-BRIEF.md`. Identify:
- What features/capabilities need to be built
- What infrastructure/setup is required
- What the acceptance criteria are
- Which areas are blocked on unresolved decisions
- The backlog readiness signal

### 2. Break work into implementation waves

Organize tickets into waves based on dependency order:

- **Wave 0: Foundation** — repo setup, CI/CD, dependency installation, configuration
- **Wave 1: Core** — the primary functionality the project exists to provide
- **Wave 2: Secondary** — supporting features, integrations, secondary workflows
- **Wave 3: Polish** — error handling hardening, performance, documentation, UX refinement

### 3. Create individual tickets

For each piece of work, create a ticket with these fields:
- `id` — unique identifier (e.g., `SETUP-001`, `CORE-001`, `FEAT-001`)
- `title` — short descriptive title
- `lane` — which wave this belongs to
- `stage` — `planning` (all new tickets start here)
- `status` — `todo` or `blocked`
- `depends_on` — list of ticket IDs this depends on
- `summary` — one-paragraph description of what needs to be done
- `acceptance` — list of specific acceptance criteria
- `artifacts` — empty list (populated during execution)
- `decision_blockers` — list of unresolved decisions that block this ticket (empty if none)

### Ticket sizing rules

- Each ticket should be completable in ONE agent session
- If a ticket requires changes to more than 5-7 files, split it
- If a ticket has more than 5 acceptance criteria, consider splitting
- Prefer many small tickets over few large ones

### Handling unresolved decisions

- Do NOT fabricate implementation detail for work that depends on unresolved major choices
- Create explicit `blocked` tickets with `decision_blockers` listing what needs to be decided
- Create `decision` tickets for choices the team needs to make (e.g., "Choose database engine")
- Create `discovery` tickets for research that needs to happen before implementation

### 4. Write ticket files

For each ticket, write a markdown file to `tickets/<id>.md` using the template in `assets/templates/TICKET.template.md`.

### 5. Update the manifest

Write `tickets/manifest.json` with the structure defined in `references/ticket-system.md`:
- `version`: 1
- `project`: project name from canonical brief
- `active_ticket`: first ticket in wave 0
- `tickets`: array of all ticket objects

### 6. Generate the board

Write `tickets/BOARD.md` as a human-readable view of the backlog organized by wave, showing:
- Ticket ID, title, status, dependencies
- Grouped by wave
- This is a DERIVED VIEW — the manifest is the source of truth

### 7. Align workflow state

Ensure `.opencode/state/workflow-state.json` reflects the first active ticket:
```json
{
  "active_ticket": "<first-ticket-id>",
  "stage": "planning",
  "status": "ready",
  "approved_plan": false
}
```

## Refine mode

Use when expanding or normalizing an existing backlog:
1. Read the existing manifest
2. Identify gaps, unclear tickets, or new work from updated brief
3. Add/modify tickets following the same rules
4. Regenerate BOARD.md

## After this step

Continue to `../project-skill-bootstrap/SKILL.md` as directed by scaffold-kickoff.

## Rules

- Keep manifest machine-readable
- Keep board human-readable (derived from manifest)
- Keep queue status coarse: `todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `done`
- Do NOT use ticket status for transient approval state (that's in workflow-state.json)
- Record dependencies explicitly
- Put acceptance criteria on every ticket

## References

- `references/ticket-system.md` for the contract
- `assets/templates/TICKET.template.md` for the ticket template
