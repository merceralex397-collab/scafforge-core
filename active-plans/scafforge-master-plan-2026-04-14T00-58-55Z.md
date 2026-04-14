# Scafforge final master repair, simplification, and validation plan

## 1. End state

The target is not merely "fewer bugs." The target is:

- any supported repo type exposes **one obvious legal next move**
- a weak model can tell whether it is time to plan, implement, review, QA, smoke-test, close out, or stop
- the agent knows **which tool** to call, **which owner** must act, **which artifact** is required, **which format** it must use, and **which blocker path** applies
- `audit -> repair -> continue` runs smoothly across downstream repos without direct downstream hand edits
- game repos have a real asset-pipeline capability that helps choose, seed, route, prove, and audit content workflows instead of leaving the downstream repo to improvise

This plan treats operator or agent confusion as package evidence. If an agent can get stuck in a way that a simpler contract could have prevented, that is a Scafforge defect even if no single line technically crashes.

## 2. Evidence used during planning

### 2.1 Current repo state

- Branch: `autofixing`
- Branch position: `38` commits ahead of `main`
- Current worktree state: clean during planning
- Total commits seen in direct history review: `229`

### 2.2 Live package baseline captured during planning

- `npm run validate:contract` -> pass
- `npm run validate:smoke` -> pass
- `python3 scripts/integration_test_scafforge.py` -> fail (`proof-python-cli` currently trips `EXEC002` because the seeded test/import shape uses `src.proof_python_cli` even though `src` is not importable during pytest collection)
- `python3 scripts/validate_gpttalker_migration.py` -> pass, but the report still proves a fixture-backed `/tmp` migration path rather than live downstream smoothness

### 2.3 Concrete planning evidence

- `GPTTalker/gpttalkerstuck1.md`
- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/root-cause-map.md`
- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/blocker-register.md`
- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/bug-and-structural-flaw-register.md`
- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/validation-log.md`
- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/fullassessment1104261519.md`
- `active-plans/asset-pipeline-agent-research-2026-04-14.md`
- `active-plans/scafforge-present-state-research-report-2026-04-14.md`
- latest downstream diagnosis manifests for `GPTTalker`, `spinner`, `glitch`, and `womanvshorseVA/VB/VC/VD`
- direct branch diff and full-history churn analysis

### 2.4 Rubber-duck / sub-agent planning inputs already returned

- `workflow-duck`: identified the lack of a stable `repair_follow_on` contract, contradictory `managed_blocked` semantics, mismatched repair completion paths, string-parsed reconciliation logic, smoke contract instability, and docs/harness drift
- `history-duck`: confirmed that `managed_blocked`, graph validation, repair-follow-on, Godot export, and verdict-parsing are repeated-fix gravity wells and that evidence noise is overwhelming code signal
- `validation-duck`: identified validation blind spots, GPTTalker-heavy fixtures, weak Godot proof, and the need to compare diagnosis deltas rather than stop at "package green"
- `workflow-duck-lite`: highlighted workflow complexity, restart-surface drift, provenance round-trip gaps, bootstrap/verification ordering risk, and the need to split guidance from mechanical helpers
- `history-duck-lite`: highlighted repeated deadlock patterns, Godot ETC2/ASTC churn, graph-validation bypass proliferation, and tracked evidence/process debris

### 2.5 Direct complexity metrics captured during planning

- Team leader prompt: `298` lines
- `ticket-execution` skill: `118` lines
- generated `workflow.md`: `111` lines
- generated `ticket_lookup.ts`: `674` lines
- generated `ticket_update.ts`: `229` lines
- generated `repair_follow_on_refresh.ts`: `94` lines
- generated `stage-gate-enforcer.ts`: `543` lines
- generated shared `workflow.ts`: `2035` lines
- total measured core workflow surface above: `4261` lines
- generated tool count: `18`
- generated agent count: `17`
- references to `artifact_write` / `artifact_register` across prompts and skills: `32`

These numbers matter because weak models are not navigating a tiny state machine. They are navigating a large, multi-authority rule system with many chances to choose the wrong surface.

### 2.6 Additional report-backed evidence now folded into the plan

- the current smoke regression is not only "red"; the live repro specifically drops `host_surface_classification: missing_executable` because the explicit-missing-executable path is surfacing as `Error: spawn EIO` with `missing_executable: null`
- package-root operating docs currently describe root `tickets/` and `IMPLEMENTATION-HANDOFF.md` as active truth surfaces even though real package work is happening through `active-plans/`, `active-audits/`, and archived references
- the canonical validation quartet is not backed by checked-in repo-local CI, so markdown "green again" claims can drift away from actual `HEAD`
- `scripts/run_agent.sh` currently amplifies `active-plans/agent-logs/` sprawl by treating the planning directory as a long-lived log sink
- the asset-pipeline redesign needs a capability taxonomy, machine-readable compliance surfaces, and separate tool-license versus model-license provenance rather than only coarse source-route labels

## 3. Current diagnosis summary

### 3.1 Workflow cognition and usability failures

1. **Stage/status vocabulary is too easy to misuse.**
   - `GPTTalker/gpttalkerstuck1.md` shows the team leader manually authoring a large implementation artifact, then attempting `ticket_update` with `stage=review, status=todo`, which is rejected because the stage expects `status=review`.
   - This is not just a bug. It is evidence that the workflow still asks the agent to memorize stage/status trivia that should be mechanized.

2. **Artifact production is too manual.**
   - `artifact_write.ts` only persists raw text.
   - `artifact_register.ts` is a second mandatory step.
   - Prompts and skills repeatedly instruct agents to remember headings, verdict lines, raw output sections, and canonical paths.
   - Weak models are being asked to act as formatting clerks in addition to engineers.

3. **Too many surfaces describe the same workflow differently.**
   - `workflow.ts`
   - `stage-gate-enforcer.ts`
   - `ticket_lookup.ts`
   - `ticket_update.ts`
   - `repair_follow_on_refresh.ts`
   - `ticket-execution/SKILL.md`
   - team-leader prompt
   - `docs/process/workflow.md`
   - restart surfaces

4. **The system still relies on hidden memory.**
   - Agents need to remember exact stage ordering, exact status names, artifact ownership, remediation-only review evidence rules, bootstrap-first behavior, smoke-test ownership, and repair-follow-on semantics.
   - The competence contract explicitly says no workflow step may depend on hidden operator memory of extra flags, follow-up commands, or omitted transcript inputs. Current evidence shows that standard is not met.

### 3.2 Contract and architecture failures

1. **`repair_follow_on` is not a single stable contract.**
   - Writer, loader, validator, prompts, and reconciliation logic disagree on payload shape and completion semantics.
   - Some fields are dropped on round-trip.
   - Some logic still depends on human-readable blocking-reason text parsing.

2. **`managed_blocked` is contradictory.**
   - Some surfaces describe it as stop-and-report.
   - Some describe it as self-resolve.
   - Some carve out allowed mutation paths.
   - The plugin, prompts, and skills do not agree on what is actually legal.

3. **Lifecycle authority is duplicated.**
   - Forward/backward routing logic appears in multiple places.
   - Restart-surface truth is derived but still drifts.
   - Graph-validation bypasses have spread because invariants are not cleanly localized.

4. **Validation is still partly string-based instead of behavior-based.**
   - Verdict parsing has needed multiple fixes.
   - Some proof still depends on string presence instead of round-trip state invariants.
   - The smoke system still has a live failing semantic regression.

5. **Post-closeout pointer convergence is still unreliable.**
   - Historical downstream evidence shows multiple repos finishing or superseding a lane while `tickets/manifest.json`, workflow active-ticket pointers, and restart surfaces still point at stale closed work.
   - This is a direct violation of the "one legal next move" contract because the package leaves contradictory active-ticket truth after closeout.
   - Current GPTTalker evidence shows the failure is not only stale pointers: `START-HERE.md` can still recommend "Continue the required internal lifecycle from the current ticket stage." while the active ticket is already `done`, `open_remediation_tickets` is `0`, and `repair_follow_on.outcome` is `source_follow_up`.
   - The present audit flow did not flag that illegal next action, which means restart-surface validation is still checking rendered fields more than legal-move semantics.

### 3.3 Smoke, proof, and validation failures

1. **Smoke regressions still matter even though the current command is green.**
   - On the current `2026-04-14` package run, `npm run validate:smoke` passes.
   - The earlier missing-explicit-executable regression still belongs in scope because it shaped the smoke contract work: the child-process layer was surfacing `Error: spawn EIO` and the logic only promoted a narrower `missing_executable` host-surface classification for `ENOENT`, exit `127`, or matching stderr text.
   - The smoke workstream should now focus on making that regression stay dead and on finishing the remaining resume/checkpoint and coverage gaps, not on pretending the top-level smoke command is still the package's current red gate.

2. **Smoke architecture is still fail-fast.**
   - This conflicts with the architecture goal that smoke should collect all actionable failures, not mask later ones.

3. **Proof quality is uneven by stack.**
   - GPTTalker migration validation is fixture-heavy and `/tmp`-based.
   - Godot proof exists, but the package still needs stronger release/finish and import/load guarantees.
   - Public audits are not yet clearly proving asset-pipeline starter surfaces on live game repos.
   - Current Spinner evidence shows that "Godot headless load passes" is still too weak as a game-quality proxy: the shared spinner core still uses frame-dependent interaction math (`_current_velocity *= friction` each physics frame, drag velocity divided by a hardcoded `0.016`), and exported `hit_radius` values are being treated as verified toddler-safe interaction zones even though the current `InputDetector` never uses `hit_radius` at all.
   - The latest Spinner audit no longer surfaces those shared gameplay defects, which means Scafforge's current game review/audit path can lose real code-quality findings while continuing to validate workflow surfaces.
   - Current `glitch` evidence shows the Godot reference-integrity and execution audits are still not extension-boundary-safe: valid `res://...gdshader` references are being truncated to `.gd`, which produces false `EXEC-GODOT-002` and `REF-001` failures against repos whose shader files actually exist.
   - That means the package can still block a truthful Godot repo on a parser defect inside the audit layer rather than a real missing-file condition.
   - Current `glitch` evidence also shows that Scafforge can still certify Godot gameplay features by file inspection and method presence even when the live scene wiring is broken: `TouchControls.tscn` has no button `pressed`/`released` hookups into `TouchController`, `Checkpoint.tscn` has no `body_entered` hookup into `Checkpoint.gd`, and `PlayerController._jump_state()` currently falls through to `FALL` immediately on `not is_on_floor()`.
   - Historical review and QA artifacts still marked those surfaces as passing, which means present Godot review coverage is still too structural and does not yet prove scene-signal integrity or basic controller-state viability.
   - Current `womanvshorseVA` evidence shows the same weakness at the API-contract layer: review artifacts allowed runtime-incompatible Godot code patterns such as `CanvasLayer` scripts calling `draw_circle()` / `queue_redraw()`, `Node` scripts calling `get_viewport_rect()`, and signal wiring built against `hud.get_script()` instead of the live HUD instance.
   - `godot4 --headless --path /home/rowan/womanvshorseVA --quit` still fails today with those parse errors, which means present package review/QA still does not systematically prove script-base compatibility, node/script attachment compatibility, or instance-vs-script callable correctness before runtime.
   - Current `womanvshorseVB` evidence shows that Godot "clean load" proof is still too forgiving at the warning layer: headless startup exits `0` but emits an invalid UID warning and silently falls back from a stale `uid://...` reference in `title_screen.tscn` to the asset path.
   - The latest VB diagnosis still reported `warnings: 0`, which means current import/load validation is not surfacing warning-level resource-identity drift even when the engine is already recovering from it at runtime.
   - The package's own multi-stack validation is also currently not green end-to-end: `python3 scripts/integration_test_scafforge.py` fails because `seed_python_cli_target()` writes `from src.proof_python_cli import format_message` into both `tests/test_cli.py` and `src/proof_python_cli/__main__.py`, but the generated package layout does not make `src` importable during pytest collection.
   - Reproducing the current proof target still yields `ModuleNotFoundError: No module named 'src'`, so the greenfield continuation verifier correctly reports `EXEC002` for the generated Python CLI probe.

