---
name: ticket-pack-builder
description: Create a repo-local ticket system with an index, machine-readable manifest, board, and individual ticket files. Use when a repo needs task decomposition that autonomous agents can follow without re-planning the whole project each session.
---

# Ticket Pack Builder

Use this skill to create or refine the repo-local work queue.

## Modes

- **bootstrap**: generate the first implementation-ready backlog during the initial scaffold
- **refine**: regenerate, expand, or normalize an existing backlog later
- **remediation-follow-up**: add or normalize canonical follow-up tickets after audit, diagnosis, review, or repair work identifies concrete remediation or reverification needs

## Mode selection

- If this skill is reached from `scaffold-kickoff` during greenfield scaffolding, use `bootstrap`.
- If this skill is reached from retrofit or later backlog maintenance work, use `refine`.
- If audit, diagnosis, generated review, or repair outputs already identify specific remediation or reverification work, use `remediation-follow-up`.
- If invoked directly and `tickets/manifest.json` does not exist yet, use `bootstrap`.
- If invoked directly and a backlog already exists, use `refine` unless the request is explicitly about post-audit or post-repair follow-up, in which case use `remediation-follow-up`.
- If the user request is ambiguous about whether to create the first backlog or revise an existing one, ask the user before choosing a mode.

## Bootstrap mode procedure

### 1. Read the finalized generation surfaces

Read:
- `docs/spec/CANONICAL-BRIEF.md`
- `.opencode/skills/`
- `.opencode/agents/`
- `.opencode/commands/`
- `.opencode/state/workflow-state.json`

Identify:
- What features/capabilities need to be built
- What infrastructure/setup is required
- What the acceptance criteria are
- Which areas are blocked on unresolved decisions
- The backlog readiness signal
- The finalized repo-local validation commands and workflow surfaces

### 2. Break work into implementation waves

Organize tickets into waves based on dependency order:

- **Wave 0: Foundation** — repo setup, environment bootstrap, dependency installation, configuration
- **Wave 1: Core** — the primary functionality the project exists to provide
- **Wave 2: Secondary** — supporting features, integrations, secondary workflows
- **Wave 3: Polish** — error handling hardening, performance, documentation, UX refinement

### 3. Create individual tickets

For each piece of work, create a ticket with these fields:
- `id` — unique identifier (e.g., `SETUP-001`, `CORE-001`, `FEAT-001`)
- `title` — short descriptive title
- `wave` — which execution wave this belongs to
- `lane` — which project area or ownership lane this belongs to
- `parallel_safe` — whether this ticket can be advanced in parallel with other tickets when dependencies are satisfied
- `overlap_risk` — `low`, `medium`, or `high` expected overlap with other tickets
- `stage` — `planning` (all new tickets start here)
- `status` — `todo` or `blocked` for new tickets; later lifecycle-aligned queue values are derived by `ticket_update`
- `resolution_state` — `open` for new tickets, later `done`, `reopened`, or `superseded`
- `verification_state` — `trusted` only after current proof exists; initialize new tickets as `suspect`
- `depends_on` — list of ticket IDs this depends on
- `source_ticket_id` — source ticket when this is a follow-up or remediation ticket, otherwise `null`
- `follow_up_ticket_ids` — linked downstream remediation or expansion tickets, initially empty
- `summary` — one-paragraph description of what needs to be done
- `acceptance` — list of specific acceptance criteria tied to finalized repo-local commands, checks, or observable workflow surfaces
- `artifacts` — empty list (populated during execution)
- `decision_blockers` — list of unresolved decisions that block this ticket (empty if none)

### Ticket sizing rules

- Each ticket should be completable in ONE agent session
- If a ticket requires changes to more than 5-7 files, split it
- If a ticket has more than 5 acceptance criteria, consider splitting
- Prefer many small tickets over few large ones

### Parallel lane rules

- Mark `parallel_safe: true` only when the ticket has no unresolved dependency on another unfinished ticket and the expected overlap risk is low
- Use `overlap_risk` to make concurrency judgment explicit instead of assuming it from lane names
- Default to `parallel_safe: false` when the ownership boundary is unclear
- Keep lane names aligned with real write ownership so lease-based execution has a credible boundary

### Mandatory Wave 0 bootstrap ticket

Wave 0 must always include one bootstrap/setup ticket that covers:
- runtime and toolchain presence
- project dependency installation
- test dependency installation
- verification command readiness
- initial canonical brief and scaffold sanity checks

Treat that ticket as the default first active ticket unless the canonical brief proves a different setup sequence is required.

### Handling unresolved decisions

