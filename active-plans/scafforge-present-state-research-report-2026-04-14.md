# Scafforge present-state research report

## Executive Summary

Scafforge is a host-side skill bundle for generating, auditing, repairing, and handing off OpenCode-shaped repositories; its architecture is coherent on paper, with a clear package-vs-output boundary, a single public scaffold entrypoint, and a generated runtime centered on ticket state, provenance, and a stage-gate plugin.[^1][^2]

The repo is **not presently release-green**. At current `HEAD`, `npm run validate:contract` passes, but `npm run validate:smoke` fails in the smoke harness’s explicit-missing-executable scenario; a live reproduction shows the generated `smoke_test.ts` tool returning `failure_classification: "environment"` while dropping the more specific `host_surface_classification: "missing_executable"` signal because the underlying command comes back as `Error: spawn EIO`, `missing_executable: null`, and `failure_classification: "test_failure"`.[^3][^4][^5]

The most important non-regression problems are **workflow/documentation drift and operational hygiene**. The package docs still describe package-root `tickets/manifest.json` / `tickets/BOARD.md` / `IMPLEMENTATION-HANDOFF.md` as if they are the active package backlog surfaces, but the repo root currently has no `tickets/` directory and the handoff file now lives under archived/reference paths; this is exactly the kind of “operator must infer the real next move” situation the competence contract says should count as package evidence.[^6][^7]

The repo also relies too heavily on **manual validation narratives** rather than continuously enforced validation. The package defines canonical validation commands, but the repo has no checked-in workflow files for running them automatically; the GitHub metadata visible remotely is limited to dynamic Copilot/CodeQL workflows, the GitHub issue tracker is empty, and the package’s own validation log still records “green again” narratives immediately before today’s smoke failure.[^8][^9]

Finally, Scafforge’s own working notes show that some debt is still open: the `project-skill-bootstrap` ↔ `opencode-team-bootstrap` seam remains accepted temporary debt, `asserted_completed_stages` revalidation is still open, managed-blocked backward routing is still open, and broader Godot/product validation remains an active blocker theme. Those are not as urgent as the smoke regression, but they are still real present-state risks.[^10]

## What Scafforge is and how it functions

Scafforge is explicitly **not** a generated project; it is the package that creates and manages generated project operating frameworks. The repo’s own docs define three layers: the host agent, the Scafforge package (`skills/`, `scripts/`, `references/`, tests, plans), and the generated repo output (`.opencode/`, `tickets/`, `docs/spec/`, provenance, restart surfaces), with the downstream OpenCode agent operating inside the generated repo.[^1][^2]

At runtime, the package revolves around a deterministic orchestration chain. `scaffold-kickoff` is the single public entrypoint, and the skill-flow manifest maps greenfield, retrofit, managed-repair, pivot, and diagnosis/review flows to a bounded skill sequence that always ends in `handoff-brief`.[^2] In generated repos, the most critical moving parts are the workflow state machine (`workflow.ts`), the generated ticket surfaces, and the stage-gate enforcer plugin that runs before every tool call; the architecture doc correctly notes that if the stage-gate has a bug, all downstream tool calls can fail.[^2][^18]

That design is stronger than the repo’s older failure history might suggest. The current repair engine records diff summaries, takes backups before replacing managed surfaces, can preserve those backups, and restores from backup if managed-surface replacement fails; likewise, several earlier critical bugs in managed-blocked enforcement, provenance round-tripping, and copytree behavior are now explicitly recorded as fixed in the repo’s own bug register.[^11][^12]

## Current-state evidence snapshot