4. **Regression control is still too manual.**
   - The repo defines a canonical validation quartet, but those release-gate commands are not yet enforced by checked-in repo-local CI.
   - Validation-log narratives are therefore acting as a soft release ledger instead of a continuously enforced guardrail.
   - On the current host run, the quartet is not green end-to-end because `integration_test_scafforge.py` is still failing even while `validate:contract`, `validate:smoke`, and `validate_gpttalker_migration.py` pass.

5. **Smoke does not yet have explicit resume/checkpoint semantics.**
   - The current monolith does not persist partial execution checkpoints or idempotency markers, which weakens post-failure diagnosis and resume-style headless execution.

6. **Proof-command validity is still under-policed.**
   - Current GPTTalker evidence shows that historically accepted migration proof commands can be non-runnable against the repo's real runtime contract.
   - The recorded `FIX-018` command shape uses `sqlite3.connect(':memory:')` and a sync-style call into an async `DatabaseManager` / `run_migrations` path; rerunning that command against the current repo still fails with `TypeError: object sqlite3.Cursor can't be used in 'await' expression`.
   - This means the package still allows tickets, audits, and review artifacts to treat command-shaped prose as proof even when the command is type-invalid or drifted away from the actual runtime API.
   - Current Godot release evidence shows this is also a live package inconsistency: `skills/ticket-pack-builder/SKILL.md` and `skills/ticket-pack-builder/scripts/apply_remediation_follow_up.py` still emit `godot --headless --path . --export-debug Android ...` while the template and audit now expect `Android Debug`.
   - Rerunning that stale command shape against the current `glitch` repo fails immediately with `Invalid export preset name: Android.`, proving the package can still generate acceptance commands that are syntactically wrong for the repo surfaces it just produced.

7. **Host/path leakage still reaches durable repo surfaces.**
   - Current Spinner evidence shows operator-specific absolute paths still land in live ticket acceptance and validation commands such as `godot4 --headless --path /home/pc/projects/spinner ...`.
   - That leakage is not confined to archived diagnosis packs; it remains in current repo ticket surfaces (`BUGFIX-NAV-004`, `BUGFIX-NAV-005`, and corresponding manifest entries), which weakens portability, makes copied evidence less truthful on another machine, and obscures whether a command is meant to be repo-relative or host-specific.

### 3.4 Asset-pipeline failures

1. **The current `asset-pipeline` skill exists, but it is still too generic.**
   - It has route concepts and a seeding script, but it does not yet feel like a firm strategy router with route-specific decision support, failure modes, and downstream operating guidance.

2. **`possibleassethelp` is more opinionated than the current Scafforge asset skill.**
   - It has an umbrella router (`game-studio`)
   - it has specialist route skills (`sprite-pipeline`, `web-3d-asset-pipeline`, etc.)
   - it includes concrete scripts
   - it includes quality gates and workflow staging
   - the current Scafforge asset skill does not yet give the same confidence or route specificity

3. **Game integration exists in tests, but live repo backfill appears incomplete.**
   - `integration_test_scafforge.py` explicitly expects:
     - `assets/pipeline.json`
     - `.opencode/meta/asset-pipeline-bootstrap.json`
     - `assets/PROVENANCE.md`
   - none of the live `womanvshorseVA/VB/VC/VD` repos appear to have `assets/pipeline.json`
   - none of them appear to have `.opencode/meta/asset-pipeline-bootstrap.json`
   - this is strong evidence of a real gap between package claim and downstream reality

