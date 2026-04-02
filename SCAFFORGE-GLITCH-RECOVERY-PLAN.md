# Scafforge Bulletproofing Plan

> **SUPERSEDED:** This document has been replaced by the comprehensive phased plan in [`recovery-plan/`](recovery-plan/00-PLAN-INDEX.md). The new plan covers all issues identified here plus universal stack support, code quality feedback loops, stack-aware audit, and a multi-stack proof program. This file is preserved for historical context only.

## Ultimate Aim

The ultimate aim is not merely to repair `livetesting/glitch`.

The real objective is to make Scafforge robust enough that a weaker AI can operate safely inside a generated repo for any supported project class without getting trapped between contradictory workflow surfaces, missing stack guidance, or shallow validation.

Glitch remains the current proof target because it exposed real failures, but it is not the only target. The package must converge on a stronger guarantee:

1. generation leaves one legal next move,
2. audit finds the real root cause instead of only the visible symptom,
3. repair restores truthful managed surfaces before asking generated agents to continue,
4. stack-specific repos are not declared healthy on generic workflow checks alone.

## Evidence Base

This plan is based on verified current package and proof-target evidence from:

- `README.md`
- `references/competence-contract.md`
- `references/one-shot-generation-contract.md`
- `skills/scaffold-kickoff/SKILL.md`
- `skills/repo-scaffold-factory/SKILL.md`
- `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`
- `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`
- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-audit/scripts/shared_verifier.py`
- `skills/scafforge-audit/scripts/audit_contract_surfaces.py`
- `skills/scafforge-audit/scripts/audit_lifecycle_contracts.py`
- `skills/scafforge-audit/scripts/audit_restart_surfaces.py`
- `skills/scafforge-audit/scripts/audit_session_transcripts.py`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-repair/SKILL.md`
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- `skills/project-skill-bootstrap/SKILL.md`
- `skills/opencode-team-bootstrap/SKILL.md`
- `skills/agent-prompt-engineering/SKILL.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/SKILL.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/ticket-execution/SKILL.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/context_snapshot.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_claim.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `glitchresearch.md`
- `livetesting/glitch/glitchblock1.md`
- `livetesting/glitch/diagnosis/20260401-215051/`
- `livetesting/glitch/.opencode/skills/stack-standards/SKILL.md`
- `livetesting/glitch/.opencode/skills/godot-architecture/SKILL.md`

## Verified Scafforge Reality

### 1. How Scafforge currently generates repos

Verified behavior:

- `repo-scaffold-factory` performs deterministic render by copying the generic project template and substituting placeholders.
- The stack-specific operating layer is then largely produced by agent-driven follow-on work in `project-skill-bootstrap`, `opencode-team-bootstrap`, and `agent-prompt-engineering`.
- The greenfield proof gates in `verify_generated_scaffold.py` and `shared_verifier.py` mainly prove continuation-contract consistency, bootstrap routing, active-ticket alignment, and placeholder-skill removal.

What this means:

- Scafforge is strong at generating a generic workflow skeleton.
- Scafforge is weaker at proving that the generated repo is actually valid for a non-trivial stack unless later specialization gets it right.

### 2. What a weaker AI is expected to do in the generated repo

The package expects a weaker model to:

- resume from `tickets/manifest.json` plus `.opencode/state/workflow-state.json`,
- rely on repo-local skills rather than reconstructing conventions from scratch,
- route ticket movement through `ticket_lookup.transition_guidance` and `ticket_update`,
- stop on contradictions instead of exploring workaround transitions,
- trust restart surfaces only as derived summaries.

This expectation is explicit in:

- `references/competence-contract.md`
- `skills/agent-prompt-engineering/SKILL.md`
- `skills/project-skill-bootstrap/SKILL.md`
- `skills/opencode-team-bootstrap/SKILL.md`

Therefore the package bar is high: if the generated repo leaves a weaker model unsure how to proceed, that is a package defect.

### 3. What is already strong

The current package is not empty or naive. It already contains meaningful hardening:

- a clear competence contract centered on one legal next move,
- explicit weak-model-first wording across kickoff, prompt engineering, skill bootstrap, and audit,
- generic greenfield continuation verification in `shared_verifier.py`,
- broad workflow-layer audit families for restart surfaces, lifecycle contracts, transcript chronology, ticket graph contradictions, and repair-cycle churn,
- deterministic managed-surface replacement and restart regeneration in repair.

This matters because the plan should not pretend Scafforge has no defenses. The issue is uneven coverage, cross-stack gaps, and incorrect routing of some already-detected failures.

### 4. Where it is not bulletproof yet

The current package is still not robust enough for arbitrary project classes because:

1. stack-specific correctness is not proven by the generic scaffold verification gates,
2. the deepest execution-surface diagnosis is Python-centric,
3. some workflow-tool contradictions still exist in the template,
4. audit reporting can still route package defects as if subject-repo repair were the next step,
5. repair replacement is deterministic but not yet safety-rich enough for broad managed overwrite scenarios,
6. the generated repo can still look structurally complete while being inert at runtime.

## Factual Answer To The "Python-Only Audit" Question

The exact statement "audit only addresses Python code issues" is not accurate.

What is true:

- audit is not only a Python linter or Python code checker,
- audit already diagnoses generic workflow, restart, transcript, ticket-graph, and repair-cycle defects across repos,
- audit also inspects transcript evidence for commands such as `cargo test`, `go test`, `npm run test`, `pnpm run test`, `yarn test`, and `bun run test`.

What is also true, and important:

- the only deep execution-surface code path I found is `audit_python_execution()` in `skills/scafforge-audit/scripts/audit_execution_surfaces.py`,
- I did not find equivalent built-in `audit_godot_execution`, `audit_node_execution`, `audit_rust_execution`, or `audit_go_execution` passes,
- I did not find Godot-aware logic in `verify_generated_scaffold.py` or `shared_verifier.py`,
- I did not find package-level Godot scene/autoload/runtime validation logic in the current audit scripts.

Accurate conclusion:

- Scafforge audit is workflow-generic and transcript-aware.
- Scafforge execution-depth is currently Python-centric.
- For the package to become bulletproof across arbitrary project types, audit needs a stack-adapter or execution-adapter layer instead of relying on Python-specific depth plus generic workflow checks.

## Proof Surfaces

The following are direct proofs that shape this plan:

1. `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`
   Proof: deterministic render copies a generic template and substitutes placeholders; it does not prove stack-specific correctness.

2. `skills/scafforge-audit/scripts/shared_verifier.py`
   Proof: greenfield verification checks bootstrap lane, active-ticket alignment, restart-surface agreement, and placeholder local skills. No Godot-specific or stack-specific viability checks were found.

3. `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/SKILL.md`
   Proof: the baseline generated stack skill is intentionally generic and explicitly says it must be replaced later.

4. `skills/project-skill-bootstrap/SKILL.md`
   Proof: stack-specific skill correctness is delegated to agent-driven synthesis after scaffold render.

5. `skills/opencode-team-bootstrap/SKILL.md`
   Proof: project-specific agent/team correctness is also agent-driven, not purely deterministic.

6. `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
   Proof: contains one deep execution pass, `audit_python_execution()`, plus generic execution-contract checks.

