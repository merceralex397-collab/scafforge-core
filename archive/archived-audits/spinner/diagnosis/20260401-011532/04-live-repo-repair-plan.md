# Live Repo Repair Plan

## Preconditions

- Repo: /home/rowan/spinner
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Package Changes Required First

- None recorded.

## Post-Update Repair Actions

- No safe managed-surface repair was identified from the current findings.

## Ticket Follow-Up

- No subject-repo ticket follow-up was recommended from the current diagnosis run.

## Reverification Plan

- After package-side fixes land, run one fresh audit on the subject repo before applying another repair cycle.
- After managed repair, rerun the public repair verifier and confirm restart surfaces, ticket routing, and any historical trust restoration paths match the current canonical state.
- Do not treat restart prose alone as proof; the canonical manifest and workflow state remain the source of truth.