4. **The current asset routes need refinement.**
   - Route A is described as "Codex-derived ideas," which is not really an asset acquisition route. It is closer to a procedural/programmatic design route.
   - The skill needs stronger handling for:
     - procedural/programmatic assets
     - free/open sourcing
     - Blender-MCP generation
     - Godot-native content creation
     - hybrid mixed-route repos
     - route-specific validation and ticketing

5. **The current route model is not internally comparable enough for strong decision support.**
   - current routes mix inspiration, sourcing, execution recipe, and engine feature bucket in one list
   - the package needs a cleaner route taxonomy so the downstream repo can receive unambiguous route-specific skills, agents, tickets, and proof rules

6. **Provenance is still inconsistent and under-wired.**
   - provenance expectations drift between documentation, initializer output, and validation
   - `validate_provenance.py` exists, but it is not yet clearly wired into the public greenfield, audit, repair, and release loops

7. **Current asset seeding is still too heuristic-driven.**
   - the current flow leans on stack-label and keyword inference
   - the womanvshorse repos show that canonical brief route truth is not being fully propagated into seeded metadata, route-specific agents, route-specific skills, and tickets

8. **The pipeline still collapses tool provenance and model provenance together.**
   - local AI generation stacks can be open-source while the actual checkpoint or model weights carry different commercial, attribution, or non-commercial restrictions
   - the current provenance story does not yet enforce tool-level versus model-level license policy separately

9. **The seeded asset surfaces are too small for serious compliance and import QA.**
   - `assets/pipeline.json` and `assets/PROVENANCE.md` are not enough on their own for route selection, attribution generation, workflow capture, import QA, or license-policy enforcement

10. **Asset-role decomposition is too coarse for weak-model downstream execution.**
   - the current starter hints do not yet split route strategy, sourcing, generation, optimization, and provenance audit into narrow enough responsibilities

11. **Route-specific finish proof is still underdefined.**
   - historical womanvshorse evidence shows that export success or route presence is not enough; the route also needs route-appropriate runtime/playability/visual proof and, where relevant, screenshot-backed or artifact-backed finish review

### 3.5 Womanvshorse learnings already visible

1. **VA** proves that procedural/programmatic art is a real route, not a placeholder route.
   - The pipeline must explicitly support "no external assets" repos and still define finish proof.

2. **VB** proves that provenance-heavy free/open sourcing works, but it needs deeper license/credits/import tooling.
   - `assets/PROVENANCE.md` is rich and concrete here.
   - it also shows repo-bloat and sanitization problems that the package should help prevent.
   - Current live VB evidence also shows import validation must cover Godot resource-identity cleanliness, not just file presence: `title_screen.tscn` still carries a stale texture UID that headless load downgrades into a warning and a path fallback.

3. **VC** proves that Blender-MCP is viable as a route, but it needs stronger briefs, richer provenance, persistence discipline, import validation, and budgets.
   - Current provenance is only two lines for the two generated models.
   - it also needs a clearer workfile policy so intermediate Blender files do not leak into final runtime asset areas.
   - Current live VC evidence shows the route can still outrun the runnable baseline entirely: `MODEL-001` and `MODEL-002` are marked done while `SETUP-001` and `SETUP-002` remain open, `project.godot` still has no `run/main_scene`, and the repo has no `scenes/` or `scripts/` surfaces at all.
   - The current VC ticket graph even inverts the dependency spine (`SETUP-001` depends on `MODEL-006`, while `MODEL-*` tickets depend on nothing), which means the package still needs an explicit "minimal runnable baseline before specialization" contract for Blender-MCP and other asset-heavy routes.

4. **VD** proves that Godot-native creation is also a first-class route.
   - The pipeline must still record the route explicitly even when there are no external assets to track.
   - that route still needs reference-integrity and mobile-renderer proof.

### 3.6 Evidence, repo hygiene, and drift failures

1. Tracked logs and diagnosis output are overwhelming code signal.
2. `.running-pids` and temp-path coupling suggest process debris and host-specific assumptions are still leaking into durable evidence.
3. Live repos appear to lag template truth.
4. Some reports describe stale optimistic states that no longer match live validators.
5. Package-root documentation and actual operating surfaces have drifted apart.
6. `active-plans/agent-logs/` is currently mixed into the same tree as live planning documents.
7. The repo still depends too much on markdown validation narratives instead of automated regression enforcement.
8. Historical session evidence shows that downstream no-hand-edit governance is still too easy to violate when package and repo truth surfaces drift.
9. Project-scoped discovery tools versus external SDK/template paths remain an under-specified friction point for headless game validation.

## 4. Non-negotiable design decisions for the repair

### 4.1 One legal next move becomes a machine contract

It must no longer live primarily in prompt prose. There will be one canonical machine-readable contract for:

- current stage
- current owner
- legal next actions
- required artifact kind and path
- required proof before transition
- allowed recovery and blocker paths

The public runtime expression of that contract should be a deterministic **action card** returned by `ticket_lookup` and echoed by restart surfaces:

- actor
- action type
- exact tool
- schema-valid args
- exact artifact expectation, if any
- explicit illegal alternatives and why they are illegal

All prompts, docs, restart surfaces, and validators must derive from or verify against that contract.

### 4.2 Simplification must preserve capability

The plan is not to delete workflow protections. The plan is to make the protected path easier than the wrong path.

That means:

- keep low-level tools where needed for compatibility
- add simpler deterministic wrappers or helpers for common stage transitions and artifact submission
- shrink prompt burden by moving mechanical knowledge into tools and generated cheat-sheets

### 4.3 Artifact writing must stop being a clerical trap

The agent should not have to manually remember every heading, verdict label, and path for every artifact family.

The plan will treat this as a core architecture problem, not just a prompt wording problem.

Markdown should become presentation, not the primary truth substrate for artifact validation. The plan will move toward structured evidence first, rendered markdown second.

### 4.4 `managed_blocked` and `repair_follow_on` must become explicit and typed

No string parsing, no dropped fields, no contradictory self-resolution stories, no ambiguous mutation carve-outs.

### 4.5 Asset pipeline becomes an umbrella strategy router, not a thin side skill

Scafforge must help decide and scaffold the content route.

The downstream repo must still own actual asset creation/acquisition/import work.

### 4.6 Nothing is deferred out of scope

Open blockers, smoke architecture debt, workflow simplification, asset-pipeline redesign, evidence hygiene, live repo backfill, and cross-stack proof are all included in this plan.

## 5. Execution workstreams

### Workstream 1: Rebuild the baseline and freeze a truth ledger

#### Goal

Start implementation from live truth, not from stale documents or optimistic memory.

#### Actions

- rerun the package baseline
- compare live validator output with active-plans claims
- build a current issue ledger with statuses:
  - open
  - resolved
  - regressed
  - stale-doc-only
  - downstream-only
- record which repo surfaces are package truth vs evidence noise

#### Primary files

- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/validation-log.md`
- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/root-cause-map.md`
- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/blocker-register.md`
- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/fullassessment1104261519.md`
- `reports/gpttalker-validation/latest.*`

#### Verification

- the ledger explains every known issue family and whether it is currently reproduced
- stale documents are explicitly marked as stale in the ledger
- live validator output is captured before any edits

### Workstream 2: Build a workflow cognition inventory and failure taxonomy

#### Goal

Turn "agents are confused" into a concrete set of reproducible failure classes across any repo type.

#### Actions

- inspect `GPTTalker/gpttalkerstuck1.md` in detail
- classify confusion families:
  - stage/status ambiguity
  - artifact-format ambiguity
  - duplicate-authority ambiguity
  - hidden-state ambiguity
  - bootstrap/repair/process-flag ambiguity
  - next-owner ambiguity
  - tool-signature mismatch
  - too-many-valid-looking choices