- Do NOT fabricate implementation detail for work that depends on unresolved major choices
- Create explicit `blocked` tickets with `decision_blockers` listing what needs to be decided
- Create `decision` tickets for choices the team needs to make (e.g., "Choose database engine")
- Create `discovery` tickets for research that needs to happen before implementation

### 4. Write ticket files

For each ticket, write a markdown file to `tickets/<id>.md` using the template in `tickets/templates/TICKET.template.md`.

### 5. Update the manifest

Write `tickets/manifest.json` with the structure defined in `references/ticket-system.md`:
- `version`: 3
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
  "status": "todo",
  "approved_plan": false,
  "ticket_state": {
    "<first-ticket-id>": {
      "approved_plan": false,
      "reopen_count": 0,
      "needs_reverification": false
    }
  },
  "process_version": 5,
  "process_last_changed_at": null,
  "process_last_change_summary": null,
  "pending_process_verification": false,
  "parallel_mode": "sequential",
  "bootstrap": {
    "status": "pending",
    "last_verified_at": null,
    "environment_fingerprint": null,
    "proof_artifact": null
  },
  "lane_leases": [],
  "state_revision": 0
}
```

## Refine mode

Use when expanding or normalizing an existing backlog:
1. Read the existing manifest
2. Identify gaps, unclear tickets, or new work from updated brief
3. Add/modify tickets following the same rules
4. Regenerate BOARD.md

## Remediation-follow-up mode

Use when audit, diagnosis, review, or repair work already produced concrete findings and the repo needs canonical follow-up tickets.

### 1. Read the source evidence first

Collect the current source of truth for the follow-up:
- the latest diagnosis pack in `diagnosis/<timestamp>/` when working from `scafforge-audit`
- the current repair summary and recorded process-version state when working from `scafforge-repair`
- the latest registered `review`, `qa`, `smoke-test`, or `backlog-verification` artifacts when working inside a generated repo
- any machine-readable recommended-ticket payload emitted alongside the audit or diagnosis reports

Do not infer remediation work from vague commentary when canonical evidence already exists.

### 2. Decide whether to create, reopen, or defer

For each finding:
- create a new follow-up ticket when the work is net-new and scoped
- reopen or reverification-route an existing ticket when the historical ticket already owns the defect and current evidence justifies restoring or revising trust
- defer ticket creation when the evidence is incomplete or intent-changing and requires a human decision first

### 3. Preserve canonical linkage

For every remediation or reverification ticket:
- set `source_ticket_id` when the work came from a prior ticket
- append the new ticket ID to the source ticket's `follow_up_ticket_ids`
- keep `verification_state: suspect` until current evidence proves the issue resolved
- record the evidence source in the ticket summary or Notes so downstream agents can trace the follow-up back to the diagnosis, review, or repair artifact

### 4. Respect guarded ticket creation

When the generated repo exposes guarded ticket tooling:
- route creation through the canonical `ticket_create` flow instead of raw manifest edits when the workflow contract requires it
- preserve any source-mode or provenance fields that distinguish process verification, post-completion defects, or net-new scoped work

When operating at package level without the generated tooling available, emit the canonical ticket payload and update the generated ticket surfaces in the same contract shape the repo expects.

### 5. Regenerate derived views

After applying the follow-up:
- update `tickets/manifest.json`
- regenerate `tickets/BOARD.md`
- ensure any changed trust, reverification, or process-follow-up state stays consistent with `.opencode/state/workflow-state.json`

## After this step

Continue to `../handoff-brief/SKILL.md` as directed by scaffold-kickoff.

## Rules

- Keep manifest machine-readable
- Keep board human-readable (derived from manifest)
- Keep queue status coarse and aligned with the workflow tools: `todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`
- Do NOT use ticket status for transient approval state (that's in workflow-state.json)
- Treat `plan_review` and `smoke_test` as workflow-tool-owned queue values, not as free-form authoring choices
- Keep closeout acceptance criteria aligned with the deterministic `smoke_test` tool rather than generic PASS prose
- Keep `wave`, `lane`, `parallel_safe`, and `overlap_risk` aligned with real execution boundaries
- Record dependencies explicitly
- Put acceptance criteria on every ticket
- Prefer executable acceptance criteria where possible so downstream agents have concrete repo-local commands or observable pass/fail checks to run
- Keep historical completion separate from current trust: `status` stays queue-oriented, while `resolution_state` and `verification_state` represent historical closure and present trust
- Treat post-audit and post-repair ticket creation as a first-class workflow path, not an ad hoc backlog note
- Keep ticket docs, workflow docs, and ticket tools aligned on the same lifecycle semantics before handoff

## References

- `references/ticket-system.md` for the contract
- `assets/templates/TICKET.template.md` for the ticket template
