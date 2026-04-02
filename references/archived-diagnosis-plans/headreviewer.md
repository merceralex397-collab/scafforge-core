> **ARCHIVED:** This document is superseded by the `recovery-plan/` directory.

# Head Reviewer Report For PR8

## Verdict

Request changes.

PR8 is directionally better than `main`. It materially improves generated-repo next-action routing, makes repair follow-on state more explicit, adds host-surface failure classification, and gives pivot a first-class contract surface.

It is not yet strong enough to merge as if the remediation is safely on track. The main reasons are:

1. the branch currently overclaims verification health
2. the greenfield proof gate is still not actually before handoff
3. repair and restart regeneration can still preserve stale `START-HERE.md` content
4. the repair stale-surface map claims escalation coverage that the public repair runner cannot currently emit

## Highest-Signal Findings

### 1. Verification health is currently overclaimed, and the package remains host-sensitive

Files and evidence:

- `scafforge-remediation-progress-review.md:35-47`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts:177-205`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts:226`
- `skills/scafforge-audit/scripts/audit_repo_process.py:3542-3567`
- `scripts/smoke_test_scafforge.py:768-833`

Observed locally on March 30, 2026:

- `python scripts/validate_scafforge_contract.py` passed
- `python scripts/smoke_test_scafforge.py` failed

The progress review says the smoke test passes and that `uv` is available on "this machine". That is not true in the current workspace run.

The branch still hardcodes POSIX-style `.venv/bin/...` execution paths across generated tools, audit detection, and smoke fixtures. On this Windows host, that combines with missing `uv` to produce the wrong failure family in the smoke suite and breaks the branch’s claim that verification is now fail-closed and trustworthy.

This is not just an environment quirk. It is a package-level review issue because Scafforge’s package repo explicitly claims to be host-agnostic in `AGENTS.md:9`.

### 2. The greenfield verifier is still sequenced after handoff generation in practice

Files:

- `scafforge-consolidated-remediation-plan.md:92`
- `scafforge-consolidated-remediation-plan.md:220-239`
- `skills/skill-flow-manifest.json:21-31`
- `scripts/validate_scafforge_contract.py:209-220`
- `skills/scaffold-kickoff/SKILL.md:92-123`

The consolidated plan says the kickoff-owned verification gate should run before handoff.

The implementation does not actually do that:

- the machine-readable greenfield sequence still ends with `handoff-brief`
- the validator locks that sequence in
- `scaffold-kickoff` still makes handoff step 8 and runs the verifier inside that step, before finishing it, not before entering it

Impact:

- restart surfaces can still be written before the package proves they are truthful
- this improves failure visibility, but it does not fully solve the "agents restart into a false-ready repo" problem

### 3. Repair and restart regeneration can silently preserve stale `START-HERE.md` managed content

Files:

- `skills/scafforge-repair/scripts/apply_repo_process_repair.py:84-96`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py:53-62`

Both `merge_start_here()` implementations return the existing content unchanged when the start marker exists but the end marker is missing.

I reproduced this directly. In that partial-marker state, the new managed block from the rendered output is discarded and the stale block survives unchanged.

Impact:

- repair is not yet reliably widespread across restart surfaces
- inaccurate or contradictory restart instructions can survive both repair and restart regeneration
- this directly conflicts with the remediation goal of making restart surfaces derived and truthful

### 4. The repair stale-surface map overclaims `human_decision` escalation coverage

Files:

- `skills/scafforge-repair/scripts/apply_repo_process_repair.py:287-379`
- `skills/scafforge-repair/scripts/run_managed_repair.py:286-294`
- `skills/scafforge-repair/SKILL.md:81`

`build_stale_surface_map()` exposes a `human_decision` category via `intent_decision_required`, but the public repair runner never passes that flag as `True`.

As shipped in this PR, the public repair flow cannot actually emit that category.

Impact:

- the repair report implies a capability that is not operational
- this weakens the trustworthiness of the stale-surface map
- it also increases concern around pivot, because intent-changing escalation is documented but not yet implemented as a reliable executable path

### 5. The remediation approach is still drifting toward text-coupled overengineering

Files:

- `skills/scafforge-audit/scripts/shared_verifier.py:222-264`
- `scripts/validate_scafforge_contract.py:34-66`
- `scripts/validate_scafforge_contract.py:209-220`

The direction of travel is correct, but the implementation is leaning heavily on literal snippet checks and fixed text ordering across docs and generated tools.

That buys short-term safety, but it is expensive and brittle:

- wording edits become contract failures even when behavior is still correct
- reviewers have to maintain prose and runtime surfaces in lockstep
- the package risks turning operator-safety work into governance-string maintenance

This is the strongest signal behind the concern that the project is becoming over-engineered.

## Assessment By Area

### Overall project approach

The high-level project goal is still sound: generated repos should expose one legal next move, and operator confusion should count as package failure evidence.

The current risk is not the goal. It is the implementation style. Too much of the contract is being enforced as synchronized prose and string snippets instead of smaller structural or executable invariants. That will slow future repairs and make the package harder to evolve safely.

### Overall PR approach

The PR improves the right areas:

- bootstrap-first routing is stronger
- closed-ticket dependent continuation is stronger
- explicit `ticket_reverify` and `ticket_reconcile` routing is stronger
- repair follow-on truthfulness is stronger
- host/tool mismatch classification is stronger

But the PR still does not fully rectify the "audited/repaired repo locks the agent" concern. It reduces several deadlock families without yet closing the bigger sequencing and host-execution gaps.

### Consolidated remediation plan

The consolidated plan is mostly the right correction to earlier drift:

- it is right to shrink audit
- it is right to avoid making audit the greenfield gate
- it is right to make repair bounded and fail-closed
- it is right to add pivot as its own lifecycle

The plan’s weakness is that it still leaves too much room for documentation-heavy enforcement. The implementation already shows that tendency. The plan should keep pushing toward structural and executable verification, not more cross-referenced wording rules.

## Concern Check

### 1. Audited/repaired repos getting locked

Partially addressed, not fully rectified.

The branch clearly improves this through:

- bootstrap-first routing
- dependent continuation routing
- explicit trust-restoration and reconciliation routing
- more truthful repair follow-on state

It does not fully solve it because:

- the greenfield gate is still not truly pre-handoff
- verification is still host-sensitive
- restart-surface regeneration still has the partial-marker bug

### 2. Project becoming over-engineered

Valid concern.

The current implementation is accumulating too much text-coupled validation. That is a maintainability risk and a likely source of future false positives and reviewer fatigue.

### 3. Bugs / bad coding in the PR

Valid concern.

The concrete code bug I would block on is the duplicated `merge_start_here()` behavior that silently preserves stale restart content when markers are partially broken.

The unreachable `human_decision` stale-surface category is also real, though less severe.

### 4. Repair not being widespread enough

Improved, but not fully solved.

The repair runner is more honest now, but the `START-HERE.md` merge bug proves cross-surface correction is still incomplete. More broadly, Scafforge still relies on later follow-on stages for prompts, skills, and team surfaces, so repair convergence is still partial by design.

### 5. Agents in generated repos getting confused about next action

Improved, but not fully solved.

The generated runtime surfaces are much better than before. The `workflow.ts` and `ticket_lookup.ts` changes are real improvements.

The remaining problem is that Scafforge still proves too much through surface agreement instead of path execution, and it still allows handoff generation before the proof gate is truly complete.

### 6. Pivot skill concerns

Valid concern.

The branch correctly establishes pivot as a first-class lifecycle, but `scafforge-remediation-progress-review.md:207-217` is also correct that pivot remains mostly contract-level. That means pivot is now named and bounded, but not yet operationally proven at the same standard as the stronger parts of repair and restart routing.

## PR Comment Triage

No inline file comments were present. The PR discussion consists of top-level comments, several of which are duplicates.

| Comment | Judgment | Notes |
| --- | --- | --- |
| `4156366801` Documentation Review | Mostly invalid / non-blocking | The docstring and inline-comment requests are low-value for this PR. The minor redundancy note is fair but trivial. |
| `4156370550` Performance Review | Invalid for decision-making | These are mostly micro-optimizations on validation, repair, or fixture code. Full directory replacement is intentional in deterministic repair. |
| `4156371943` Architecture Review | Partially valid | Dynamic import fragility and the size of `apply_repo_process_repair.py` are real maintainability concerns. The positive assessment of direction is also fair. |
| `4156377632` Test Coverage Review | Invalid for the current PR stage | The missing pivot integration/runtime coverage is already explicitly recorded as later-phase incomplete work in `scafforge-remediation-progress-review.md`. Under the staged-plan rule, these are not current PR blockers. |
| `4156382235` Code Correctness Review | Partially valid | The `merge_start_here()` bug is real. The rest did not hold up: I found no duplicate trailing import, the `non_clean_without_findings` complaint is a misread of intended exclusions, and the `replaced_surfaces` complaint does not actually break repair routing. |
| `4156393032` Security / Best Practices Review | Valid | No meaningful security defect surfaced. The symlink and dynamic-import notes are low-risk and reasonable. |
| `4156424190` Repair & Verification Contracts | Partially valid | Correct on dead `human_decision` wiring, dynamic import fragility, and current verification proving surface alignment more than runtime path execution. The criticism of `non_clean_without_findings` is mostly a naming/clarity concern, not a demonstrated logic bug. |
| `4156826498` Phase 4 & 5 Review | Partially valid | It is right that restart routing and host-surface classification improved materially. Its conclusion that there are no blocking issues is too generous. |
| `4156830618` Lifecycle Architecture & Shared Verifier Review | Partially valid | Correct on partial verifier extraction and the manifest omission. Incorrect in summarizing the gate as running before handoff; it does not. |
| `4156909189`, `4156910978`, `4156914503`, `4156920822` Phase 1 & 2 Reviews | Duplicate / low-signal | Treat these as one repeated partially valid comment. They add no new evidence beyond the better detailed Phase 1/2 comment. |
| `gemini-code-assist` bot review | Low-signal / not useful | "No feedback" is not credible enough to affect the review outcome. |

## Bottom Line

This PR is a meaningful improvement, but it is not ready to be treated as if the remediation is already on safe rails.

The right near-term actions before merge are:

1. fix `merge_start_here()` in both repair paths
2. stop overclaiming smoke/`uv` status in the progress review, and either make the smoke suite truthful on this host or document the platform assumption explicitly
3. make the greenfield proof gate a real pre-handoff step in the manifest, validator, and kickoff contract
4. either wire `human_decision` through the public repair path or stop claiming that category is currently emitted there

After that, continue the phased work on:

- reducing text-coupled contract enforcement
- deeper pivot runtime orchestration
- stronger executable verification instead of only surface alignment
