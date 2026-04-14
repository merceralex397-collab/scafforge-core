---
name: ticket-pack-builder
description: Create a repo-local ticket system with an index, machine-readable manifest, board, and individual ticket files. Use when a repo needs task decomposition that autonomous agents can follow without re-planning the whole project each session.
---

# Ticket Pack Builder

Use this skill to create or refine the repo-local work queue.
Use [../../references/competence-contract.md](../../references/competence-contract.md) as the backlog-quality bar: a ticket is not good enough if its acceptance leaves the operator trapped between scope boundaries and a literal failing closeout command.

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
- What declared target platforms require dedicated export or release-proof lanes
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
- `source_mode` — `process_verification`, `post_completion_issue`, `net_new_scope`, or `split_scope` when the ticket was created from later diagnosis, reverification work, or open-parent decomposition; omit for greenfield bootstrap tickets
- `split_kind` — required when `source_mode` is `split_scope`; use `sequential_dependent` when the child must not run until the parent-owned work is complete, or `parallel_independent` when the child can truly advance independently; default to `sequential_dependent` unless project evidence proves the child has no dependency on the parent's open work
- For `EXEC-REMED-001` follow-up tickets that repair missing runnable review evidence on an open parent ticket, treat the child as `parallel_independent`: the parent stays open, but the evidence-repair child is the foreground work and must not deadlock behind the parent it is meant to unblock
- `finding_source` — original audit, review, QA, or smoke finding code when this ticket exists to remediate a validated issue
- `summary` — one-paragraph description of what needs to be done
- `acceptance` — list of specific acceptance criteria tied to finalized repo-local commands, checks, or observable workflow surfaces; these must be scope-isolated to the ticket's own work
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

### Mandatory target-completion tickets for declared Tier 1 release targets

If the canonical brief or bootstrap provenance declares a Tier 1 release target, create dedicated tickets for the target-completion path instead of burying that work inside generic polish.

For Godot Android repos, always create:

- `ANDROID-001` in lane `android-export`
- `SIGNING-001` in lane `signing-prerequisites` (only when the brief requires packaged delivery; see Product Finish Contract below)
- `RELEASE-001` in lane `release-readiness`

`ANDROID-001` acceptance must cover:

- `export_presets.cfg` exists with an Android preset
- repo-local `android/` support surfaces exist and are non-placeholder
- the canonical Android export command is recorded in the ticket and repo-local skills

`SIGNING-001` acceptance must cover (when packaged delivery is required):

- keystore ownership decision is made by the project team and recorded in the brief
- keystore path, alias, and password are available to the build environment
- signing mode (debug-only vs release-signed) is explicitly resolved in canonical truth

`RELEASE-001` acceptance must cover:

- `godot --headless --path . --export-debug "Android Debug" build/android/<project-slug>-debug.apk` or the exact resolved Godot-binary equivalent succeeds (runnable proof)
- the APK exists at `build/android/<project-slug>-debug.apk`
- `unzip -l` confirms Android manifest plus compiled classes or resources content
- when the finish contract requires packaged delivery: a signed release APK or AAB exists and `SIGNING-001` is closed

`RELEASE-001` must declare `depends_on` edges to two kinds of prerequisites:

1. **Infrastructure gate**: `SIGNING-001` when the brief requires packaged delivery. In debug-only mode, omit `SIGNING-001`.
2. **Feature gate (required)**: all terminal product tickets — the highest-wave tickets that are not in infrastructure lanes (`android-export`, `signing-prerequisites`, `release-readiness`) and not in process lanes (`remediation`, `reverification`). When the backlog has no such tickets, note the gap as a decision blocker on `RELEASE-001`.

`source_ticket_id` records split-scope lineage for provenance only. It is **not** a `depends_on` target. The workflow engine forbids a split-scope child from blocking on its `source_ticket_id` (deadlock rule). `RELEASE-001`'s `source_ticket_id` is `ANDROID-001` or `SIGNING-001`; neither must appear in `depends_on`.

Do not let a generic `POLISH-001`, UX, or validation ticket stand in for Android export or release proof ownership.

### Mandatory finish-ownership tickets for consumer-facing repos

If the canonical brief includes a Product Finish Contract (section 13) that forbids placeholder output in the final product, create explicit finish-ownership tickets instead of burying finish work in a generic polish bucket.

Finish work must be split into owned tickets that cover:

- finish direction or style decision if unresolved (create as a `blocked` or `decision` ticket)
- visual content production or integration (one ticket per distinct visual domain when scope warrants separation)
- audio content production or integration when the brief requires audio deliverables
- final finish validation against the recorded contract

Do not create one generic `FINISH-001` or `POLISH-001` ticket for all content work. The backlog must be specific enough for an agent to determine what constitutes completion for each owned area.

When the finish contract explicitly allows placeholder output in the shipped product (for example `placeholder_policy: placeholder_ok`), do not invent finish-ownership tickets for those content areas.

