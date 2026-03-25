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