| Area | Intended state | Current evidence | Assessment |
|---|---|---|---|
| Package validation | Canonical validators should be green before release claims | Contract validation passes, but smoke validation currently fails on explicit missing-executable classification.[^3] | **Broken now** |
| Smoke tool behavior | Missing explicit executables should classify as environment + missing_executable host-surface failure | Live repro returns `host_surface_classification: null`, `missing_executable: null`, and artifact stderr `Error: spawn EIO`.[^4][^5] | **Broken now** |
| Package backlog truth | Docs say package work should start from root `tickets/manifest.json`, `tickets/BOARD.md`, and ticket markdowns | Root currently has no `tickets/` directory, and `IMPLEMENTATION-HANDOFF.md` is archived/reference-side rather than at the root.[^6] | **Drifted** |
| Regression control | Green claims should be backed by continuously enforced validation | Repo defines manual validation commands but has no checked-in workflow files for running them automatically; dynamic remote workflows are not a substitute for repo-local release validation.[^8] | **Weak** |
| Operational evidence | Planning evidence should stay discoverable and low-noise | `active-plans` was already flagged internally as cluttered, and the current log count has climbed to 338 files.[^13] | **Noisy** |
| Remaining debt | Open debt should be limited and well-contained | The repo still tracks open RC-003, RC-006, broader Godot/product validation blocker BLK-005, and accepted contract smell CYCLE001.[^10] | **Known unresolved risk** |

## Detailed issues and failings

### 1. Critical regression: the smoke harness is red at `HEAD`

This is the highest-confidence present-state failure. The smoke harness explicitly seeds a missing executable override (`definitely-missing-phase5-command`) and expects the generated `smoke_test.ts` tool to report an environment-level failure with `host_surface_classification == "missing_executable"`. Today, that assertion fails, which means the package’s canonical smoke gate is red right now.[^3]

The code path explains why. `runCommand()` only populates `missing_executable` when the child-process error surfaces as `ENOENT`, exit code `127`, or matching stderr text; `classifyHostSurfaceFailure()` only returns `"missing_executable"` when that field is populated or when `failure_classification` is already `"missing_executable"`.[^5] In today’s live repro, the missing command instead produces `stderr = "Error: spawn EIO"`, so the tool reports an environment failure at the top level, but the command-level record falls back to `failure_classification: "test_failure"` with `missing_executable: null`, and the host-surface classification is lost.[^4]

That matters beyond a single assertion. The smoke tool is used to separate **host/environment failure** from **ticket regression**. If it cannot reliably identify a missing executable, generated repos will produce weaker diagnostics, weaker repair routing, and potentially misleading QA/smoke artifacts even when the outer failure bucket still says “environment.”[^5]

The regression is also especially concerning because the repo’s own recent validation log says the smoke suite was green again for multiple working-tree changes on 2026-04-13, and the latest commit message at `HEAD` says all four validation gates passed. Either the regression landed immediately after those claims, or the smoke suite has host-sensitive behavior that the current validation story does not control tightly enough.[^9]

### 2. Package-root truth surfaces are out of sync with the repo’s actual layout

The repo’s governance docs currently send conflicting signals. `AGENTS.md` says that package work in this repo should start from `tickets/manifest.json`, `tickets/BOARD.md`, and ticket markdown files, and that `IMPLEMENTATION-HANDOFF.md` remains the historical transition guide for the completed implementation sequence.[^6] But the root layout no longer contains a `tickets/` directory, while the handoff file exists only under archived/reference paths, and the README now describes `active-plans/` and `active-audits/` as the live package-analysis surfaces.[^6]

This is more than cosmetic drift. The competence contract defines Scafforge as incompetent whenever the workflow does not expose one clear legal next move, one named owner, and one blocker path, and it explicitly says that operator confusion is package evidence when the next move is ambiguous or too expensive to infer.[^7] Right now, a new operator reading `AGENTS.md` literally would look for backlog state in root `tickets/`, while the actual repo evidence lives in `active-plans/`, `active-audits/`, archived diagnosis plans, and free-form validation logs.[^6][^13]

### 3. Regression control is mostly manual, and the repo has no checked-in CI for the canonical validation quartet

Scafforge defines its own package release-gate commands clearly: `npm run validate:contract`, `npm run validate:smoke`, `python3 scripts/integration_test_scafforge.py`, and `python3 scripts/validate_gpttalker_migration.py` are the canonical package-level validators.[^1][^14] But there are no checked-in GitHub workflow files under `.github/` that run those commands on push or PR; the remote Actions inventory only shows dynamic Copilot review/agent workflows and CodeQL, and the GitHub issue tracker is empty.[^8]

