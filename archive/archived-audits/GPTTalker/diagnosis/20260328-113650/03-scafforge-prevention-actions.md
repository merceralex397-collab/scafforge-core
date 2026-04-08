# Report 3: Scafforge Prevention Actions

These actions describe package-side changes that prevent the same failures from reappearing in future generated repos.

- Teach scafforge-audit and generated prompts to flag repeated lifecycle retries as contract thrash instead of ordinary transient error handling.

- Detect and block evidence-free PASS artifacts when verification could not run, and keep smoke-test proof tool-owned.

- Teach audit and generated coordinator prompts to treat coordinator-authored specialist artifacts as a workflow defect that requires prompt plus local-skill regeneration.

- Treat operator confusion itself as workflow evidence when the transcript shows no single legal next move, and audit adjacent surfaces together until one competent route exists.

- Give historical reconciliation one legal evidence-backed path so superseded invalidated tickets can be repaired without depending on impossible direct-artifact or closeout assumptions.