7. `skills/scafforge-audit/scripts/audit_restart_surfaces.py`, `audit_lifecycle_contracts.py`, and `audit_session_transcripts.py`
   Proof: Scafforge already has significant weak-model workflow diagnosis coverage that must be preserved and extended, not rediscovered from zero.

8. `skills/scafforge-audit/scripts/audit_reporting.py`
   Proof: current routing marks most non-`EXEC` and non-`ENV` findings as `scafforge-repair` rather than forcing package-first handling, which is too weak for upstream template defects.

9. `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
   Proof: deterministic replacement uses `shutil.rmtree(target)` plus `shutil.copytree(source, target)` for managed directories, with no backup or human-readable diff surface in the normal flow.

10. `livetesting/glitch/.opencode/skills/godot-architecture/SKILL.md` and `livetesting/glitch/.opencode/skills/stack-standards/SKILL.md`
    Proof: Glitch did receive project-specific Godot operating guidance, which means Scafforge can synthesize stack guidance, but current package proof gates do not verify that such guidance is actually sufficient.

## Broad Scafforge Issue Matrix

| ID | Area | Issue | Validation | Proof | Current Handling | Action |
| --- | --- | --- | --- | --- | --- | --- |
| ARCH-01 | Generation | Greenfield proof gates validate continuation contract, not stack viability | Validated | `verify_generated_scaffold.py` and `shared_verifier.py` contain no Godot-aware or stack-aware validation logic | Generic continuation proof only | Add stack-aware post-render proof adapters |
| ARCH-02 | Generation | Stack-specific repo guidance depends on agent synthesis, not deterministic package proof | Validated | Template `stack-standards` is generic; `project-skill-bootstrap` rewrites later | Placeholder removal checked, correctness not checked | Add stack-aware skill-quality verification |
| ARCH-03 | Generation | No built-in package-level Godot adapter/validator was found | Validated | No Godot logic found in package verifier or audit code | Relies on project-local synthesized skills only | Add adapter or validation family for Godot-like repos |
| WF-01 | Workflow tools | Lease-path guidance is too thin for weaker models | Validated | `ticket_claim.ts` and team-leader guidance remain under-specified | Partly covered by audit WFLOW012 family | Fix template guidance now |
| WF-02 | Workflow tools | Review transition guidance is artifact-presence driven, not verdict-aware | Validated | `ticket_lookup.ts` review case still advances on current review artifact existence | Not directly detected by current audit as verdict-blind logic | Fix template and add audit coverage |
| WF-03 | Workflow tools | QA transition guidance is evidence-presence driven, not verdict-aware | Validated | `ticket_lookup.ts` QA case uses `validateQaArtifactEvidence()` without PASS/FAIL semantics | Not directly detected as verdict-blind guidance | Fix template and add audit coverage |
| WF-04 | Workflow tools | Recovery path after failed review or QA is not sufficiently truthful | Validated | Combined behavior across `ticket_lookup.ts`, `ticket_update.ts`, and `stage-gate-enforcer.ts` still exposed the Glitch trap | Partial transcript coverage exists; contract still weak | Define explicit fail-state routing |
| WF-05 | Workflow tools | `smoke_test.ts` still has quote-tokenization bug and weak failure classification | Validated | Current template still drops quotes and only classifies `command_error` generically | Audit already covers override failures in some cases | Fix tool and classify syntax/config failures better |
| WF-06 | Workflow tools | `ticket_lookup.ts` can present split active-ticket truth | Validated | Current lookup still rewrites workflow context for requested ticket lookups | Audit covers manifest/workflow drift, not this contextual response split fully | Reconcile to one canonical active-ticket view |
| WF-07 | Workflow tools | `handoff_publish.ts` and `context_snapshot.ts` return path-only acknowledgements | Validated | Current outputs do not include verification metadata | Audit does not currently target this exact output weakness | Add verification metadata and audit checks |
| WF-08 | Workflow library | `saveWorkflowBundle()` is sequential and non-transactional | Validated design risk | Current workflow save path writes sequentially with no rollback | Not proven as Glitch root cause | Lower-priority hardening |
| AUD-01 | Audit | Audit already has strong workflow and transcript diagnosis coverage | Validated existing strength | Restart, lifecycle, transcript, ticket-graph, and repair-cycle modules are real and broad | Existing capability | Preserve and extend |
| AUD-02 | Audit | Audit reporting routes many package defects too weakly | Validated | `audit_reporting.py` sends most `WFLOW*` findings to `scafforge-repair` instead of package-first stop state | Current routing can understate package-first work | Tighten `package_work_required_first` semantics |
| AUD-03 | Audit | Deep execution validation is Python-centric | Validated | `audit_python_execution()` exists; no equivalent Godot/Node/Rust/Go execution auditors found | Generic workflow diagnosis plus Python execution depth | Add stack-adapter execution audits |
| AUD-04 | Audit | No stack-aware inert-runtime graph checks for Godot-like repos | Validated | No current audit code found for `project.godot`, `.tscn`, autoload, or scene-tree entry checks | Static workflow diagnosis only | Add Godot-like runtime graph heuristics |
| AUD-05 | Audit | Existing audit already covers WFLOW006, WFLOW011, WFLOW012, WFLOW013, WFLOW016, WFLOW017, WFLOW022, transcript thrash, and active-ticket drift families | Validated existing strength | Current audit scripts already encode these rules | Existing capability | Preserve, do not duplicate |
| REP-01 | Repair | Managed replacement is deterministic but destructive by default | Validated | `replace_directory()` uses `rmtree` plus `copytree`; no normal backup/diff/confirmation surface found | Provenance recorded, but overwrite ergonomics are thin | Add backup/diff/preservation strategy |
| REP-02 | Repair | Repair boundary for repo-specific code needs stronger stack-aware guidance | Validated | Repair docs say route source-layer bugs to ticketing, but stack-specific conditions are still shallow | Boundary exists conceptually | Tighten boundary and ticket emission rules |
| REP-03 | Repair | Post-repair verification lacks non-Python stack adapters | Validated | Repair reuses audit depth; audit depth is currently Python-centric | Generic verification only for many stacks | Add stack-aware repair verification hooks |
| MODEL-01 | Weak-model support | The package promise to weaker models is stronger than current cross-stack proof | Validated | Competence contract promises one legal next move; generation proof does not yet prove stack viability | Promise exists, proof incomplete | Expand proof program across stacks |

## Re-Examined `glitchresearch.md` Matrix

This matrix re-checks the report claims and recommendations against the current package state.

| Claim Or Recommendation | Status | Verified Position |
| --- | --- | --- |
| Lane-lease scoping blocker | Validated | Real current package issue; keep in plan |
| Duplicate autoload singletons in current Glitch repo | Historical, not current | Good preventive target, not a current-state blocker |
| Smoke-test brittleness | Validated | Real current package issue |
| `verification_state` semantics gap | Partial | Real semantics concern, not yet proven as a root blocker |
| Transition guidance / verdict mismatch | Validated | Real current package issue |
| Handoff tool verification gaps | Validated | Real current package issue |
| Active ticket split-brain | Validated | Real current package issue |
| Audit is Python-only | Partially valid after correction | Not true as stated; accurate statement is workflow-generic but execution-depth Python-centric |
| Add Godot scene validation to scaffold chain | Validated gap | No package-level Godot-aware proof layer found; add to plan |
| Fix `ticket_update` lease ownership check | Reframed | Lease enforcement already exists in `stage-gate-enforcer.ts`; the real issues are guidance quality, active-ticket targeting, and contradiction handling |
| Fix superseded implementation -> review invalidation | Partial | Artifact trust-state machinery exists; verdict-aware and cross-stage invalidation still need deeper targeted validation before exact fix shape is chosen |
| Add structured review verdict field | Validated direction | Current workflow lacks strong machine-readable verdict semantics; this is a good fix direction |
| Enhance agent prompts with heuristics | Validated and partly already present | Weak-model hardening exists in package docs, but implementation is uneven and needs better proof |
| Add command linting to smoke_test | Validated as useful follow-on | Current failure classification is too coarse |
| Add lease transfer tool | Not yet proven as necessary root fix | Could help ergonomics, but not needed before fixing contract contradictions |
| Create Godot version-locked templates | Not yet proven as the only right fix | The real verified need is stack adapters and stack-aware proof; version-locked templates are one possible design |
| Add GDScript anti-pattern linter | Not yet proven as immediate root fix | Useful candidate under a Godot adapter, but not yet the first blocker |
| Implement `ticket_progress` combined tool | Not yet proven as immediate root fix | Could reduce thrash, but the primary defect is contradictory contract logic |
| Managed overwrite risk exists | Partially validated | Real improvement area; deterministic replacement currently lacks backup/diff ergonomics |

## Existing Audit Coverage To Preserve

The revised plan must not accidentally throw away coverage that already exists.

Current audit already covers or partially covers:

- weak-model workflow thrash and repeated lifecycle retries,
- unsupported stage probing and bypass-seeking in transcripts,
- bootstrap-first routing drift,
- lease-ownership drift,
- resume truth-hierarchy drift,
- team-leader and ticket-execution underspecification,
- smoke-test override failure in transcript evidence,
- acceptance-command drift in transcript evidence,
- closeout handoff lease contradiction,
- active-ticket drift between manifest and workflow state,
- repeated audit/repair cycle churn,
- placeholder local skill leftovers.

The plan should therefore extend audit in the missing areas, not restart audit design from zero.

## What Must Change To Make Scafforge More Bulletproof

### Phase 1: Clarify Package Promise Versus Package Proof

Primary goal:

- bring the implementation up to the same level as the competence contract.

Required work:

1. Add a package-level stack-adapter concept or equivalent verification registry.
2. Distinguish generic workflow proof from stack-specific viability proof.
3. Update the root package docs to state what is currently proven generically versus what requires stack-aware verification.

Primary files:

- `README.md`
- `references/competence-contract.md`
- `references/one-shot-generation-contract.md`
- `skills/scaffold-kickoff/SKILL.md`
- `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`
- `skills/scafforge-audit/scripts/shared_verifier.py`

### Phase 2: Harden Generated Workflow Surfaces

Required work:

1. Make review and QA guidance verdict-aware.
2. Prevent forward motion on failed review or QA verdicts.
3. Define one explicit remediation path after failed validation.
4. Fix quote tokenization and improve smoke-test failure classification.
5. Remove contextual active-ticket split-brain.
6. Add strong lease-path guidance.
7. Return verification metadata from handoff and context tools.

Primary files:

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_claim.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/context_snapshot.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`

