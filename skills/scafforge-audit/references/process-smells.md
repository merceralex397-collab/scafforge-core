# Process Smells

## Stage-like backlog statuses

- ticket status tries to encode planner approval or other transient workflow state
- result: agents infer missing artifacts from labels alone

## Contradictory status semantics

- the same status means different things in `docs/process/`, `tickets/README.md`, and `manifest.json`
- result: weak models follow whichever definition they read most recently

## Raw-file stage choreography

- team leader or commands coordinate workflow by editing ticket files, the board, and the manifest directly
- result: drift, loops, and impossible delegation

## Missing workflow-state layer

- no `ticket_lookup`, `ticket_update`, or workflow-state file
- result: the workflow has no explicit transient approval state

## Overloaded artifact tools

- `artifact_register` both writes artifact bodies and registers metadata
- result: weaker models pass a summary string and overwrite the canonical artifact body

## Artifact path drift

- prompts, docs, or skills disagree about canonical artifact paths
- result: agents write proof to the wrong location or treat missing proof as complete

## Workflow vocabulary drift

- tools, workflow-state defaults, and docs use different stage or status terms such as `ready_for_planning` or `code_review`
- result: stage gates and proof checks disagree about whether work may advance

## Workflow-state desync

- `ticket_update` mirrors a background ticket into workflow-state without activating it
- result: stage gates read approval or queue state for the wrong active ticket

## Handoff overwrite

- `handoff_publish` replaces curated `START-HERE.md` content with a generic generated summary
- result: the canonical restart surface loses repo-specific read order, validation, or risk guidance

## Unsafe read-only shell allowlists

- read-only agents still allow commands like `sed *` or `gofmt *`
- result: mutation sneaks through "inspection" roles

## Over-scoped session commands

- a preflight or status command also instructs the agent to continue the entire lifecycle
- result: the agent skips the expected stopping point

## Process change blindness

- the repo cannot tell whether its operating process was replaced or materially upgraded
- result: completed tickets continue to be trusted even after the workflow contract changed

## Missing post-migration verification lane

- the repo can replace its process layer but has no explicit backlog verifier or gated follow-up path
- result: migration issues are either missed or turned into ad hoc tickets with no proof trail

## Bootstrap deadlock (BOOT001 — bootstrap tool incompatible with local Python manager)

- the generated `environment_bootstrap` surface still hardcodes global `python3 -m pip` or ignores repo-local `uv.lock` / `.venv` signals
- result: bootstrap can fail before any write-capable ticket work starts, even when the repo already has a usable uv-managed environment; resume deadlocks on workflow gates instead of reaching source remediation
- why agents miss it: diagnosis imports modules and collects tests directly from `.venv`, but does not inspect the bootstrap tool or the failed bootstrap artifact that blocked the foreground workflow

## Bootstrap command/layout mismatch (BOOT002 — bootstrap command trace contradicts the repo's dependency layout)

- the repo declares Python validation tools behind `[project.optional-dependencies].dev`, `[dependency-groups].dev`, or `[tool.uv.dev-dependencies]`, but the latest bootstrap artifact still shows `uv sync --locked` without the required extra or group flags
- result: bootstrap can succeed mechanically while still leaving repo-local validation tools like `pytest` or `ruff` missing, so the same broken bootstrap command is retried and misclassified as operator follow-up
- why agents miss it: audits and repairs often notice the missing executable but do not correlate `pyproject.toml`, the bootstrap artifact command trace, and the managed `environment_bootstrap.ts` implementation

## Placeholder local skills (SKILL001 — repo-local skill still generic)

- one or more generated `.opencode/skills/*.md` files still contain scaffold filler such as `Replace this file...`
- result: the repo loses concrete stack and validation guidance, making framework-specific mistakes more likely during implementation
- why agents miss it: current audits validate workflow tooling and execution proof, but do not check whether project-skill-bootstrap actually replaced baseline placeholder skill text

## Model profile drift (MODEL001 — repo-local model surfaces stale or missing)