In practice, the repo is using markdown logs as a manual validation ledger. `active-plans/validation-log.md` records “package validation is green again” across many working-tree changes, but those green claims were not enough to prevent today’s smoke regression from sitting at `HEAD`.[^3][^9] The result is a release process where regressions can coexist with recent “validated” narratives, which is exactly the kind of trust gap Scafforge is supposed to remove from generated repos.[^7]

### 4. The smoke subsystem is still structurally brittle even aside from today’s regression

The architecture doc and the active smoke decomposition plan agree on the diagnosis: `smoke_test.ts` is still a monolithic tool that mixes command detection, execution, failure classification, artifact rendering, and orchestration, and it still stops after the first blocking failure.[^15] The current code confirms the fail-fast behavior with a `break` as soon as `commandBlocksPass(result)` is true.[^5]

That architecture has two costs. First, it masks secondary failures that would improve diagnosis, because only the first blocking command is captured in a single run.[^15] Second, it makes regressions like the current missing-executable classification bug harder to isolate, because detection, platform-specific failure interpretation, artifact generation, and orchestration all live in one place.[^15]

Recent history shows this is not theoretical. The implementation log on 2026-04-13 records that the package had to patch `smoke_test.ts` again because stale-remediation tickets could reach smoke-test with valid QA evidence and still fail with “No deterministic smoke-test commands detected,” which means the smoke tool is still an active defect hotspot rather than a stable substrate.[^16]

### 5. Open workflow debts remain on the repo’s own books

Scafforge has fixed many earlier critical traps, but the repo is still carrying open workflow debt. The current root-cause map leaves **RC-003** (“`asserted_completed_stages` not re-validated”) open, meaning assertion-based stage completions can still diverge from evidence-backed completions.[^10] It also leaves **RC-006** open, meaning backward routing during `managed_blocked` is still not fully covered by centralized enforcement.[^10]

The blocker register still marks a broader Godot/product validation concern as active (**BLK-005**), and the skill-flow manifest still records **CYCLE001** — the dependency seam between `project-skill-bootstrap` and `opencode-team-bootstrap` — as accepted temporary debt rather than resolved design simplification.[^10] None of these are “red build right now” failures on the scale of the smoke regression, but they are exactly the kind of unresolved contract edges that accumulate into future repair loops and operator confusion.[^7][^10]

### 6. Operational knowledge is fragmented across plans and logs

The repo’s own large assessment file already concluded that `active-plans/` had lost a clean distinction between canonical durable docs, historical-but-useful notes, and runtime clutter, and that the directory needed hygiene rules so only canonical assessment/plan/status docs stayed prominent.[^13] At the time of that assessment, the log count was already 228 files; today the observed count is 338 files, with 18 top-level plan files still sitting in `active-plans/`.[^13]

That clutter is structurally encouraged by the runner. `scripts/run_agent.sh` hardwires `active-plans/agent-logs` as the logging destination for multi-provider downstream runs, and every provider attempt tees command output into per-run log files.[^17] With no GitHub issues open or closed, those logs and markdown plans have effectively become the repo’s live issue tracker, backlog, and evidence archive all at once.[^8][^13][^17]

The net effect is that Scafforge has strong raw evidence retention but weak evidence curation. Researching the repo is possible — that is what this report did — but it is more expensive than it should be because canonical history, exploratory notes, runtime logs, and validation narratives are mixed together.[^13]

### 7. Downstream convergence is still not the same thing as generated-repo self-sufficiency

The package’s recent validation log shows real progress: fresh public audits on downstream repos no longer reproduce some earlier Scafforge-routed workflow blockers, and managed repair now clears several workflow-finding families before leaving only source-follow-up or product-surface work.[^9] That is a meaningful improvement.

