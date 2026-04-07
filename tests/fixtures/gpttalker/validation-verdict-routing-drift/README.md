# Validation Verdict Routing Drift

This family captures greenfield repos where review or QA verdicts were not routed back to implementation and markdown-emphasized verdicts became ambiguous.

Archive origin:

- synthetic greenfield validation drift

What mattered:

- explicit FAIL verdicts had to route back to implementation
- markdown-emphasized verdict labels could not confuse the parser
- weaker models needed a clear blocker path after validation failed

Current protection:

- ticket_lookup routes FAIL review and QA back to implementation
- verdict extraction stays consistent enough for the gate contract
- the fixture injects a FAIL review artifact so the audit still sees routing drift
