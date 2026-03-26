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

## Restart-surface drift (WFLOW010 — derived restart files contradict canonical state)

- `START-HERE.md` or `.opencode/state/context-snapshot.md` disagrees with `tickets/manifest.json` or `.opencode/state/workflow-state.json` about the active ticket, bootstrap status, proof artifact, pending process verification, state revision, or lane-lease presence
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

## Thin workflow explainer (SKILL002 — repo-local `ticket-execution` skill omits key lifecycle mechanics)

- the generated `ticket-execution` skill does not explain transition guidance, contradiction-stop behavior, smoke-test ownership, blocker behavior, or command boundaries
- result: agents have to reverse-engineer the lifecycle from tool errors instead of reading one canonical local procedure
- why agents miss it: the skill exists, so a surface-level audit may assume the workflow explainer is present even when it carries only thin boilerplate

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
- why agents miss it: current audits may treat the transcript as implementation progress instead of as evidence of state-machine confusion

## Evidence-free PASS claims (SESSION004 — validation failure followed by PASS artifacts or summaries)

- the transcript says verification commands could not run, but later artifacts or summaries still claim PASS or "verified by running"
- result: the repo can accumulate implementation, QA, or smoke-test proof that is not backed by executed commands
- why agents miss it: current audits may inspect the final artifacts without reconciling them against the earlier failure chronology in the same session, or they may ignore later real recovery evidence and overstate the problem

## Coordinator-authored specialist artifacts (SESSION005 — team leader writes stage proof directly)

- the transcript shows the coordinator using `artifact_write` to create planning, implementation, review, QA, or smoke-test artifacts directly
- result: ticket proof is shaped by the routing agent instead of the owning specialist lane or deterministic tool
- why agents miss it: current audits may focus on the artifact content and overlook that the wrong agent authored the stage evidence in the first place

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
