# Repeated Lifecycle Contradiction

This family captures the GPTTalker churn pattern where the legal next move existed in theory but repair, restart surfaces, and ticket tooling disagreed about what the agent could actually do.

Archive origin:

- `scafforgechurnissue/plan.md`
- `scafforgechurnissue/GPTTalkerAgentLogs/session4.md`

What mattered:

- repair could not claim convergence while required follow-on work still existed
- restart surfaces had to stay aligned with the recorded repair follow-on state
- repeat audit churn was evidence of package contradiction, not operator confusion

Current protection:

- repair follow-on state is persistent, evidence-backed, and machine-readable
- canonical completion artifacts can auto-close the bounded follow-on stage catalog
- the repair integration test proves full-stage convergence through canonical evidence
