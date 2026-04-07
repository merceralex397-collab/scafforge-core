# Planning and Implementation Contract Drift

This family captures greenfield repos where the plan-review gate or implementation routing drifted back into status inference.

Archive origin:

- synthetic greenfield contract drift

What mattered:

- plan_review stayed explicit
- implementation could not be keyed off ticket.status
- weaker models needed one legal next move, not a fuzzy stage label

Current protection:

- ticket_update and stage-gate-enforcer keep plan_review and implementation routing explicit
- greenfield continuation still happens through the existing bootstrap-lane and handoff gates
- the fixture intentionally injects contract drift so the audit still catches it