- produce a stage-by-stage matrix:
  - stage
  - visible owner
  - legal tool
  - exact next args
  - artifact requirement
  - blocker path
  - restart-surface summary
- explicitly model non-happy-path state families as first-class workflow states, not side notes:
  - `pending_process_verification`
  - `managed_blocked`
  - allowed follow-on ticket creation
  - repair follow-on completion
  - issue intake / reopen / reconcile / reverify

#### Primary files

- `GPTTalker/gpttalkerstuck1.md`
- generated team-leader prompt
- generated `ticket-execution` skill
- generated `workflow.md`
- generated `ticket_lookup.ts`
- generated `ticket_update.ts`

#### Verification

- every workflow stage has an explicit confusion taxonomy entry
- every confusion class maps to at least one planned package change or validation

### Workstream 3: Centralize lifecycle, next-action, and ownership truth

#### Goal

Make lifecycle truth live in one authoritative runtime contract instead of being repeated and hand-translated across prompts, docs, and tools.

#### Actions

- centralize stage/status/owner/artifact/recovery truth in a canonical runtime contract
- make `ticket_lookup.transition_guidance` the precise, typed next-action bundle, not a vague description
- include in that bundle:
  - exact next tool
  - exact args
  - exact owner
  - exact artifact kind/path if applicable
  - exact reason other actions are currently illegal
- derive or verify the following surfaces from the same contract:
  - `workflow.ts`
  - `ticket_lookup.ts`
  - `ticket_update.ts`
  - `ticket-execution/SKILL.md`
  - team-leader prompt
  - `docs/process/workflow.md`
  - restart surfaces
- explicitly converge post-closeout and post-supersede truth so:
  - `tickets/manifest.json`
  - workflow active-ticket pointers
  - stage/status
  - restart surfaces
  all foreground the same next live lane instead of a closed ticket
- make recommended next-action generation fail closed when the active ticket is already `done`:
  - if split children or blocked dependents remain, foreground them
  - if historical reconciliation or trust restoration remains, name `ticket_reconcile` or `ticket_reverify`
  - if `repair_follow_on.outcome == source_follow_up`, route to the actual source-follow-up target instead of the closed ticket's prior stage
  - never emit the generic "continue the current ticket stage" fallback for a closed ticket with no legal lifecycle move
- add an audit-visible invariant for restart-surface legality, not only rendered-field agreement, so audits fail when `Next Action` points at a closed ticket or impossible tool path

#### Planned simplification move

Commit to adding a higher-level typed `ticket_transition` wrapper as the canonical happy-path transition tool so weak models do not need to memorize stage/status pairings like:

- `review -> review`
- `qa -> qa`
- `smoke-test -> smoke_test`
- `closeout -> done`

Keep `ticket_update` for compatibility, but treat it as a legacy low-level surface. Prompts, restart surfaces, and generated guidance route to `ticket_transition`, and any aliases such as `ticket_advance` must remain thin derived wrappers rather than independent authorities.

Make `status` mostly internal on the happy path so the weak-model path only chooses:

- advance
- return_for_rework
- block
- clear_process_verification
- close

Also explicitly separate **legal-next-move state** from **audit/repair telemetry** so `repair_follow_on`, `pending_process_verification`, and related fields do not remain one overloaded blob.

#### Verification

- snapshot tests prove one legal next move for every stage and relevant blocker state
- stage/status mismatches become mechanically hard to produce
- `ticket_lookup`, prompts, workflow docs, and restart surfaces agree on the same next action
- post-closeout and post-supersede proofs keep manifest/workflow/restart pointers converged on the same current lane
- closed-ticket + `source_follow_up` states never emit a restart instruction that tells the operator to continue the closed ticket's lifecycle stage
- audit checks fail if `START-HERE.md` presents a next action that is inconsistent with the legal action card derived from canonical state

### Workstream 4: Simplify artifact production without losing rigor

#### Goal

Remove clerical burden from artifact authoring while preserving strict evidence quality.

#### Actions

- design and implement a deterministic artifact helper path:
  - use one single-call `artifact_submit` wrapper as the canonical happy path
  - allow stage-specific aliases only if they are thin derived wrappers over the same contract
  - return canonical structured fields first and rendered markdown second
- reduce the need for agents to memorize:
  - heading names
  - verdict labels
  - raw-output sections
  - canonical path selection
  - write-then-register sequencing
- keep stage-specific evidence requirements strict:
  - implementation must carry execution/syntax/build evidence
  - review must carry actionable findings and verdict
  - QA must carry raw command output and verdict
  - smoke must remain tool-owned
- rename or clarify misleading artifact concepts such as the remediation-review "QA section" so a review artifact is never confused with the actual `qa` stage artifact
- ensure the team leader never receives raw `artifact_write` or `artifact_register` as its own final next move when delegation is the real required action
- add deterministic stage-specific examples into specialist prompts and repo-local skills

#### Primary files

- generated `artifact_write.ts`
- generated `artifact_register.ts`
- specialist prompts
- `ticket_lookup.ts`
- `ticket-execution/SKILL.md`

#### Verification

- a reproduction based on `gpttalkerstuck1.md` no longer requires manual stage/status or artifact-format guesswork
- invalid artifact shapes get exact corrective guidance, not generic failure
- stage specialists can complete artifact work in one obvious path
- validators consume structured evidence fields first and rendered markdown second

### Workstream 5: Redesign `repair_follow_on` and `managed_blocked`

#### Goal

Make repair follow-on state explicit, typed, stable on round-trip, and consistent across runtime, repair scripts, prompts, docs, and validators.

#### Actions

- define one canonical `repair_follow_on` payload
- keep legal-next-move fields separate from repair/audit telemetry fields so gating state and historical evidence cannot overwrite each other
- ensure all fields survive runtime load/save round-trip
- align:
  - `run_managed_repair.py`
  - `apply_repo_process_repair.py`
  - `follow_on_tracking.py`
  - `record_repair_stage_completion.py`
  - `repair_follow_on_refresh.ts`
  - `reconcile_repair_follow_on.py`
  - runtime loader/writer in `workflow.ts`
  - validator expectations
- replace string parsing of blocking reasons with structured reason codes
- make the completion path consistent:
  - recorded current-cycle evidence is required for follow-on completion
  - no silent self-resolution path exists outside explicit recorded evidence
- make `managed_blocked` fail-closed in the same way everywhere
- preserve typed gating data such as `allowed_follow_on_tickets` and `pending_process_verification` in the canonical payload instead of reconstructing them from prose or logs

#### Verification

- no field loss on round-trip
- no unauthorized mutation via `bash`, `write`, or `edit` during true `managed_blocked`
- allowed follow-on self-resolution, if kept, is exact and typed
- current-cycle completion evidence is required where intended

### Workstream 6: Align stage-gate, ticket tools, prompts, docs, and restart surfaces

#### Goal

End the current multi-authority drift.

#### Actions

- compare and reconcile:
  - `stage-gate-enforcer.ts`
  - `ticket_lookup.ts`
  - `ticket_update.ts`
  - `environment_bootstrap.ts`
  - `handoff_publish.ts`
  - `ticket_create.ts`
  - `ticket_reconcile.ts`
  - `ticket_reverify.ts`
  - `issue_intake.ts`
  - `workflow.md`
  - team-leader prompt
  - `ticket-execution/SKILL.md`
  - `START-HERE.md`
  - `.opencode/state/context-snapshot.md`
  - `.opencode/state/latest-handoff.md`
  - `skill-flow-manifest.json`
  - `skills/scaffold-kickoff/SKILL.md`
  - `skills/scafforge-audit/*`
  - `skills/scafforge-repair/*`
  - `scripts/run_agent.sh`
  - invocation-tracking surfaces such as `skill_ping` and invocation logs
