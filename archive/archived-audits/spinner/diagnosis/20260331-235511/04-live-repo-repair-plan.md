# Live Repo Repair Plan

## Preconditions

- Repo: /home/rowan/spinner
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Package Changes Required First

- None recorded.

## Post-Update Repair Actions

- Route 2 workflow-layer finding(s) into `scafforge-repair` for deterministic managed-surface refresh.

- After deterministic repair, rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

### REMED-001

- linked_report_id: WFLOW012
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Adopt one lease model everywhere: the team leader owns `ticket_claim` and `ticket_release`, specialists work only inside the already-active ticket lease, and only Wave 0 setup work may claim before bootstrap is ready.

### REMED-002

- linked_report_id: WFLOW010
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Keep manifest.active_ticket and workflow.active_ticket synchronized through ticket_update activate calls. EnsureWriteLease should accept an optional target-ticket parameter so artifact tools can validate against the correct ticket instead of the workflow-level active ticket.

## Ticket Follow-Up

- No subject-repo ticket follow-up was recommended from the current diagnosis run.

## Reverification Plan

- After package-side fixes land, run one fresh audit on the subject repo before applying another repair cycle.
- After managed repair, rerun the public repair verifier and confirm restart surfaces, ticket routing, and any historical trust restoration paths match the current canonical state.
- Do not treat restart prose alone as proof; the canonical manifest and workflow state remain the source of truth.