Leaving finish work as unwritten commentary outside the canonical backlog is not permitted when the Product Finish Contract records a non-placeholder finish bar.

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
- keep ticket objects aligned with the runtime contract in `.opencode/lib/workflow.ts`

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
  "process_version": 7,
  "process_last_changed_at": null,
  "process_last_change_summary": null,
  "pending_process_verification": false,
  "parallel_mode": "sequential",
  "bootstrap": {
    "status": "missing",
    "last_verified_at": null,
    "environment_fingerprint": null,
    "proof_artifact": null
  },
  "lane_leases": [],
  "state_revision": 0
}
```

## Output contract

Before leaving this skill, confirm all of these are true:
- `tickets/manifest.json` exists, uses `version: 3`, and every ticket record matches the runtime ticket contract
- `tickets/BOARD.md` exists and is clearly derived from the manifest instead of carrying extra machine state
- every `tickets/<id>.md` file exists for the manifest entries created or changed in this run
- `.opencode/state/workflow-state.json` names the foreground ticket from the manifest and seeds `bootstrap.status: "missing"` on fresh scaffolds until bootstrap proof exists
- any declared Tier 1 target platform has its canonical export or release-proof lane present in the manifest before handoff
- follow-up tickets preserve `source_ticket_id`, `follow_up_ticket_ids`, and `source_mode` linkage when the work came from diagnosis, repair, or reverification evidence
- remediation tickets preserve `finding_source` so downstream review, QA, and closeout can rerun the original failing check

## Refine mode

Use when expanding or normalizing an existing backlog:
1. Read the existing manifest
2. Identify gaps, unclear tickets, or new work from updated brief
3. Add/modify tickets following the same rules
4. Regenerate BOARD.md

## Remediation-follow-up mode

Use when audit, diagnosis, review, or repair work already produced concrete findings and the repo needs canonical follow-up tickets.

Public follow-up command when a diagnosis pack already contains ticket recommendations:

```sh
python3 skills/ticket-pack-builder/scripts/apply_remediation_follow_up.py <repo-root> --diagnosis <diagnosis-dir-or-manifest>
```

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
- set `finding_source` when the follow-up exists to remediate a validated audit, review, QA, or smoke-test finding
- keep `verification_state: suspect` until current evidence proves the issue resolved
- record the evidence source in the ticket summary or Notes so downstream agents can trace the follow-up back to the diagnosis, review, or repair artifact
- ensure the ticket acceptance reruns the original finding-producing command when the repo already has a concrete build, lint, reference, or smoke failure to clear

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

### 6. Emit canonical repair completion evidence when this ran as repair follow-up

When `scafforge-repair` required `ticket-pack-builder` as a repair follow-on stage, read `.opencode/meta/repair-follow-on-state.json` and, after the ticket follow-up work is actually complete, write:

- `.opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md`

Use this minimal shape so the public repair runner can auto-recognize completion for the current repair cycle on the next run:

```md
# Repair Follow-On Completion

- completed_stage: ticket-pack-builder
- cycle_id: <cycle_id from .opencode/meta/repair-follow-on-state.json>
- completed_by: ticket-pack-builder

## Summary

- Created or updated the canonical repair follow-up tickets required by the current repair cycle.
```

Do not write this artifact speculatively. Only emit it once the remediation-follow-up ticket work is actually complete for the current cycle.

## After this step

Continue to `../handoff-brief/SKILL.md` as directed by scaffold-kickoff.

## Rules

- Keep manifest machine-readable
- Keep board human-readable (derived from manifest)
- Keep queue status coarse and aligned with the workflow tools: `todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`
- Do NOT use ticket status for transient approval state (that's in workflow-state.json)
- Treat `plan_review` and `smoke_test` as workflow-tool-owned queue values, not as free-form authoring choices
- Keep closeout acceptance criteria aligned with the deterministic `smoke_test` tool rather than generic PASS prose
- When a ticket needs a smoke gate, prefer one explicit backticked repo-local smoke command so `smoke_test` can treat that command as the canonical smoke scope instead of improvising a heuristic subset or full-suite fallback
- Keep acceptance criteria scope-isolated. If a literal closeout command would still fail on later-ticket work, split the backlog differently or encode the dependency explicitly instead of shipping contradictory acceptance
- Keep `wave`, `lane`, `parallel_safe`, and `overlap_risk` aligned with real execution boundaries
- Record dependencies explicitly
- Put acceptance criteria on every ticket
- Prefer executable acceptance criteria where possible so downstream agents have concrete repo-local commands or observable pass/fail checks to run
- Do not generate a ticket whose literal acceptance command knowingly reaches into sibling-ticket or later-ticket scope
- Keep historical completion separate from current trust: `status` stays queue-oriented, while `resolution_state` and `verification_state` represent historical closure and present trust
- Treat post-audit and post-repair ticket creation as a first-class workflow path, not an ad hoc backlog note
- Keep ticket docs, workflow docs, and ticket tools aligned on the same lifecycle semantics before handoff

## References

- `references/ticket-system.md` for the contract
- `assets/templates/TICKET.template.md` for the package-side canonical ticket template; it must stay identical to the generated `tickets/templates/TICKET.template.md` surface