- the repo is missing `.opencode/skills/model-operating-profile/SKILL.md`, still references deprecated MiniMax M2.5 surfaces, or carries older model defaults across provenance, model matrix, and agent prompts
- result: the team leader and specialists keep stale delegation and evidence-shaping defaults even after the package moved to newer model guidance
- why agents miss it: current repairs can refresh deterministic workflow surfaces without regenerating project-specific model-profile or agent prompt layers, and weaker repair prompts may wrongly treat deprecated package-managed defaults as protected intent

## Repeated failed repair cycle (CYCLE001 — prior audit and repair did not clear workflow drift)

- the repo already contains a prior diagnosis pack plus a later repair-history entry, but the same workflow-layer findings are still present on the next audit
- result: the team can loop through audit -> repair -> resume -> fail without understanding which package defect, skipped regeneration step, or stale repair assumption caused the first repair to miss
- why agents miss it: current audits often describe only the current findings and not the failure of the previous diagnosis-to-repair cycle

## Repeated diagnosis churn (CYCLE002 — same-day diagnosis packs repeat without an intervening package or process-version change)

- the repo accumulates multiple same-day diagnosis packs that repeat the same repair-routed findings, but there is no later Scafforge package update, process-version change, or repair-history entry after the latest pack
- result: the team burns time generating new diagnosis packs that add no new decision-making evidence and still cannot proceed into a trustworthy repair run
- why agents miss it: current audits can treat every rerun as fresh evidence unless they compare same-day diagnosis manifests against the current findings and the absence of later package-side change

## Verification-basis regression (CYCLE003 — a later clean pack drops the earlier transcript basis)

- a transcript-backed diagnosis pack identified workflow defects, but a later zero-finding verification pack on the same day omitted the supporting logs and still recorded clean state
- result: the repo appears repaired on current-state evidence alone even though nobody proved the original deadlock no longer traps the operator
- why agents miss it: repair verification still looks successful when it reruns current-state audit only; the transcript basis has to be carried forward automatically or the workflow silently narrows the evidence set

## Smoke-test contract drift (WFLOW001 — generated smoke test ignores repo-managed Python)

- the generated `smoke_test` tool still uses system `python3 -m pytest` even when the repo exposes `uv.lock` or `.venv`
- result: ticket closeout can deadlock on a tooling mismatch even when repo-managed validation commands already work
- why agents miss it: the workflow looks deterministic on paper, but the generated tool is not actually aligned with the repo's runtime contract

## Handoff overclaim (WFLOW002 — published restart summary outruns evidence)

- `START-HERE.md` or `.opencode/state/latest-handoff.md` claims a dependency is unblocked, the issue is only tooling, or the problem is not a code defect even though the active ticket is not done or downstream verification has not run
- result: the next session starts from a false causal model and can waste time on the wrong repair surface
- why agents miss it: current handoff publication accepts free-form next-action text without validating it against manifest/workflow state or executed artifacts

## Review-stage ambiguity (WFLOW003 — plan review and implementation review are overloaded)

- docs describe plan review before implementation, but tools or prompts only allow `review` after an implementation artifact exists
- result: weaker models invent bypasses, set approval flags ad hoc, or move directly into implementation
- why agents miss it: the workflow reads coherently to a human while the operational tool contract enforces a different state machine

## Transition-contract mismatch (WFLOW004 — stage gates key off the wrong state surface or accept unsupported stages)

- `ticket_update` or the stage-gate plugin still checks `ticket.status` instead of lifecycle `ticket.stage`, or they accept unknown `stage` values without upfront validation
- result: the agent starts probing stage/status pairs because the operational contract is inconsistent or underspecified
- why agents miss it: the docs may describe the intended lifecycle correctly while the tool layer still enforces an older or partial state machine

## Smoke-proof bypass (WFLOW005 — generic artifact tools can fabricate closeout proof)

- `artifact_write` or `artifact_register` still allow `smoke-test` artifacts, or the plugin does not reserve that stage to `smoke_test`
- result: PASS-style closeout evidence can be written without the deterministic workflow tool ever running
- why agents miss it: the artifact layer appears complete, but the ownership boundary between generic artifact tools and deterministic closeout tools is missing

## Handoff ownership conflict (WFLOW007 — docs-handoff path and plugin enforcement disagree)

