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
- `npm run validate:smoke` -> fail
- `python3 scripts/integration_test_scafforge.py` -> pass
- `python3 scripts/validate_gpttalker_migration.py` -> pass, but the report still proves a fixture-backed `/tmp` migration path rather than live downstream smoothness

### 2.3 Concrete planning evidence

- `GPTTalker/gpttalkerstuck1.md`
- `active-plans/root-cause-map.md`
- `active-plans/blocker-register.md`
- `active-plans/bug-and-structural-flaw-register.md`
- `active-plans/validation-log.md`
- `active-plans/fullassessment1104261519.md`
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

### 3.3 Smoke, proof, and validation failures

1. **`validate:smoke` is currently red.**
   - The missing-explicit-executable case is not being classified the way the harness expects.

2. **Smoke architecture is still fail-fast.**
   - This conflicts with the architecture goal that smoke should collect all actionable failures, not mask later ones.

3. **Proof quality is uneven by stack.**
   - GPTTalker migration validation is fixture-heavy and `/tmp`-based.
   - Godot proof exists, but the package still needs stronger release/finish and import/load guarantees.
   - Public audits are not yet clearly proving asset-pipeline starter surfaces on live game repos.

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

### 3.5 Womanvshorse learnings already visible

1. **VA** proves that procedural/programmatic art is a real route, not a placeholder route.
   - The pipeline must explicitly support "no external assets" repos and still define finish proof.

2. **VB** proves that provenance-heavy free/open sourcing works, but it needs deeper license/credits/import tooling.
   - `assets/PROVENANCE.md` is rich and concrete here.
   - it also shows repo-bloat and sanitization problems that the package should help prevent.

3. **VC** proves that Blender-MCP is viable as a route, but it needs stronger briefs, richer provenance, persistence discipline, import validation, and budgets.
   - Current provenance is only two lines for the two generated models.
   - it also needs a clearer workfile policy so intermediate Blender files do not leak into final runtime asset areas.

4. **VD** proves that Godot-native creation is also a first-class route.
   - The pipeline must still record the route explicitly even when there are no external assets to track.
   - that route still needs reference-integrity and mobile-renderer proof.

### 3.6 Evidence, repo hygiene, and drift failures

1. Tracked logs and diagnosis output are overwhelming code signal.
2. `.running-pids` and temp-path coupling suggest process debris and host-specific assumptions are still leaking into durable evidence.
3. Live repos appear to lag template truth.
4. Some reports describe stale optimistic states that no longer match live validators.

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

- `active-plans/validation-log.md`
- `active-plans/root-cause-map.md`
- `active-plans/blocker-register.md`
- `active-plans/fullassessment1104261519.md`
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

#### Verification

- drift tests fail when docs/prompts/tools disagree on stage order, artifact ownership, or next action
- restart surfaces always match canonical state after mutation and repair

### Workstream 7: Fix the live smoke failure and harden the broader proof architecture

#### Goal

Get the package green again, then make green actually mean something.

#### Actions

- fix the current missing-executable classification regression
- remove fail-fast masking from the generated smoke tool
- strengthen failure classification semantics
- ensure stack-specific smoke and finish proof stay truthful
- strengthen package validation sequencing so the manual validators are part of the standard convergence bar, not hidden extras
- compare package green to downstream reality so package green cannot hide live repo drift
- add audit-stability checks so the same package commit and same repo state do not oscillate between different public findings

#### Primary files

- `scripts/smoke_test_scafforge.py`
- generated `smoke_test.ts`
- `scripts/validate_scafforge_contract.py`
- `scripts/integration_test_scafforge.py`
- `scripts/validate_gpttalker_migration.py`

#### Verification

- `npm run validate:smoke` passes
- smoke runs all planned commands and preserves all findings
- package green plus downstream delta checks agree

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
- `active-plans/possibleassethelp/*`

#### Verification

- route scaffolds exist for every game greenfield probe
- route-specific local skills and agents are generated when metadata demands them
- public audit can detect missing asset starter surfaces and provenance drift in live game repos

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

#### Verification

- each representative probe has explicit expected outputs and pass criteria
- no stack silently falls back to Python-shaped assumptions

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

### Workstream 14: Final convergence gate

#### Goal

End only when the package, the generated contract, and the live downstream repos all tell the same story.

#### Final gate requirements

- package validators pass
- new workflow simplification regressions pass
- asset-pipeline route probes pass
- representative cross-stack probes pass
- downstream audits no longer show package-owned workflow defects
- downstream continuation is smooth in practice
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

### 6.6 Live downstream proofs

For `GPTTalker`, `spinner`, `glitch`, and `womanvshorseVA/VB/VC/VD`:

- audit
- repair if needed
- continue
- observe whether the repo now runs smoothly

Use explicit live proof commands where applicable, not just package fixtures. At minimum the plan must cover:

- `./scripts/run_agent.sh {gpttalker,spinner,glitch,wvhva,wvhvb,wvhvc,wvhvd} --audit`
- `./scripts/run_agent.sh {gpttalker,spinner,glitch,wvhva,wvhvb,wvhvc,wvhvd} --repair`
- `./scripts/run_agent.sh {gpttalker,spinner,glitch,wvhva,wvhvb,wvhvc,wvhvd} --continue`
- GPTTalker startup/tool exposure proof
- Godot headless load proof for game repos
- Godot Android export proof where required
- APK inspection for produced Android artifacts

For `GPTTalker`, specifically verify the workflow that produced `gpttalkerstuck1.md` no longer traps the agent in formatting/lifecycle confusion.

For `spinner`, `glitch`, and womanvshorse game repos, verify both workflow smoothness and route-appropriate game/asset proof.

### 6.7 Propagation and version proofs

For every generated or repaired repo in proof scope, verify:

- workflow-surface version/fingerprint is recorded
- version/fingerprint matches the package contract that produced the repo
- repair and scaffold propagation actually installed the expected simplification and asset-pipeline surfaces

### 6.8 Host/path and provider-fallback proofs

Verify that:

- host-specific or `/tmp`-specific assumptions do not leak into durable contract truth
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
7. fix the live smoke failure and harden proof architecture
8. eliminate template-live drift and backfill current repos
9. redesign the asset pipeline
10. synthesize womanvshorse route learnings and backfill those repos
11. extend proof across representative repo types
12. run downstream proof loops until smooth
13. repair evidence hygiene and docs drift
14. hold the final convergence gate only when all proof layers agree

## 9. Notes and constraints

- no direct hand edits in `GPTTalker`, `spinner`, or `glitch`
- downstream changes must come through the mandated lanes
- Scafforge remains the evidence and orchestration center
- game asset strategy belongs in Scafforge; actual asset work belongs in downstream repos
- nothing in this plan is treated as optional polish