- eliminate duplicated or conflicting transition logic
- ensure restart surfaces do not summarize the state differently than runtime tools
- verify that repair-side and runtime-side restart publication do not reintroduce duplicate authority
- collapse restart guidance toward one primary next-action surface, with any secondary restart documents strictly derived and minimal
- treat `START-HERE.md` as the primary human restart surface and require all other restart documents to stay strictly derived from the same next-action contract
- make restart-surface validation distinguish "field parity" from "action legality" so a surface can fail even when copied fields match but the named next move is impossible
- teach audit and repair to detect the GPTTalker-class contradiction: active ticket already closed, no open remediation tickets, `source_follow_up` visible, but restart prose still tells the agent to continue the closed ticket stage

#### Verification

- drift tests fail when docs/prompts/tools disagree on stage order, artifact ownership, or next action
- restart surfaces always match canonical state after mutation and repair
- restart surfaces also expose a legally executable next move, not just a textually synchronized summary

### Workstream 7: Fix the remaining proof-gate failures and harden the broader proof architecture

#### Goal

Get the package green again, then make green actually mean something.

#### Actions

- fix the current missing-executable classification regression
- normalize platform-specific missing-executable failures such as `spawn EIO` into the same canonical host-surface classification as `ENOENT`
- preflight executable resolution where possible so explicit-missing-executable cases are classified before command launch semantics distort the signal
- remove fail-fast masking from the generated smoke tool
- add resume/checkpoint semantics so partial smoke execution can be resumed or at least diagnosed without losing already-captured command evidence
- strengthen failure classification semantics
- ensure stack-specific smoke and finish proof stay truthful
- fix the current `proof-python-cli` integration fixture so seeded Python CLI probes use an import/package shape that actually collects under pytest
- make external dependency discovery and explicit command overrides truthful for non-project-scoped assets such as Godot export templates, Android tooling, and other SDK paths
- strengthen package validation sequencing so the manual validators are part of the standard convergence bar, not hidden extras
- add checked-in repo-local CI for the canonical validation quartet so release claims are not carried only by markdown logs
- add regression coverage for the live `spawn EIO` path and any equivalent provider/runtime-specific missing-executable paths
- compare package green to downstream reality so package green cannot hide live repo drift
- add audit-stability checks so the same package commit and same repo state do not oscillate between different public findings
- require remediation acceptance commands and review-command evidence to be executable against the repo's real runtime contract, not just command-shaped text
- store and validate proof commands as structured runnable inputs (`argv`, env, cwd, interpreter/runtime expectations) so audit and repair can rerun them exactly
- add a validator path that rejects historically accepted commands when they are sync/async-invalid, target the wrong interpreter, or no longer match the repo's actual entrypoint/API contract

#### Primary files

- `scripts/smoke_test_scafforge.py`
- generated `smoke_test.ts`
- `scripts/validate_scafforge_contract.py`
- `scripts/integration_test_scafforge.py`
- `scripts/validate_gpttalker_migration.py`

#### Verification

- `npm run validate:smoke` passes
- `python3 scripts/integration_test_scafforge.py` passes
- smoke runs all planned commands and preserves all findings
- explicit-missing-executable probes classify as `missing_executable` even on the currently observed `spawn EIO` path
- interrupted or partially completed smoke runs preserve enough checkpoint/evidence state to support deterministic diagnosis and resume
- Godot/Android smoke probes capture both export success and post-export artifact inspection where the route requires shipped outputs
- repo-local CI runs the canonical validation quartet and fails closed on regressions
- package green plus downstream delta checks agree
- remediation review proof fails closed when the recorded command cannot be rerun successfully on the current repo contract
- validators distinguish "raw command recorded" from "raw command was actually runnable and produced the claimed outcome"

### Workstream 8: Eliminate template-live drift and backfill current repos

#### Goal

Make current live repos reflect the current package truth before using them as proof targets.

#### Actions

- compare current template surfaces to live repo-managed copies in:
  - `glitch`
  - `GPTTalker`
  - `spinner`
  - `womanvshorseVA/VB/VC/VD`
- identify missing package fixes
- run managed repair/backfill through the mandated lanes
- confirm the latest package features actually land downstream
- add a workflow-surface version or fingerprint so generated or repaired repos can prove whether they actually carry the current contract

#### Key focus areas

- workflow contract fixes
- stage-gate fixes
- verdict parsing fixes
- blocker-reason hardening
- asset-pipeline starter surfaces for game repos

#### Verification

- live repo-managed surfaces match the intended package version after repair
- downstream audits stop reporting package-routed drift that should already be fixed
- repair or scaffold fails closed when a repo claims current package truth but surface fingerprints disagree

### Workstream 9: Redesign the asset pipeline into a serious game-content framework

#### Goal

Turn `asset-pipeline` from a thin generic skill into a robust game-content strategy layer that helps decide, scaffold, route, validate, and repair content work.

#### Architecture direction

`asset-pipeline` becomes the umbrella router for game/content pipeline work, similar in spirit to how `possibleassethelp/skills/game-studio/SKILL.md` routes into specialist paths.

#### Core changes

1. **Reframe the route catalog into comparable route families**
   - repo-authored procedural/programmatic
   - third-party open/licensed
   - Blender-MCP generated
   - Godot-native authored
   - optional sprite-generation subroute
   - hybrid mixed-route projects
   - stop treating inspiration or design-pattern sources as if they were asset-acquisition routes

2. **Add route-specific guidance surfaces**
   - stronger references
   - stronger decision trees
   - route-specific quality gates
   - route-specific verification commands
   - route-specific provenance rules
   - route-specific ticketing guidance

3. **Use `possibleassethelp` as concept source**
   - umbrella routing
   - specialist skill split
   - concrete scripts
   - quality gates
   - playtest loop
   - engine/content-specific references

4. **Add an explicit asset-strategy phase for game repos**
   - the canonical brief must carry a per-domain asset strategy:
     - finish bar
     - allowed licenses
     - candidate routes
     - selected route
     - fallback route
   - `scaffold-kickoff` must resolve this before scaffold render for game repos instead of hoping route hints can be inferred later

5. **Strengthen deterministic seeding**
   - ensure game scaffolds always seed:
     - `assets/pipeline.json`
     - `assets/provenance.json`
     - `assets/PROVENANCE.md`
     - `assets/briefs/README.md`
     - `assets/previews/`
     - `assets/workfiles/`
     - `assets/licenses/`
     - `assets/import-reports/`
     - `.opencode/meta/asset-pipeline-bootstrap.json`
   - ensure those surfaces survive repair and refresh

6. **Strengthen downstream ownership**
   - Scafforge decides and scaffolds the route
   - the downstream repo owns actual asset acquisition, generation, import, validation, and finishing work
   - the generated local skills and tickets must carry that ownership clearly

7. **Integrate better into greenfield and repair**
   - `repo-scaffold-factory` seeds the deterministic surfaces
   - `asset-pipeline` refines the route map
   - `project-skill-bootstrap` synthesizes route-specific local skills from metadata **or canonical-brief evidence**
   - `opencode-team-bootstrap` adds route-specific specialists from metadata **or canonical-brief evidence**
   - `agent-prompt-engineering` hardens ownership and route language
   - `ticket-pack-builder` seeds asset route tickets
   - `verify_generated_scaffold` and public audit prove the surfaces exist and agree

8. **Fix provenance and route validation**
   - make provenance machine-readable first and human-readable second
   - derive `assets/PROVENANCE.md` from canonical provenance metadata instead of letting it drift by hand
   - wire provenance validation into greenfield verification, audit, repair verification, and release/finish gates
   - add public audit findings for:
     - missing `assets/pipeline.json`
     - missing `.opencode/meta/asset-pipeline-bootstrap.json`
     - missing or incomplete provenance where route policy requires it
     - route/agent/skill/ticket misalignment