- the docs-handoff prompt tells agents to write and register an optional canonical `handoff` artifact, but the plugin blocks generic `artifact_write` or `artifact_register` for that same stage
- result: the documented closeout path dead-ends even though the generated docs lane is following package instructions
- why agents miss it: the handoff contract looks coherent when each surface is read alone, but the prompt and plugin disagree on who owns optional `handoff` artifacts

## Hidden process-verification state (WFLOW008 — pending backlog trust restoration is hidden or contradicted)

- `.opencode/state/workflow-state.json` sets `pending_process_verification: true`, but restart surfaces still imply ready-for-development handoff or `ticket_lookup` does not expose the backlog-verifier and `ticket_reverify` route
- result: the repo can look clean enough to resume normal development even though historical done tickets still need trust restoration under the newer workflow contract
- why agents miss it: the canonical workflow state does record the verification window, so shallow audits can assume the derived restart and routing surfaces stayed in sync

## Clearable process-verification deadlock (SESSION008 — transcript proves the legal clear path still fails)

- the supporting log shows `ticket_lookup.process_verification.clearable_now = true`, the coordinator calls metadata-only `ticket_update(..., pending_process_verification: false)` on the current writable ticket, and the installed tool still throws a lifecycle transition error such as `Cannot move X to implementation from implementation`
- result: the repo exposes a supposedly legal cleanup action that cannot actually execute, so agents stop on a fake lifecycle contradiction instead of clearing the stale global verification flag
- why agents miss it: surface-only audit sees the documented clear path in `ticket_lookup`, `ticket_update`, and the prompts, but without transcript evidence it cannot tell that the installed tool still routes the no-op cleanup through stage-entry validation

## Blender worker misrouting (SESSION009 — transcript proves a Blender-routed ticket stayed on the wrong worker)

- the supporting log says Blender scene-editing tools were unavailable in the current implementation toolset, yet the same transcript names `blender-asset-creator` as the correct next worker before any bridge defect should be accepted
- result: a Blender-routed asset ticket burns time on the generic implementer or lane-executor, then reports a fake MCP/tool-availability blocker even though the repo already exposes a dedicated Blender specialist
- why agents miss it: prompt review alone can look correct because the team-leader doc names the Blender specialist, but the installed `ticket_lookup.transition_guidance.delegate_to_agent` still routes implementation to the generic worker unless transcript evidence exposes the contradiction

## Restart-surface drift (WFLOW010 — derived restart files contradict canonical state)

- `START-HERE.md`, `.opencode/state/context-snapshot.md`, or `.opencode/state/latest-handoff.md` disagrees with `tickets/manifest.json` or `.opencode/state/workflow-state.json` about the active ticket, handoff status, bootstrap status, proof artifact, pending process verification, repair follow-on state, state revision, or lane-lease presence
- result: the next session starts from stale resume data and can route the wrong ticket, skip bootstrap recovery, or ignore an active lease
- why agents miss it: the repo still has the canonical state files, so shallow audits can assume restart surfaces were regenerated even when repair or tool saves left them stale

## Coordinator workflow overreach (WFLOW006 — team leader prompt leaves room for artifact authorship or command misuse)

- the team leader prompt does not route from `ticket_lookup.transition_guidance`, does not stop on repeated lifecycle contradictions, does not forbid writing specialist artifacts itself, or does not mark slash commands as human-only entrypoints
- result: the coordinator starts guessing at the state machine, authoring artifacts, or searching for workflow loopholes
- why agents miss it: the prompt looks authoritative, but it is missing the exact stop conditions and ownership boundaries that weaker models need

## Bootstrap-first guidance drift (WFLOW011 — bootstrap recovery is left to inference)

- bootstrap is `missing`, `failed`, or `stale`, but `ticket_lookup`, the team leader prompt, or the repo-local workflow skill do not make `environment_bootstrap` the first required action
- result: weaker coordinators keep attempting normal lifecycle moves, probing alternate stages, or treating environment failures as product defects before the repo can even validate code
- why agents miss it: each surface may contain a vague bootstrap hint, but none of them deterministically short-circuit the workflow when bootstrap is not ready

## Lease-ownership split (WFLOW012 — coordinator and specialists disagree about who claims tickets)

