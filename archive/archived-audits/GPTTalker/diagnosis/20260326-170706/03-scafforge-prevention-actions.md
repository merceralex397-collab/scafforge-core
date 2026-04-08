# Report 3: Scafforge Prevention Actions

These actions describe package-side changes that prevent the same failures from reappearing in future generated repos.

- Teach audit to inspect the previous diagnosis and repair history, then force repair to explain why the prior cycle failed before another managed-repair run proceeds.

- Teach scafforge-audit and generated prompts to flag repeated lifecycle retries as contract thrash instead of ordinary transient error handling.

- Reject unsupported stage probing and explicit workflow bypass attempts in both generated tools and prompt hardening.

- Teach audit and generated coordinator prompts to treat coordinator-authored specialist artifacts as a workflow defect that requires prompt plus local-skill regeneration.

- Make `ticket_reverify` the legal trust-restoration path for closed done tickets instead of binding it to the normal closed-ticket lease rules.

- Use one lease-ownership model everywhere: the team leader claims and releases ticket leases, specialists work under the active lease, and only Wave 0 setup work may claim before bootstrap is ready.

- Make `/resume` trust canonical manifest plus workflow state first, keep all restart surfaces derived-only, include `.opencode/state/latest-handoff.md`, and preserve the active open ticket as the primary lane.

- Audit transcript tool errors directly, keep `_workflow_*` helpers out of the model-visible tool surface, and fail package verification when internal helper exports can be selected like executable tools.

- Refresh managed workflow docs, tools, and validators together so repair replaces drift instead of layering new semantics over old ones.

- Tighten generated review and QA guidance so runtime validation and test collection proof exist before closure.

- Detect and repair leftover placeholder local skills so generated stack guidance is concrete before implementation continues.

- Teach audit and repair to treat pending backlog process verification as a first-class verification state so repaired repos are not declared clean while historical done tickets remain untrusted.