But the same validation log and full assessment still show how much of Scafforge’s practical success depends on host-side repair loops, curated evidence handling, and repeated downstream runs. The repo’s own evidence continues to describe widespread `EXEC-REMED-001` follow-up in downstream repos and repeated package work to keep the repair/audit/handoff loop truthful.[^9][^19] Relative to the competence contract’s promise of one clear legal next move and generated-repo self-sufficiency, Scafforge is improving, but it has not fully escaped heavy host-side operational babysitting.[^7][^19]

## What should **not** be treated as current failures

Some older critiques are now stale. The repair layer is no longer missing backup/restore behavior: current code backs up existing targets, records diff summaries, optionally preserves backups, and restores from backup on failure.[^11] Likewise, the bug register marks several earlier high-severity defects — missing `hasPendingRepairFollowOn` import, copytree `.venv` crashes, model-prefix doubling, provenance round-trip loss, and unhelpful managed-blocked messaging — as fixed.[^12]

That matters because a lot of Scafforge’s archived plans are intentionally historical. The right reading of the repo today is **not** “the base architecture is still broken everywhere”; it is “the architecture is mostly coherent, but the repo still lacks strong regression control, has a currently red smoke gate, and has allowed its package-root operating story to drift away from the actual working surfaces.”[^3][^6][^8][^11][^12]

## Recommended remediation plan

1. **Fix the smoke classification regression first.** The safest repair is to preflight executable resolution before `spawn()` (or otherwise normalize `EIO`/runner-specific failures into a missing-executable classification when the executable cannot be resolved), then extend `scripts/smoke_test_scafforge.py` with a regression that asserts the currently observed `spawn EIO` path is classified as `missing_executable`.[^3][^4][^5]
2. **Add repo-local CI for the canonical validation quartet.** At minimum, PR automation should run the two package npm validators plus the integration and GPTTalker migration validators that the repo itself calls canonical. Until that exists, “green again” statements in logs and commit messages remain too easy to invalidate accidentally.[^1][^8][^9][^14]
3. **Reconcile `AGENTS.md`/README with reality.** Either restore a real package-root `tickets/` backlog and root historical handoff surface, or rewrite the docs so `active-plans/`, `active-audits/`, and archived handoff references are the official package working surfaces. Leaving both stories in parallel violates the repo’s own competence bar.[^6][^7]
4. **Split `smoke_test.ts` and remove fail-fast behavior.** The repo already has the design sketch: separate detection, execution, classification, artifact generation, and orchestration, and run all detected commands before classifying the result set. That will improve diagnosis even when a failure still occurs.[^15]
5. **Give `active-plans/` real hygiene rules.** The existing assessment already asked for archiving/indexing rules; the current log count shows that need has only grown. Concretely: archive old logs, keep one index of canonical docs, and stop using free-form markdown as the only searchable issue system.[^8][^13][^17]
6. **Close the explicitly tracked workflow debts.** RC-003, RC-006, the broader Godot/product validation blocker, and CYCLE001 are already named. They should be treated as the next structural cleanup bundle after the smoke regression and CI work, because they are small enough to target and important enough to keep generating confusion if left open.[^10]
7. **Do not reopen already-fixed repair-safety bugs without fresh evidence.** The repo has already paid to add repair backups, restoration, and provenance hardening; future work should build on that baseline instead of re-litigating those older defects from stale plans.[^11][^12]

## Confidence Assessment

**High confidence:** Scafforge’s intended architecture, current smoke failure, current missing-executable repro behavior, package-root surface drift, lack of repo-local CI workflows, open recorded debt items, and active-plans/log sprawl are all directly supported by current repo files or fresh observed evidence.[^2][^3][^4][^6][^8][^10][^13]

**Medium confidence:** The most likely root cause of the smoke regression is the mismatch between the tool’s ENOENT/127-based missing-executable detection and the currently observed `spawn EIO` runner behavior. That explanation fits both the live repro and the code, but I did not isolate the lower-level Node/runtime cause of the `EIO` itself.[^4][^5]