9. **Adopt route-specific specialists and helpers**
   - `asset-sourcer`
   - `blender-asset-creator`
   - `godot-native-artist` or equivalent finish implementer
   - route-aware QA/reviewer support
   - absorb or replicate useful `possibleassethelp` capabilities such as sprite normalization/preview, 3D shipping optimization, and playtest/visual QA guidance

10. **Replace coarse route labels with a capability taxonomy**
   - `source-open-curated`
   - `source-mixed-license`
   - `procedural-2d`
   - `procedural-layout`
   - `procedural-world`
   - `local-ai-2d`
   - `local-ai-audio`
   - `reconstruct-3d`
   - `dcc-assembly`
   - `optimize-import`
   - `provenance-compliance`

11. **Seed stronger machine-readable asset surfaces**
   - `assets/requirements.json`
   - `assets/manifest.json`
   - `assets/ATTRIBUTION.md`
   - `assets/workflows/`
   - `assets/previews/`
   - `assets/qa/import-report.json`
   - `assets/qa/license-report.json`
   - `.opencode/meta/asset-provenance-lock.json`

12. **Make compliance and import validation first-class**
   - enforce allowed and denied licenses by policy
   - distinguish tool license from model-weight license
   - require author/source URL, tool name, model ID, workflow ID, and version/hash where feasible
   - validate asset budgets for meshes, textures, and audio
   - validate Godot import success and version-controlled import metadata where applicable
   - require preview artifacts for human audit

13. **Split asset work into weaker-model-safe operating roles**
   - `asset-strategist`
   - `asset-sourcer`
   - `texture-ui-generator`
   - `audio-generator`
   - `world-builder`
   - `blender-asset-creator`
   - `import-optimizer`
   - `provenance-auditor`

14. **Encode fallback ladders by asset class**
   - UI/fonts/icons: curated sources first, composition/reskinning second, AI only for bespoke splash art
   - 2D tiles/sprites: curated packs first, tileset/layout synthesis second, targeted generation only to fill gaps
   - VFX: Godot-native particles and shaders first
   - audio: procedural SFX first, curated sourcing second, AI only behind explicit policy
   - low-poly props: curated low-poly sources plus Blender cleanup
   - terrain/environments: procedural terrain/layout plus open materials and selective DCC work

15. **Model the asset pipeline as a router plus specialist operating pack**
   - keep one umbrella entrypoint for asset strategy and route choice
   - immediately hand off to narrow route-specific specialists instead of one monolithic "make assets" skill
   - keep runtime/engine architecture, asset shipping, UI/frontend, and playtest/finish review as separate bounded concerns

16. **Require route-appropriate visual and playtest proof**
   - screenshot-backed or artifact-backed finish review for visible game routes
   - route-specific runtime import/load validation
   - playfield/HUD readability checks where the route affects presentation
   - keep optimization upstream so runtime loaders stay simple and predictable

17. **Harden Blender route operational readiness**
   - add an asset-description/briefing surface that turns game needs into Blender route tasks
   - add a registry bridge from Blender outputs into Scafforge asset manifests
   - automate or at least verify add-on/runtime setup requirements instead of assuming a manually prepared Blender host forever

#### Primary files

- `skills/asset-pipeline/SKILL.md`
- `skills/asset-pipeline/scripts/init_asset_pipeline.py`
- `skills/asset-pipeline/scripts/validate_provenance.py`
- `skills/project-skill-bootstrap/SKILL.md`
- `skills/opencode-team-bootstrap/SKILL.md`
- `skills/repo-scaffold-factory/SKILL.md`
- `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`
- `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`
- public audit scripts that should inspect live game repos
- `archive/archived-diagnosis-plans/active-plans-review-2026-04-14/possibleassethelp/*`

#### Verification

- route scaffolds exist for every game greenfield probe
- route-specific local skills and agents are generated when metadata demands them
- public audit can detect missing asset starter surfaces and provenance drift in live game repos
- route probes distinguish tool-license versus model-license provenance
- generated asset manifests, attribution, workflow capture, and QA reports stay mutually consistent
- route-specific finish review uses visual/runtime evidence that matches the selected route rather than generic export success alone

### Workstream 10: Learn from and backfill all four womanvshorse repos

#### Goal

Use the womanvshorse repos as evidence of what each route needs, then repair any missing package-owned surfaces.

#### Route-specific lessons to extract and operationalize

- **VA procedural/programmatic**
  - prove that "no external assets" is a first-class finish route
  - define what finish proof means when the route is procedural
  - add explicit route metadata and runtime visual proof instead of treating the route as "no asset work"

- **VB free/open**
  - strengthen provenance and attribution handling
  - define credits-scene and license-proof expectations
  - define import/format/normalization checks
  - add source scoring, download sanitization, runtime file-manifest discipline, and access-friction fallback policy

- **VC Blender-MCP**
  - strengthen asset-brief quality, persistence chaining, import proof, budgets, and richer provenance
  - verify that generated local skills and agents actually reflect the Blender persistence contract
  - add explicit workfile policy and capability negotiation instead of assuming one Blender execution mode forever

- **VD Godot-built-in**
  - define finish proof for no-external-assets repos
  - make the route explicit even when provenance file is intentionally minimal
  - add reference-integrity and mobile-renderer proof where relevant

#### Concrete package concerns already visible

- live repos appear to be missing `assets/pipeline.json`
- live repos appear to be missing `.opencode/meta/asset-pipeline-bootstrap.json`
- some routes have strong repo evidence (`VB` provenance), while others are under-specified (`VC` provenance too thin)
- `VB` shows asset-bloat and provenance coverage problems even when provenance exists
- `VC` shows that strong asset briefs are collapsing into generic tickets
- `VD` shows that "no external assets" still needs explicit route proof and validation

#### Verification

- after package-side fixes and downstream repair, each repo explicitly reflects its asset route
- each route has corresponding local skill/agent/ticket support where appropriate
- each route has route-appropriate finish proof
- each repo carries the expected asset starter surfaces or an explicit justified minimal variant

### Workstream 11: Extend validation to cover any repo type, not just current downstreams

#### Goal

Prove the simplified workflow on representative repo categories, not only on the current live downstream trio.

#### Coverage matrix to build

- Python service/app
- Node project
- Rust or Go project
- Java or Android project
- .NET project
- Godot 2D game
- Godot 3D game
- Makefile/shell fallback repo
- retrofit path
- managed-repair path
- pivot path
- diagnosis-review path

#### What to prove for each representative probe

- bootstrap lane exposes one legal first move
- ticket selection and lifecycle progression are clear
- artifact submission path is obvious
- smoke/validation path is truthful
- repair path does not create contradictory states
- restart surfaces match runtime contract
- interrupted-run resume/hydration returns to canonical state instead of fresh-starting
- audit reruns are stable for the same package commit and same repo state
- stack-specific behavior checks actually exercise the representative failure modes of that stack instead of stopping at generic boot success
- for Godot repos specifically, validation covers interaction invariants such as frame-rate independence, input-zone gating, and UI-overlay isolation from gameplay touch handlers
- for Godot repos specifically, reference-integrity scanning is extension-boundary-safe and correctly distinguishes scripts from other engine resource types such as shaders instead of truncating valid paths into false missing-script errors
- for Godot repos specifically, validation proves scene signal hookups for declared gameplay/UI handlers instead of only checking that matching methods exist in `.gd` files
- for Godot repos specifically, controller-state checks catch impossible or trivially collapsing transitions such as a jump state that immediately demotes itself to fall on every airborne frame
- for Godot repos specifically, validation proves runtime API compatibility between the attached node type, the script base type, and the methods called in that script instead of assuming any parsed `.gd` body is semantically attachable
- for Godot repos specifically, load/import proof distinguishes clean success from warningful fallback and surfaces invalid resource UIDs or import-identity drift as actionable findings
- for Blender-MCP and other asset-heavy game routes specifically, specialization tickets cannot outrun the runnable baseline: `SETUP-001`, `run/main_scene`, and minimal scene/script surfaces must exist before model-generation tickets can close

