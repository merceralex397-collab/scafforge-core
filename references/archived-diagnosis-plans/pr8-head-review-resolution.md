> **ARCHIVED:** This document is superseded by the `recovery-plan/` directory.

# PR 8 Head Review Resolution

This document is the final review-resolution record for PR 8 on branch `codex/remediation-proof-repair-pivot`.

Scope:

- every PR review posted against commit `79ec4cf68093ce35a446115d9e71064a48dbb00a`
- the later top-level review comments derived from those reviews
- live verification against the current branch state rather than accepting review claims on trust

Evidence used for classification:

- `gh pr view 8 --json reviews,comments`
- local review artifacts:
  - `headreviewer.md`
  - `pr8_review.md`
  - `review.txt`
  - `.pr-review-agent5.md`
- current branch code
- current validation runs:
  - `python3 scripts/validate_scafforge_contract.py`
  - `python3 scripts/smoke_test_scafforge.py`
  - `python3 scripts/integration_test_scafforge.py`
  - `python3 scripts/validate_gpttalker_migration.py`

## Final Triage

### Accepted As True And Resolved

#### Smoke harness and shared test support

Grouped reviews:

- `Agent 4 Review: Smoke Test Harness`
- `Smoke Test Infrastructure Review`

Accepted findings:

- duplicate helper definitions in `scripts/smoke_test_scafforge.py`
- missing explicit Node.js prerequisite/version guard in the generated-tool harness
- GPTTalker fixture and integration expectations were too weak in places

Resolution:

- shared wrapper helpers now live in `scripts/test_support/repo_seeders.py`
- `scripts/test_support/scafforge_harness.py` now fail-closes on missing or too-old Node
- integration and migration checks now assert invariant-specific expected findings

Rejected or downgraded:

- the size of `scripts/smoke_test_scafforge.py` is a maintainability concern, but not a correctness defect after the current support-module split and passing suite
- host-conditional `uv` coverage is now explicit and truthful; on this host the `uv` path is exercised

#### Generated tool behavior

Grouped reviews:

- `Agent 7 Review — Generated Repo Tool Templates`
- `Generated Repo Template Review — PR #8`

Accepted findings:

- `ticket_reconcile.ts` incorrectly defaulted `remove_dependency_on_source` to true
- `ticket_reconcile.ts` could accept unrelated current-registry evidence
- shadowed `stderr` variables in generated execution tools were confusing and inconsistent

Resolution:

- `remove_dependency_on_source` now defaults to false unless explicitly true
- registry-backed evidence is now limited to the source, target, or replacement source ticket
- shadowed `stderr` variables were renamed
- smoke coverage now proves the corrected reconciliation behavior

Rejected or downgraded:

- `ticket_lookup` returning `noop` for a clean done-ticket case is not incorrect by itself because the restart surfaces and handoff tools already own the next-action continuation outside that closed-ticket state
- the supersede path setting `verification_state = "reverified"` is acceptable in the current contract because the tool is recording canonical reconciliation evidence at the moment of supersession

#### Contract validator and document/contract drift

Grouped reviews:

- `Agent 6 Review — Contract Validator`
- `Contract Validator Review`
- `Review: Skill Flow Manifest and Kickoff`
- `Agent 8 Review: skill-flow-manifest.json & Cross-Skill Boundary Consistency`

Accepted findings:

- missing or mismatched manifest mode declarations
- kickoff retrofit wording drift
- one-shot contract omitted the early bootstrap-lane verification step
- divergent ticket templates
- audit report output drift from the report-template contract
- several validator checks were overly brittle or incorrect in small but real ways

Resolution:

- manifest modes and flow-graph sanity are explicit and validator-enforced
- kickoff and one-shot docs now match the implemented lifecycle
- ticket templates are aligned
- diagnosis-report rendering matches the documented four-report template
- validator brittleness was reduced for the invalid regex-like absence check and the worst multiline literal checks

Rejected or downgraded:

- the validator’s overall size and high literal-check density are real maintenance concerns, but they are not unresolved correctness defects after the current alignment work

#### Audit, shared verifier, and diagnosis-pack behavior

Grouped reviews:

- `Agent 3 Review: Audit Skill Modularization`
- `Audit Modularization Review`
- `Review: Audit Skill and Diagnosis Pack`
- `Review: Shared Verifier Architecture`
- `Shared Verifier Architecture Review`

Accepted findings:

- diagnosis-report output originally missed required template sections
- review/diagnosis output needed tighter alignment with the report templates

Resolution:

- report output and diagnosis manifest result-state naming now match the report contract
- audit modularization landed across the major rule families and reporting

Rejected or downgraded:

- the claimed `.glob()` crash in `verify_greenfield_continuation` was false
- dynamic import coupling and helper duplication are legitimate maintenance tradeoffs, not unresolved runtime defects in the current branch
- calls for a fully data-driven rule catalog were architectural suggestions, not correctness blockers for PR 8

#### Repair lifecycle correctness

Grouped reviews:

- `Review: Repair & Verification Contracts`
- `Review: Repair Skill Public Contract`
- `Review: scafforge-repair major rewrite`
- later top-level repair review comments

Accepted findings:

- the public repair path previously overclaimed `human_decision` stale-surface routing
- follow-on stage recording could leave stale repair outcome and stale restart surfaces
- repair-side restart regeneration could erase pivot blockers
- repair docs needed to make the public completion path and execution record clearer

Resolution:

- `human_decision` was removed from the public repair path
- `record_repair_stage_completion.py` now recomputes repair-follow-on state, syncs the execution record, and republishes restart surfaces immediately
- repair-side restart regeneration now loads pivot state and preserves pivot follow-on truth
- repair docs now name the execution record and the pivot-aware restart constraint

Rejected or downgraded:

- `non_clean_without_findings` was not a demonstrated logic bug; the real issue was naming clarity and contract scope
- duplicate `merge_start_here()` implementations were a valid DRY concern earlier, but the active correctness bug was the partial-marker handling, which is already fixed

#### Pivot lifecycle correctness

Grouped reviews:

- `Agent 1 Review: scafforge-pivot Skill`
- `Pivot Skill Implementation Review — PR #8`
- later top-level pivot review comments

Accepted findings:

- pivot restart publication needed to remain truthful when repair rerendered surfaces
- repo-relative `--supporting-log` paths were resolved from the wrong root
- pivot lineage execution needed clearer skip reasons when runtime metadata was missing

Resolution:

- repair-side restart regeneration now preserves pivot state
- `plan_pivot.py` now resolves `--supporting-log` relative to the pivoted repo root and requires the file to exist
- pivot lineage execution now emits explicit skip reasons
- smoke coverage now proves repo-root supporting-log resolution and pivot-state preservation

Rejected or downgraded:

- “pivot is only contract-level” became outdated as the branch gained execution-backed pivot stage tracking, restart publication, and lineage execution

#### GPTTalker fixtures, integration, and migration validation

Grouped reviews:

- `Agent 10 Review — Test Fixtures, Integration Tests, and GPTTalker Validation`
- `Integration Test & Migration Validation Review`

Accepted findings:

- fixture builders and integration checks needed explicit expected finding-code assertions
- one fixture family was not seeding the right repo shape to reproduce its intended finding
- repeated-lifecycle contradiction fixtures were pinned to a fake package commit and could not trigger `CYCLE002`
- migration summary generation was using tempdir-backed paths after cleanup

Resolution:

- fixture metadata now includes `expected_finding_codes`
- integration uses those expectations and passes supporting logs through
- the relevant fixture builders and seeders were corrected
- migration summary generation now happens while the temp repo still exists

Rejected or downgraded:

- the earlier claim that GPTTalker migration proof was entirely missing is now outdated; the branch has real-subject migration validation and committed reports

### Rejected As False Or Outdated

#### False

- `verify_greenfield_continuation` crashing because `.opencode/agents/` is missing
- `audit_execution_surfaces.py` arithmetic on `"unknown"` test counts
- `build_stale_surface_map()` contradictions caused by `replaced_surfaces = []` in normal repair execution
- duplicate trailing `import sys` in `plan_pivot.py`

#### Outdated By Later Branch Work

- “greenfield verification still runs after handoff”
- “pivot has no runtime or integration proof”
- “host-sensitive `.venv` handling is still broken on this branch”
- “Phase 4/5 work leaves no blocking issues” as a final review verdict

## Final Merge Judgment

After verifying the reviews against the current branch, the final judgment is:

- valid correctness findings were implemented
- false findings were rejected
- advisory-only maintainability comments were separated from merge-blocking defects
- current code, docs, and verification now agree

PR 8 satisfies the remediation plan and is merge-ready.