### Phase 3: Add Stack-Aware Greenfield Proof

Required work:

1. Add stack-adapter verification hooks after scaffold generation and before handoff.
2. Start with a Godot adapter because Glitch already proves the need.
3. Prove not only that local skills are non-placeholder, but that required stack-specific invariants are covered.

Godot proof targets:

- `project.godot` parses and aligns with scene references,
- autoload boundaries are not duplicated in scene files,
- basic scene files are syntactically consistent,
- the generated repo exposes a valid first-run validation command family,
- critical runtime entry surfaces are named explicitly in repo-local skills.

Primary files:

- `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`
- `skills/scafforge-audit/scripts/shared_verifier.py`
- future adapter-specific verifier modules under Scafforge package control

### Phase 4: Expand Audit Beyond Python-Centric Execution Depth

Required work:

1. Keep the existing workflow/restart/transcript modules intact.
2. Add stack-adapter execution audits beyond Python.
3. Add a Godot-aware inert-runtime check family for:
   - initializer defined but uninvoked
   - manager scene defined but not instantiated
   - signal emitted with no reachable consumer
   - consumer expects runtime provider that never enters the tree
4. Tighten reporting so upstream template defects set `package_work_required_first` rather than defaulting to subject-repo repair.

Primary files:

- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-audit/scripts/audit_repo_process.py`
- future adapter-specific audit modules

### Phase 5: Make Repair Safer And More Stack-Aware

Required work:

1. Keep deterministic managed-surface refresh.
2. Add backup and diff visibility for replaced managed surfaces.
3. Preserve the current boundary where repo-specific code is not silently rewritten by default.
4. Make repair emit precise remediation tickets for remaining repo-code work after managed-surface repair.
5. Use stack-aware post-repair verification rather than generic workflow verification alone.

Primary files:

- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- `skills/scafforge-repair/scripts/record_repair_stage_completion.py`

### Phase 6: Proof Program Across Project Types

Scafforge is not bulletproof when only one live proof target exists.

Required proof set:

1. minimal Python repo
2. minimal Node repo
3. minimal Rust repo
4. minimal Go repo
5. Godot proof repo, using Glitch first

Each proof target should verify:

1. generation reaches immediate continuation,
2. repo-local skills are stack-correct enough for weaker models,
3. audit identifies real workflow and stack failures,
4. repair restores managed truth without hiding repo-local defects,
5. one legal next move remains after repair.

## Immediate Implementation Priorities

Priority 0:

1. Fix verdict-blind transition guidance in the template.
2. Fix the failed-review and failed-QA lifecycle trap.
3. Fix smoke-test quote handling and improve error classification.
4. Fix audit reporting so package defects become package-first work.

Priority 1:

1. Add stack-aware proof hooks to greenfield verification.
2. Add a Godot-aware audit adapter for Glitch-class repos.
3. Add safer managed-surface replacement ergonomics in repair.

Priority 2:

1. Expand adapter-based execution auditing to more stacks.
2. Decide whether version-locked templates, stack modules, or hybrid adapters are the best long-term structure.
3. Revisit lower-priority improvements such as `ticket_progress`, lease transfer, and workflow save atomicity.

## Glitch's Role In This Plan

Glitch is still essential, but as a proof repo.

The package should use Glitch to verify that:

1. audit no longer recommends forward progress from failed QA or review proof,
2. audit no longer undercalls package-first work,
3. repair restores corrected managed surfaces,
4. the remaining Glitch runtime defects are emitted as truthful remediation work rather than hidden by generic workflow success,
5. a weaker model can resume from the repaired repo with one legal next move.

## Definition Of Done

This work is not done until all of the following are true:

1. the package contract and the package proof gates are aligned,
2. audit is workflow-generic and no longer Python-centric for deep execution coverage,
3. generated repos for stack-specific projects are not handed off on generic continuation proof alone,
4. `package_work_required_first` becomes true whenever the root cause lives in Scafforge-managed surfaces,
5. repair restores managed surfaces safely and truthfully,
6. Glitch can be re-audited and repaired under the corrected package without recreating the original contradiction,
7. Scafforge demonstrates the same safety pattern on more than one project type.