#### Verification

- each representative probe has explicit expected outputs and pass criteria
- no stack silently falls back to Python-shaped assumptions
- Godot probes fail when shared gameplay helpers accept dead tuning vars as "verified" or when interaction behavior changes materially across frame rates
- Godot audit probes do not emit `EXEC-GODOT-002` / `REF-001` false positives for valid non-script engine resources such as `.gdshader`
- Godot probes fail when scene-owned input or checkpoint behavior depends on unwired `.tscn` signal connections that review/QA artifacts claimed were already verified
- Godot release proofs fail when package-generated export commands use a preset name that does not match the repo's actual `export_presets.cfg`
- Godot probes fail when scripts rely on APIs that do not exist on their declared base type or on the node type they are attached to
- Godot probes surface warning-level resource UID/import drift instead of silently treating warningful loads as clean proof
- asset-heavy route probes fail when model/content tickets can complete ahead of a runnable baseline (`run/main_scene`, minimal scene tree, and setup ticket chain)

### Workstream 12: Run the downstream proof loop until smooth

#### Goal

Demonstrate that current downstream targets actually benefit from the package changes and no longer exhibit Scafforge-induced friction.

#### Repos in proof scope

- `GPTTalker`
- `spinner`
- `glitch`
- `womanvshorseVA`
- `womanvshorseVB`
- `womanvshorseVC`
- `womanvshorseVD`
- `blender-agent` direct proof where package integration depends on it

#### Required lane order

- sync changed Scafforge skills to:
  - `~/.codex/skills/`
  - `~/.copilot/skills/`
  - `~/.config/kilo/skills/`
- run headless `codex exec` audit/repair first
- use Kilo fallback when needed
- use Copilot fallback only last
- use headless `opencode run` for downstream ticket continuation

#### Smoothness bar

- no repeated lifecycle confusion loops
- no artifact-format confusion loops
- no invalid stage/status probing loops
- no package-routed workflow blockers that should have been fixed package-side
- no restart-surface contradiction traps
- no resume/hydration fresh-start drift after `--continue`
- provider fallback and global-skill sync behave exactly as designed
- live downstream proof uses actual product/runtime commands, not only fixture success
- same package commit + same repo state produces stable audit results
- successful proof runs reach the correct next move without repeated invalid transition attempts
- successful proof runs do not require manual artifact rewrites after the canonical helper path is chosen

### Workstream 13: Repair evidence hygiene, host coupling, and documentation drift

#### Goal

Make Scafforge itself easier to audit, reason about, and bisect.

#### Actions

- reduce tracked runtime noise where possible
- relocate or archive stale logs and heavy evidence that no longer belong in active canonical locations
- clean `.running-pids` handling and other process debris
- reduce hardcoded host/tmp path assumptions where they are still leaking into proof
- eliminate operator-specific absolute paths from durable generated repo surfaces such as ticket acceptance text, review instructions, audit manifests, and canned validation commands unless the path is explicitly categorized as host-local evidence
- reconcile package-root docs with the actual package operating surfaces so `AGENTS.md`, `README.md`, and archive references stop telling different stories about where package work lives
- separate active planning documents from long-lived execution logs so `active-plans/` no longer doubles as the default runtime log sink
- stop treating markdown validation narratives as sufficient release truth without automated corroboration
- strengthen runner/docs/contract language so no-direct-downstream governance is explicit, checkable, and hard to accidentally violate during package work
- document and validate when agents must use `bash` rather than project-scoped discovery tools for external SDK/template discovery
- update:
  - `README.md`
  - `architecture.md`
  - `AGENTS.md`
  - active-plans canonical docs
- make canonical-vs-historical-vs-runtime evidence boundaries explicit

#### Verification

- docs match code truth
- active evidence surfaces are clearly canonical or historical
- runtime debris is no longer confusing code review
- the package repo itself exposes one clear legal next move for package work with no root-surface contradiction
- active planning docs and archived log evidence are clearly separated
- governance docs and runner prompts consistently forbid direct downstream edits for governed repos

### Workstream 14: Final convergence gate

#### Goal

End only when the package, the generated contract, and the live downstream repos all tell the same story.

#### Final gate requirements

- package validators pass
- repo-local CI for the canonical validation quartet is green
- new workflow simplification regressions pass
- asset-pipeline route probes pass
- representative cross-stack probes pass
- downstream audits no longer show package-owned workflow defects
- downstream continuation is smooth in practice
- post-closeout pointer convergence is green on all proof repos
- finish proof is route-appropriate and not satisfied by export existence alone
- docs and restart surfaces match runtime truth
- repeated audits on the same package commit and same repo state do not oscillate
- resume/hydration proof is green
- host/path leakage proof is green

## 6. Verification and validation matrix

### 6.1 Package validators

- `npm run validate:contract`
- `npm run validate:smoke`
- `python3 scripts/integration_test_scafforge.py`
- `python3 scripts/validate_gpttalker_migration.py`

These are necessary but not sufficient.

### 6.2 Workflow simplification proofs

Build or expand replayable proofs for:

- invalid stage/status guess attempts
- artifact-format ambiguity
- coordinator-vs-specialist artifact ownership ambiguity
- remediation-review "QA section" naming confusion
- `managed_blocked` contradiction cases
- `repair_follow_on` round-trip persistence
- `pending_process_verification` non-happy-path routing
- allowed follow-on ticket creation gating
- restart-surface drift after repair
- stage-owner mismatch
- coordinator artifact authorship traps
- bootstrap-not-ready routing
- post-closeout pointer convergence
- supersede/reopen pointer convergence

### 6.3 Weak-model "would an idiot know what to do?" proofs

For each stage and run type, verify that a weak model can recover the correct next move from:

- `ticket_lookup.transition_guidance`
- the current team-leader prompt
- `ticket-execution/SKILL.md`
- `docs/process/workflow.md`
- `START-HERE.md`

The pass condition is not "all these files exist." The pass condition is:

- one next move
- one owner
- one tool
- one artifact requirement
- one blocker route
- no contradictory alternate story
- zero invalid stage/status retries before the correct next move is chosen in the proof run
- zero coordinator-authored stage-artifact attempts in the proof run

Turn `GPTTalker/gpttalkerstuck1.md` into a first-class regression family and test stuck checkpoints directly against the new action-card contract.

### 6.4 Asset-pipeline proofs

Build greenfield or repair probes for:

- procedural/programmatic route
- free/open route
- Blender-MCP route
- Godot-native route
- mixed-route game

For each, prove:

- an asset decision artifact exists
- deterministic starter surfaces exist
- route map is specific
- local skills and agents reflect the route
- ticketing reflects the route
- provenance rules are appropriate
- machine-readable provenance and human-readable provenance remain aligned
- route-specific verification actually runs
- public audit can detect missing package-owned asset surfaces
- route-specific finish review uses visual/runtime evidence that matches the selected route rather than generic export success alone

### 6.5 Cross-stack proofs

Run representative probes across supported stack families and verify:

- bootstrap truthfulness
- lifecycle clarity
- artifact clarity
- smoke truthfulness
- restart-surface alignment
- repair behavior
- interrupted-run resume/hydration behavior
- audit stability under repeated runs on the same state
- the proof fixtures and seeded representative repos are themselves import-valid, runnable, and aligned with the packaging/layout conventions they claim to represent

### 6.6 Live downstream proofs

For `GPTTalker`, `spinner`, `glitch`, and `womanvshorseVA/VB/VC/VD`:

- audit
- repair if needed
- continue
- observe whether the repo now runs smoothly
- verify post-closeout active-ticket/workflow/restart convergence
- verify diagnosis freshness after package changes instead of trusting stale packs

Use explicit live proof commands where applicable, not just package fixtures. At minimum the plan must cover:

- `./scripts/run_agent.sh {gpttalker,spinner,glitch,wvhva,wvhvb,wvhvc,wvhvd} --audit`
- `./scripts/run_agent.sh {gpttalker,spinner,glitch,wvhva,wvhvb,wvhvc,wvhvd} --repair`
- `./scripts/run_agent.sh {gpttalker,spinner,glitch,wvhva,wvhvb,wvhvc,wvhvd} --continue`
- GPTTalker startup/tool exposure proof
- GPTTalker restart-surface legality proof for the closed-ticket + `source_follow_up` state
- GPTTalker migration-proof command validity proof against the repo's actual async database contract
- Godot headless load proof for game repos
- Godot Android export proof where required
- APK inspection for produced Android artifacts
- Godot audit-finding truthfulness proof for game repos, including a fixture that contains valid shader/resource references and must not trip missing-script or missing-resource findings
- Godot command-truthfulness proof that package-generated Android export commands use the same preset name the scaffold actually emitted

For `GPTTalker`, specifically verify the workflow that produced `gpttalkerstuck1.md` no longer traps the agent in formatting/lifecycle confusion.
Also verify that no generated or repaired GPTTalker state can surface a closed-ticket `Next Action`, and that any remediation acceptance command preserved in tickets or review artifacts still executes successfully under the live runtime contract.

For `spinner`, `glitch`, and womanvshorse game repos, verify both workflow smoothness and route-appropriate game/asset proof.
For `spinner`, specifically verify that shared gameplay helpers no longer pass package review with frame-dependent interaction math, dead `hit_radius` configuration, or adult-control touches that can still route into toy-spin handling.
For `glitch`, specifically verify that valid Godot shader/resource references no longer trip false `EXEC-GODOT-002` or `REF-001` findings during audit reruns.
Also verify that game-scene signal wiring is real rather than implied by method names, and that package-generated Godot release commands still match the preset name and arguments the repo actually exposes.
For `womanvshorseVA`, specifically verify that runtime-incompatible Godot API usage (wrong base class, wrong attached node type, or Script-resource callable misuse) cannot pass review/QA before the repo hits runtime.
For `womanvshorseVB`, specifically verify that headless Godot proof no longer treats invalid UID fallback warnings as a clean pass.
For `womanvshorseVC`, specifically verify that Blender-route model-generation work cannot outrun `SETUP-001` / `run/main_scene` / minimal scene-script baseline creation.

### 6.7 Propagation and version proofs

For every generated or repaired repo in proof scope, verify:

- workflow-surface version/fingerprint is recorded
- version/fingerprint matches the package contract that produced the repo
- repair and scaffold propagation actually installed the expected simplification and asset-pipeline surfaces

### 6.8 Host/path and provider-fallback proofs

Verify that:

- host-specific or `/tmp`-specific assumptions do not leak into durable contract truth
- generated tickets, acceptance criteria, restart guidance, and canned validation commands use repo-relative paths or explicit placeholders instead of machine-specific absolute paths
- provider fallback behaves in the required order: Codex -> Kilo -> Copilot
- skill sync is performed before proof on every changed skill family

## 7. No-regression strategy

- keep legacy low-level tools until wrapper coverage is proven
- add new helpers first, then move prompts and skills onto them
- ensure helpers are derived from one canonical contract so wrappers do not become competing authorities
- keep validation on old and new paths until convergence is proven
- compare diagnosis deltas, not just green/red outputs
- preserve strict evidence quality; simplify path selection, not proof standards

## 8. Todo execution order

1. refresh baseline and truth ledger
2. build the workflow confusion taxonomy
3. centralize lifecycle and next-action truth
4. simplify artifact submission
5. redesign `repair_follow_on` and `managed_blocked`
6. align prompts, tools, docs, and restart surfaces
7. fix the remaining proof-gate failures and harden proof architecture
8. eliminate template-live drift and backfill current repos
9. redesign the asset pipeline
10. synthesize womanvshorse route learnings and backfill those repos
11. extend proof across representative repo types
12. run downstream proof loops until smooth
13. repair evidence hygiene and docs drift
14. hold the final convergence gate only when all proof layers agree

### 8.1 Section-addressable todo index

- `TODO-01` — Execute **Workstream 1: Rebuild the baseline and freeze a truth ledger** and close it only after **6.1 Package validators** is rerun with current evidence recorded.
- `TODO-02` — Execute **Workstream 2: Build a workflow cognition inventory and failure taxonomy** and close it only after the simplification proofs in **6.2** and weak-model routing proofs in **6.3** show the new taxonomy is actually usable.
- `TODO-03` — Execute **Workstream 3: Centralize lifecycle, next-action, and ownership truth** and close it only after **6.2** and the restart-surface portions of **6.6** show one legal next move with no contradictory owners.
- `TODO-04` — Execute **Workstream 4: Simplify artifact production without losing rigor** and close it only after artifact evidence quality passes **6.2**, **6.3**, and the package validator reruns in **6.1**.
- `TODO-05` — Execute **Workstream 5: Redesign `repair_follow_on` and `managed_blocked`** and close it only after **6.2**, **6.6**, and **6.7** prove truthful restart routing and versioned follow-on state.
- `TODO-06` — Execute **Workstream 6: Align stage-gate, ticket tools, prompts, docs, and restart surfaces** and close it only after **6.2**, **6.3**, and **6.7** all agree on the same lifecycle contract.
- `TODO-07` — Execute **Workstream 7: Fix the remaining proof-gate failures and harden the broader proof architecture** and close it only after every command in **6.1** is green and the smoke/proof-specific requirements in **6.5** and **6.6** are satisfied.
- `TODO-08` — Execute **Workstream 8: Eliminate template-live drift and backfill current repos** and close it only after **6.6** and **6.7** show current downstream repos actually match current package truth.
- `TODO-09` — Execute **Workstream 9: Redesign the asset pipeline into a serious game-content framework** and close it only after **6.4 Asset-pipeline proofs** pass for every supported route family.
- `TODO-10` — Execute **Workstream 10: Learn from and backfill all four womanvshorse repos** and close it only after the womanvshorse-specific checks in **6.6** pass on live repos.
- `TODO-11` — Execute **Workstream 11: Extend validation to cover any repo type, not just current downstreams** and close it only after **6.5 Cross-stack proofs** passes on every representative probe.
- `TODO-12` — Execute **Workstream 12: Run the downstream proof loop until smooth** and close it only after the downstream matrix in **6.6** is green without hand-edited exceptions.
- `TODO-13` — Execute **Workstream 13: Repair evidence hygiene, host coupling, and documentation drift** and close it only after **6.8 Host/path and provider-fallback proofs** passes and the evidence/command contracts in **6.1** and **6.6** remain green.
- `TODO-14` — Execute **Workstream 14: Final convergence gate** and close it only after the full verification matrix in **6.1-6.8** passes and the no-regression rules in **7** still hold.

### 8.2 Todo completion contract

- A todo is not done when code lands; it is done only when the linked workstream actions are complete, the linked verification section passes, and the evidence is current for the package commit being evaluated.
- Any todo that changes generated behavior must include at least one rerun from **6.5** or **6.6** plus the relevant package validator reruns from **6.1**.
- Any todo that changes restart, lifecycle, ticket, or repair truth must prove that `START-HERE.md`, workflow state, and ticket state remain convergent under **6.2**, **6.3**, and **6.7**.
- Any todo that changes asset or game routes must prove route-specific validation under **6.4** and live downstream behavior under **6.6** before it can be marked complete.

## 9. Notes and constraints

- no direct hand edits in `GPTTalker`, `spinner`, or `glitch`
- downstream changes must come through the mandated lanes
- Scafforge remains the evidence and orchestration center
- game asset strategy belongs in Scafforge; actual asset work belongs in downstream repos
- nothing in this plan is treated as optional polish