**Important uncertainty:** Some validation-log entries may have been true on the exact host/package state where they were written. The present conclusion is not that those notes were fabricated; it is that the repo currently lacks strong enough automated regression enforcement to make those claims durable across subsequent changes.[^3][^8][^9]

## Footnotes

[^1]: `/home/pc/projects/Scafforge/README.md:3-9,22-29,60-80`; `/home/pc/projects/Scafforge/package.json:1-30`.
[^2]: `/home/pc/projects/Scafforge/architecture.md:5-30,33-63,76-119,123-145,157-181`; `/home/pc/projects/Scafforge/skills/skill-flow-manifest.json:26-39,67-97,98-257`.
[^3]: `/home/pc/.copilot/session-state/c55ec71d-3cd5-464b-a412-acd49aa80b86/files/research-evidence.md:3-25`; `/home/pc/projects/Scafforge/scripts/smoke_test_scafforge.py:9008-9040,12663-12670`.
[^4]: `/home/pc/.copilot/session-state/c55ec71d-3cd5-464b-a412-acd49aa80b86/files/research-evidence.md:27-58`.
[^5]: `/home/pc/projects/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts:552-570,643-718,749-780,878-917`.
[^6]: `/home/pc/projects/Scafforge/AGENTS.md:55-72`; `/home/pc/projects/Scafforge/README.md:46-52`; `/home/pc/.copilot/session-state/c55ec71d-3cd5-464b-a412-acd49aa80b86/files/research-evidence.md:72-76`; `/home/pc/projects/Scafforge/references/archived-diagnosis-plans/IMPLEMENTATION-HANDOFF.md:1-18`.
[^7]: `/home/pc/projects/Scafforge/references/competence-contract.md:1-15`.
[^8]: `/home/pc/projects/Scafforge/package.json:28-30`; `/home/pc/.copilot/session-state/c55ec71d-3cd5-464b-a412-acd49aa80b86/files/research-evidence.md:78-83`.
[^9]: `/home/pc/projects/Scafforge/active-plans/validation-log.md:7-12`; commit `6db058fa37699ee0694fff0a2ec76b63e5a8fced`.
[^10]: `/home/pc/projects/Scafforge/active-plans/bug-and-structural-flaw-register.md:54-72`; `/home/pc/projects/Scafforge/active-plans/root-cause-map.md:34-43,73-82,86-108`; `/home/pc/projects/Scafforge/active-plans/blocker-register.md:8-24`; `/home/pc/projects/Scafforge/skills/skill-flow-manifest.json:12-24`.
[^11]: `/home/pc/projects/Scafforge/skills/scafforge-repair/scripts/apply_repo_process_repair.py:765-801,1451-1635`.
[^12]: `/home/pc/projects/Scafforge/active-plans/bug-and-structural-flaw-register.md:3-40`.
[^13]: `/home/pc/projects/Scafforge/active-plans/fullassessment1104261519.md:177-252`; `/home/pc/.copilot/session-state/c55ec71d-3cd5-464b-a412-acd49aa80b86/files/research-evidence.md:60-70`.
[^14]: `/home/pc/projects/Scafforge/AGENTS.md:86-94`; `/home/pc/projects/Scafforge/README.md:22-29`.
[^15]: `/home/pc/projects/Scafforge/architecture.md:199-215`; `/home/pc/projects/Scafforge/active-plans/smoke-tool-decomposition.md:1-27`; `/home/pc/projects/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts:878-886`.
[^16]: `/home/pc/projects/Scafforge/active-plans/implementation-log.md:5-15`.
[^17]: `/home/pc/projects/Scafforge/scripts/run_agent.sh:17-20,127-148,151-260`.
[^18]: `/home/pc/projects/Scafforge/architecture.md:123-131`; `/home/pc/projects/Scafforge/active-plans/bug-and-structural-flaw-register.md:5-10`.
[^19]: `/home/pc/projects/Scafforge/active-plans/validation-log.md:24-30,36-37`; `/home/pc/projects/Scafforge/active-plans/fullassessment1104261519.md:13-24,49-52`.