- workflow docs or prompts still mix coordinator-owned and worker-owned `ticket_claim` / `ticket_release` instructions
- result: the team leader and specialists can both think they should claim the same ticket, especially around planning and pre-bootstrap work
- why agents miss it: each surface looks locally plausible, but together they create a contradictory lease model that weaker agents cannot reconcile

## Resume truth-hierarchy drift (WFLOW013 — derived handoff text outranks canonical state)

- `/resume` or surrounding docs do not make `tickets/manifest.json` plus `.opencode/state/workflow-state.json` canonical, omit `.opencode/state/latest-handoff.md`, or let backlog reverification displace the active open ticket too early
- result: resumed sessions can follow stale restart text, ignore the current active lane, or treat historical reverification as a higher priority than current open work
- why agents miss it: the restart narrative feels authoritative unless the truth hierarchy is made explicit in every resume-facing surface

## Invocation-log coordinator artifact authorship (WFLOW014 — current repo evidence shows the wrong agent wrote stage proof)

- `.opencode/state/invocation-log.jsonl` shows the coordinator using `artifact_write` for planning, implementation, review, QA, or smoke-test artifacts
- result: current stage proof is suspect even if the artifact body itself looks plausible, because the routing agent bypassed the owning specialist or deterministic tool
- why agents miss it: transcript-based checks can miss the current repo-local invocation history unless audit inspects the structured log directly

## Smoke-test override execution defect (WFLOW016 — explicit smoke override fails before the command starts)

- the generated `smoke_test` tool passes `command_override` directly into `spawn()` argv, fails to parse one-item shell-style commands, mis-parses multiple shell-style override strings, or treats leading `KEY=VALUE` tokens as the executable name instead of environment overrides
- result: valid explicit smoke-test commands fail with `ENOENT` or similar launch errors before the requested verification command even starts, and the failure can be misreported as a generic environment issue
- why agents miss it: the transcript still looks like a failed smoke run unless audit inspects the tool contract and the launch error closely enough to see that the tool surface itself mis-executed the override

## Acceptance-command smoke drift (WFLOW017 — smoke-test scope ignores the ticket’s canonical acceptance command)

- the generated `smoke_test` tool does not inspect ticket acceptance criteria for explicit smoke commands, and instead falls back to generic repo-level pytest detection or caller-supplied `test_paths`
- result: the smoke-test stage can widen to unrelated full-suite failures or narrow to an ad hoc subset that does not match the ticket’s real closeout requirement
- why agents miss it: the smoke artifact still contains a legitimate test command, so shallow audit reduces the problem to “tests failed” instead of noticing that the tool ran the wrong smoke scope

## Closed-ticket remediation deadlock (WFLOW018 — completed-ticket follow-up still requires a normal write lease)

- `ticket_create(process_verification|post_completion_issue)` or `issue_intake` expects completed historical source tickets, but the stage-gate still requires the source ticket's normal write lease
- result: post-completion remediation or backlog-verification routing becomes mechanically impossible on closed tickets even when current evidence exists
- why agents miss it: the tool docs describe a legal route, but the plugin still applies ordinary active-ticket lease rules underneath it

## Stale ticket-graph contradiction (WFLOW019 — source/follow-up lineage no longer matches current dependencies)

- a follow-up ticket both names a `source_ticket_id` and depends on that same source, references a missing source, or its parent no longer lists it in `follow_up_ticket_ids`
- result: weaker models get trapped between contradictory queue state and current evidence because no canonical reconciliation path exists
- why agents miss it: each ticket can look locally plausible while the graph as a whole is stale or contradictory

## Open-parent split drift (WFLOW020 — child decomposition from open tickets lacks a canonical source mode)

- a child ticket extends an open or reopened parent ticket, but the repo lacks `split_scope` support, the child is still routed as `net_new_scope` / `post_completion_issue`, or the parent is still marked `blocked` after the split
- result: planned decomposition from active parent scope drifts into remediation semantics and later produces stale dependencies or follow-up graphs
- why agents miss it: the queue still shows parent and child tickets, but the contract does not distinguish open-parent splitting from historical remediation

## Historical reconciliation deadlock (WFLOW024 — superseded invalidated history has no legal path forward)

