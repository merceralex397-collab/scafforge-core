# Durable Adoption Policy

The product does not ship with a hardcoded durable repo list.

## Durable admission criteria

A repo is a durable candidate when most of the following are true:

- it is meant to be kept beyond a short experiment
- it has a meaningful project identity or stakeholder
- it needs ongoing repair, review, or historical traceability
- it should remain visible in the control plane by default
- archival and research value outweigh cleanup pressure

## Adoption rule

Current machine-local repos may be adopted as durable when they meet the criteria above and an operator approves the adoption.

That approval captures:

- repo id and human name
- inventory origin as `adopted`
- initial lifecycle state
- current host bindings
- initial autonomy level

## Non-goal

Machine-local adoption candidates are not product defaults. They are operator-managed inventory state.