- a completed ticket is both `resolution_state == superseded` and `verification_state == invalidated`, but `ticket_reconcile`, `ticket_create(post_completion_issue)`, `issue_intake`, or closeout publication still require evidence or state that no longer exists on the historical source ticket
- result: the repo can truthfully recognize that a historical ticket was superseded, yet still strand the operator with no legal path to reconcile the queue, publish handoff, or move the workflow forward
- why agents miss it: the queue state looks internally descriptive, but the tool contract still assumes direct historical artifacts or pre-supersede evidence ownership that the reconciled ticket no longer has

## Legacy repair-gate leak (WFLOW021 — prompts or restart surfaces still reason from `handoff_allowed`)

- generated prompts, `/resume`, `START-HERE.md`, `.opencode/state/context-snapshot.md`, or `.opencode/state/latest-handoff.md` still tell agents to reason from `repair_follow_on.handoff_allowed`, `repair_follow_on_handoff_allowed`, or a rendered `handoff_allowed` bullet
- result: weaker models keep treating an old boolean gate as authoritative even though `repair_follow_on.outcome` is now the canonical repair-state contract
- why agents miss it: the restart surface still looks internally consistent, so they keep following the stale boolean instead of the newer outcome model

## Closeout lease contradiction (WFLOW022 — restart publication still needs an open-ticket lease)

- the transcript shows `handoff_publish` or equivalent restart-surface publication failing with `missing_ticket_write_lease` after the ticket is already closed
- result: the workflow has no legal way to publish truthful restart surfaces at closeout time
- why agents miss it: the surface failure can look like a one-off tool error unless audit treats closeout publication as a distinct contract from ordinary open-ticket lane mutation

## Acceptance-scope contamination (WFLOW023 — the ticket’s literal closeout command reaches into later-ticket work)

- a ticket’s acceptance says a command must exit 0, but the same transcript shows that command still fails on later-ticket or sibling-ticket scope that the current ticket explicitly does not own
- result: the coordinator is forced to choose between violating scope, falsifying acceptance, or stalling on a contradiction that should have been prevented during ticket generation
- why agents miss it: the acceptance command looks concrete and executable, so shallow review treats it as good ticket hygiene instead of noticing that the command is broader than the ticket’s owned scope

## Thin workflow explainer (SKILL002 — repo-local `ticket-execution` skill omits key lifecycle mechanics)

- the generated `ticket-execution` skill does not explain transition guidance, contradiction-stop behavior, smoke-test ownership, blocker behavior, or command boundaries
- result: agents have to reverse-engineer the lifecycle from tool errors instead of reading one canonical local procedure
- why agents miss it: the skill exists, so a surface-level audit may assume the workflow explainer is present even when it carries only thin boilerplate

## Missing Blender route operating surfaces (SKILL003 — Blender-required repos lack mandatory agent/skill contract surfaces)

- asset-pipeline metadata says Blender-MCP is required, but the repo-local skill pack or agent pack is missing required Blender route surfaces such as `asset-description`, `blender-mcp-workflow`, or a `blender-asset-creator`
- result: the repo advertises a Blender asset route that weaker models cannot actually execute
- why agents miss it: the MCP entry may exist in config, so shallow review assumes the Blender route is usable even when the surrounding managed surfaces were never fully materialized

## Session chronology miss (SESSION001 — current-state-only audit misses later reasoning failure)

- a supplied transcript shows stale early-session context, later corrective evidence, and a final summary that still overstates readiness or root cause
- result: the audit answers the wrong question unless it treats chronology as first-class evidence
- why agents miss it: current audits prioritize present repo state and only secondarily inspect historical session order

## Workflow thrash loop (SESSION002 — repeated lifecycle rejection with no new evidence)

- the transcript shows the same `ticket_update` blocker firing multiple times
- result: the session burns time and tokens retrying the same rejected transition instead of resolving the contract contradiction
- why agents miss it: current audits may note the blocker itself but not the repeated, unproductive retries that reveal a prompt or workflow-explainer gap

## Workflow bypass search (SESSION003 — unsupported stage or workaround probing)

- the transcript shows attempts like `stage=todo`, direct jumps to later stages, or explicit "workaround" language
- result: the agent is no longer following the lifecycle contract and is searching for whatever the tool layer will accept
- why agents miss it: current audits may treat stale JSON inside tool output as if it were the coordinator's own reasoning, or they may treat the transcript as implementation progress instead of evidence of state-machine confusion

## Evidence-free PASS claims (SESSION004 — validation failure followed by PASS artifacts or summaries)

- the transcript says verification commands could not run, but later artifacts or summaries still claim PASS or "verified by running"
- result: the repo can accumulate implementation, QA, or smoke-test proof that is not backed by executed commands
- why agents miss it: current audits may inspect the final artifacts without reconciling them against the earlier failure chronology in the same session, or they may ignore later real recovery evidence and overstate the problem

## Coordinator-authored specialist artifacts (SESSION005 — team leader writes stage proof directly)

- the transcript shows the coordinator using `artifact_write` to create planning, implementation, review, QA, or smoke-test artifacts directly
- result: ticket proof is shaped by the routing agent instead of the owning specialist lane or deterministic tool
- why agents miss it: current audits may focus on the artifact content and overlook that the wrong agent authored the stage evidence in the first place

## No-legal-next-move trap (SESSION006 — the operator is left to infer how to proceed)

- the transcript contains multiple contradictory blockers at once: lifecycle rejections, closeout lease contradictions, acceptance-scope tension, or deterministic tool failures
- result: the operator keeps reasoning about workarounds because the workflow does not expose one competent legal next move
- why agents miss it: individual findings are often recorded separately, so nobody states the higher-level truth that the workflow itself stopped being navigable

## Broken helper tool surface (WFLOW015 — internal workflow helpers exposed as callable tools)

- the transcript shows a `_workflow_*` helper call or similar internal helper call failing with `def.execute is not a function` or another missing-handler runtime error
- result: the coordinator can select a non-executable helper instead of a real tool, so the workflow fails before normal transition guidance or deterministic routing can even run
- why agents miss it: transcript parsers often capture only tool name and input args, discard `Error` blocks, and never distinguish internal helper exports from real executable `tool({...})` modules

## Execution blindness (EXEC001 — module import failure)

- one or more Python packages fail to import at runtime due to errors invisible to static analysis
- common causes: TYPE_CHECKING-guarded names used as unquoted runtime annotations (`-> ServiceType:` instead of `-> "ServiceType":`), FastAPI dependency functions parameterised with non-Pydantic types (e.g. `app: FastAPI` instead of `request: Request`), circular imports
- result: the hub or node agent cannot start; all 25+ MCP tools are blocked regardless of how much implementation code exists; tickets can reach `closeout/done` without the service ever being run
- why agents miss it: each ticket is implemented in isolation; no integration step imports the full module chain; the QA agent accepted "code exists and looks correct" as sufficient proof

## Test collection blocked (EXEC002 — pytest collection error)

- one or more test files import a broken module, causing pytest to abort collection before any test runs
- result: the test suite cannot execute at all; QA artifacts that claim tests passed were never actually run
- why agents miss it: agents ran `pytest` on individual files or checked exit codes without reading stderr; collection errors exit with code 2 not 1, and may have been misread as "tests ran but failed"

## Test suite failures (EXEC003 — tests ran but some failed)

- pytest collected and ran tests but one or more failed
- result: implementation is incomplete or regressed; closeout evidence is invalid
- why agents miss it: QA artifacts recorded "validation complete" without including raw pytest output; the team leader accepted thin QA artifacts without requiring pass/fail counts with command output

## "Acceptable Wave N Scaffolding" bypass (PROC001 — placeholder behavior approved without a follow-on ticket)

- a review, QA, coordinator, or handoff artifact uses framing such as "acceptable Wave N scaffolding", "placeholder for now to be replaced later", "will be addressed in a future wave", or similar to justify approving stub implementations in product-spine code
- the framing is used without a specific, named, currently-open follow-on ticket that owns the stub replacement
- result: placeholder behavior accrues legitimate-looking proof artifacts and reaches `done` without ever being implemented; the wave framing has no contractual basis in Scafforge's review contract
- why agents miss it: audits inspect whether proof exists for a ticket, not whether the proof was manufactured via compliant-sounding framing that has no contract backing; weak models generating review artifacts pattern-match to "acceptable" language instead of checking whether a stub-replacement ticket exists
