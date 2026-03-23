# Scafforge Review Package: Plan Comparison, OpenCode Alignment, and Weak-Agent Failure Analysis

## Scope

This review compares Scafforge's current scaffold/runtime behavior against:

- [SCAFFORGE-REMEDIATION-PLAN.md](./SCAFFORGE-REMEDIATION-PLAN.md)
- [SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md)
- Current Scafforge scaffold/runtime surfaces:
  [\_workflow.ts](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts),
  [stage-gate-enforcer.ts](../skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts),
  [artifact_register.ts](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/artifact_register.ts),
  [handoff_publish.ts](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts),
  [opencode.jsonc](../skills/repo-scaffold-factory/assets/project-template/opencode.jsonc),
  [apply_repo_process_repair.py](../skills/repo-process-doctor/scripts/apply_repo_process_repair.py),
  [validate_scafforge_contract.py](../scripts/validate_scafforge_contract.py),
  [smoke_test_scafforge.py](../scripts/smoke_test_scafforge.py)
- Current OpenCode docs:
  [Config](https://opencode.ai/docs/config/),
  [Permissions](https://opencode.ai/docs/permissions/),
  [Plugins](https://opencode.ai/docs/plugins/),
  [Custom Tools](https://opencode.ai/docs/custom-tools/),
  [Agents](https://opencode.ai/docs/agents/),
  [Commands](https://opencode.ai/docs/commands/),
  [Rules](https://opencode.ai/docs/rules),
  [Skills](https://opencode.ai/docs/skills),
  [Modes](https://opencode.ai/docs/modes/)

The review assumes smaller or weaker OpenCode agents will follow visible affordances, optimize for the nearest pass condition, and exploit unguarded workflow tools long before they reason carefully about prose guidance.

## Verification Run

- `python scripts/validate_scafforge_contract.py` passed.
- `python scripts/smoke_test_scafforge.py` passed.

That matters because several of the highest-risk issues below are not "missing file" failures. They are false-confidence failures that survive the current validator and smoke test.

## Findings

### 1. [High] False completion is still possible because workflow truth can be mutated outside the stage gate

- Current code:
  [stage-gate-enforcer.ts#L31](../skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts#L31) only intercepts `bash`, `write`/`edit`, and `ticket_update`.
  [artifact_register.ts#L14](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/artifact_register.ts#L14) directly appends ticket and registry entries after only checking canonical path and file existence.
  [handoff_publish.ts#L20](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts#L20) publishes `START-HERE.md` without any explicit stage-proof or completion guard.
- OpenCode baseline:
  [Plugins](https://opencode.ai/docs/plugins/) documents `tool.execute.before` and `tool.execute.after` as first-class enforcement hooks.
  [Custom Tools](https://opencode.ai/docs/custom-tools/) says custom tools can override or replace built-in tool behavior.
- Weak-agent failure path:
  a weaker agent does not need to beat the `ticket_update` gate if it can write an artifact, register it, and publish a handoff surface that looks finished.
- Plan comparison:
  [SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L54](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L54) identifies this directly and is correct.
  [SCAFFORGE-REMEDIATION-PLAN.md#L73](./SCAFFORGE-REMEDIATION-PLAN.md#L73) reaches the same problem via stronger proof and broader validator work, but does not isolate "all workflow-mutating tools" as its own enforcement surface.
- Overlap status:
  `same problem, different mechanism`
- Missing decision before implementation:
  the later implementation plan must define the canonical list of workflow-truth mutators and name the single enforcement point for each one.

### 2. [High] Proof is still heuristic, markdown-first, and easy for weaker agents to satisfy cosmetically

- Current code:
  [\_workflow.ts#L529](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L529) treats execution evidence as regex hits.
  [\_workflow.ts#L555](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L555) and [\_workflow.ts#L573](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L573) add byte-length gates.
  [\_workflow.ts#L579](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L579) looks for `Overall Result: PASS`.
  [artifact_register.ts#L29](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/artifact_register.ts#L29) records artifacts without schema validation, contradiction checks, or command/result integrity.
- OpenCode baseline:
  [Custom Tools](https://opencode.ai/docs/custom-tools/) exposes structured argument validation through `tool.schema` / Zod. That does not force Scafforge to use JSON artifacts, but it means the platform is designed for machine-validated contracts rather than regex-only proof.
- Weak-agent failure path:
  a weaker agent can produce a long markdown artifact with command-looking text and a PASS marker, then rely on the gate to treat appearance as proof.
- Plan comparison:
  [SCAFFORGE-REMEDIATION-PLAN.md#L73](./SCAFFORGE-REMEDIATION-PLAN.md#L73) and [SCAFFORGE-REMEDIATION-PLAN.md#L79](./SCAFFORGE-REMEDIATION-PLAN.md#L79) propose stricter executable proof and structured artifact schemas.
  [SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L29](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L29) proposes the same core change from the "structured proof" angle.
- Overlap status:
  `same change`
- Missing decision before implementation:
  the later implementation plan must choose the artifact contract format and precedence:
  frontmatter in markdown,
  JSON sidecar,
  pure JSON,
  or a mixed design with one canonical machine-readable source.

### 3. [High] State mutation is plain read/modify/write file IO, so the transactional/concurrency problem is real and not covered by the remediation plan in enough detail

- Current code:
  [\_workflow.ts#L202](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L202) and [\_workflow.ts#L222](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L222) do direct JSON reads and writes.
  [\_workflow.ts#L402](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L402) and [\_workflow.ts#L410](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L410) persist manifest and registry independently.
- OpenCode baseline:
  [Permissions](https://opencode.ai/docs/permissions/) and [Agents](https://opencode.ai/docs/agents/) are permissive by default and support subagents, which makes parallel mutation a realistic operating mode rather than an edge case.
  [Config](https://opencode.ai/docs/config/) also documents layered project-local configuration, which reinforces that Scafforge is expected to live inside a mutable repo-local runtime, not a serialized control plane.
- Weak-agent failure path:
  two agents can each appear to comply locally while racing on manifest, artifact registry, or workflow state and producing an incoherent but plausible workflow story.
- Plan comparison:
  [SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L43](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L43) calls this out directly and correctly.
  [SCAFFORGE-REMEDIATION-PLAN.md#L103](./SCAFFORGE-REMEDIATION-PLAN.md#L103) touches registry integrity, but not the underlying transaction model clearly enough.
- Overlap status:
  `distinct but dependent`
- Missing decision before implementation:
  the later implementation plan must explicitly choose the state model:
  atomic file-replacement with version checks,
  append-only event log plus derivation,
  SQLite,
  or another transactional store.

### 4. [High] The generated restart surface still ships placeholders and can overclaim trust because it is not truly derived-only

- Current code:
  [\_workflow.ts#L703](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L703) renders `START-HERE.md` with literal placeholder text for validation results and known risks.
  [handoff_publish.ts#L31](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts#L31) publishes that surface from current state, but does not verify that the state is itself trustworthy.
  [apply_repo_process_repair.py#L68](../skills/repo-process-doctor/scripts/apply_repo_process_repair.py#L68) and [apply_repo_process_repair.py#L301](../skills/repo-process-doctor/scripts/apply_repo_process_repair.py#L301) merge the managed block rather than replacing the entire surface with one canonical derivation path.
- OpenCode baseline:
  [Rules](https://opencode.ai/docs/rules) says `AGENTS.md` content is included in model context, which is useful guidance but not enforcement.
  For weaker agents, a top-level `START-HERE.md` is a dominant affordance, so any placeholder or overclaim there is more dangerous than similar text buried in a skill.
- Weak-agent failure path:
  the agent treats the top restart surface as authoritative, trusts stale or placeholder validation sections, and continues from a false status baseline.
- Plan comparison:
  [SCAFFORGE-REMEDIATION-PLAN.md#L98](./SCAFFORGE-REMEDIATION-PLAN.md#L98) is right that `START-HERE.md` must become derived-only.
  [SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L51](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L51) correctly broadens that into "derived surfaces from source state, never writable truth."
- Overlap status:
  `same problem, different mechanism`
- Missing decision before implementation:
  the later implementation plan must define which fields are derivable from canonical state and which, if any, are allowed as operator-authored annotations.

### 5. [Medium] The current validator and smoke test are meaningful, but they still validate conformance more than adversarial behavior

- Current code:
  [validate_scafforge_contract.py#L75](../scripts/validate_scafforge_contract.py#L75) through [validate_scafforge_contract.py#L170](../scripts/validate_scafforge_contract.py#L170) mainly checks required files, required strings, manifest shape, and disallowed text.
  [smoke_test_scafforge.py#L23](../scripts/smoke_test_scafforge.py#L23) through [smoke_test_scafforge.py#L136](../scripts/smoke_test_scafforge.py#L136) verifies template render and repair round-trip, but does not intentionally attempt fake proof, future-stage artifacts, illegal handoff publication, or concurrent updates.
- OpenCode baseline:
  [Permissions](https://opencode.ai/docs/permissions/) is permissive by default, and [Commands](https://opencode.ai/docs/commands/) plus [Agents](https://opencode.ai/docs/agents/) make subagent routing and parallel execution first-class. Scafforge therefore needs adversarial behavior tests, not only happy-path generation tests.
- Weak-agent failure path:
  a weak agent fails in exactly the ways the current test harness does not simulate, so the scaffold can pass release checks while still being easy to game.
- Plan comparison:
  [SCAFFORGE-REMEDIATION-PLAN.md#L84](./SCAFFORGE-REMEDIATION-PLAN.md#L84) and [SCAFFORGE-REMEDIATION-PLAN.md#L93](./SCAFFORGE-REMEDIATION-PLAN.md#L93) are correct about self-tests and contract verification.
  [SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L86](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L86) is more specific about adversarial and concurrency scenarios.
- Overlap status:
  `distinct but dependent`
- Missing decision before implementation:
  the later implementation plan must define the behavioral test matrix, including which scenarios are unit-tested at tool level and which are tested against a generated repo end to end.

### 6. [Medium] Repair is still deterministic replacement, not a declared managed-merge contract

- Current code:
  [apply_repo_process_repair.py#L168](../skills/repo-process-doctor/scripts/apply_repo_process_repair.py#L168) and [apply_repo_process_repair.py#L174](../skills/repo-process-doctor/scripts/apply_repo_process_repair.py#L174) implement whole-file and whole-directory replacement.
  [apply_repo_process_repair.py#L278](../skills/repo-process-doctor/scripts/apply_repo_process_repair.py#L278) through [apply_repo_process_repair.py#L301](../skills/repo-process-doctor/scripts/apply_repo_process_repair.py#L301) replace `opencode.jsonc`, `.opencode/tools`, `.opencode/plugins`, `.opencode/commands`, managed skills, and process docs, then merge the `START-HERE` managed block.
- OpenCode baseline:
  [Config](https://opencode.ai/docs/config/) and [Plugins](https://opencode.ai/docs/plugins/) make repo-local customization normal. That means Scafforge repair has to distinguish "managed authoritative replacement" from "local extension point" deliberately, not implicitly.
- Weak-agent failure path:
  stronger host agents will customize generated repos; later repair can silently flatten those changes or preserve the wrong ones, and weaker follow-up agents will trust the repaired state as canonical.
- Plan comparison:
  [SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L61](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L61) identifies this clearly.
  [SCAFFORGE-REMEDIATION-PLAN.md#L108](./SCAFFORGE-REMEDIATION-PLAN.md#L108) hints at reducing duplicate authority, but not at merge semantics with enough specificity.
- Overlap status:
  `distinct but dependent`
- Missing decision before implementation:
  the later implementation plan must define managed-surface categories:
  replace,
  merge,
  derive,
  or conflict-and-stop.

### 7. [Medium] "OpenCode alignment" is real, but both plans are too broad in that section and need to be broken into concrete compatibility checks

- Current code:
  [opencode.jsonc#L1](../skills/repo-scaffold-factory/assets/project-template/opencode.jsonc#L1) already uses `permission`, which matches current OpenCode docs better than older `tools` gating.
  But [opencode.jsonc#L13](../skills/repo-scaffold-factory/assets/project-template/opencode.jsonc#L13) also disables `browser_research`, `project_github`, and `openai_docs` by default, and the broader workflow still assumes a heavier process layer than OpenCode itself provides natively.
- OpenCode baseline:
  [Config](https://opencode.ai/docs/config/) documents precedence across remote, global, custom, project, `.opencode`, and inline sources.
  [Permissions](https://opencode.ai/docs/permissions/) says legacy `tools` booleans are deprecated in favor of `permission`.
  [Modes](https://opencode.ai/docs/modes/) currently contains transition-era wording around `mode`, while [Agents](https://opencode.ai/docs/agents/) still documents `mode` and `permission.task`. The docs are usable, but not perfectly uniform.
- Weak-agent failure path:
  if Scafforge treats "OpenCode alignment" as one abstract clean-up item, the later implementation can easily miss concrete runtime semantics like precedence, pattern matching, subagent permissions, or plugin load order.
- Plan comparison:
  [SCAFFORGE-REMEDIATION-PLAN.md#L68](./SCAFFORGE-REMEDIATION-PLAN.md#L68) addresses disabled integrations and misleading availability.
  [SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L71](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L71) addresses broader OpenCode-model alignment.
- Overlap status:
  `distinct but dependent`
- Missing decision before implementation:
  the later implementation plan must split OpenCode alignment into explicit sub-workstreams:
  config precedence,
  permissions semantics,
  plugin interception strategy,
  custom tool ownership,
  agent/subagent invocation model,
  and default integration posture.

## Overlap Matrix

| Theme | Current state | Remediation plan | Permissive guardrails plan | Overlap result |
| --- | --- | --- | --- | --- |
| Structured proof | Regex and size heuristics in [\_workflow.ts#L529](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts#L529) | [#L73](./SCAFFORGE-REMEDIATION-PLAN.md#L73) and [#L79](./SCAFFORGE-REMEDIATION-PLAN.md#L79) | [#L29](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L29) | Same change |
| Stage-gate coverage across mutating tools | Plugin gates only `bash`, `write`/`edit`, `ticket_update` | Implicit via stricter proof and validator work | Explicit in [#L54](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L54) | Same problem, different mechanism |
| Dynamic and adversarial validation | Static validator plus happy-path smoke test | [#L84](./SCAFFORGE-REMEDIATION-PLAN.md#L84) and [#L93](./SCAFFORGE-REMEDIATION-PLAN.md#L93) | [#L86](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L86) | Distinct but dependent |
| Derived restart and handoff surfaces | Placeholder-backed `START-HERE` plus managed-block merge | [#L98](./SCAFFORGE-REMEDIATION-PLAN.md#L98) | [#L51](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L51) | Same problem, different mechanism |
| Registry invariants and chronology | Registry is append/replace by path only | [#L103](./SCAFFORGE-REMEDIATION-PLAN.md#L103) | [#L54](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L54) | Same problem, different mechanism |
| Duplicate authority surfaces | Still possible across restart/process surfaces | [#L108](./SCAFFORGE-REMEDIATION-PLAN.md#L108) | Implicit via derived-state and merge work | Distinct but dependent |
| Disabled integrations and config drift | MCP integrations disabled by default in template | [#L68](./SCAFFORGE-REMEDIATION-PLAN.md#L68) | Included in [#L71](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L71) | Distinct but dependent |
| Transactional state and concurrency | Plain file IO with no transaction model | Only partial coverage | [#L43](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L43) | Distinct and necessary |
| Repair and managed merge behavior | Deterministic replacement, partial merge only | Mostly indirect | [#L61](./SCAFFORGE-PERMISSIVE-GUARDRAILS-PLAN.md#L61) | Distinct and necessary |
| OpenCode model alignment | Real issue, but docs/runtime need more precise mapping | Partial | Partial | Conflict if left too vague |

## Decision On Plan Overlap

The two plans are not identical, but they substantially overlap and should be collapsed into one implementation program with separate workstreams.

They are not "just saying the same thing" in every section:

- The remediation plan is stronger on scaffold hygiene, disabled-by-default integrations, validator expansion, and converting GPTTalker lessons into release-gated policy.
- The permissive-guardrails plan is stronger on complete tool-surface enforcement, transactional state, concurrency, managed-merge repair, and expressing the fixes in OpenCode-native operational terms.

But they do overlap heavily on the core problem statement:

- false completion is possible
- proof semantics are too weak
- restart surfaces can overclaim
- current tests are too soft
- the process appears stricter than it really is

The right outcome is one consolidated implementation plan, not two competing plans.

## Are The Current Plans Step-By-Step Enough?

Not yet.

Both plans are directionally correct, but neither is decision-complete enough to hand directly to an implementer without more design work.

The main missing decisions are:

1. The canonical state model.
   Right now neither plan decides whether Scafforge should remain file-based with stronger atomic semantics or move to a transactional store.

2. The canonical artifact contract.
   Both plans ask for structured proof, but neither fully decides the durable wire shape or which surface is the source of truth when markdown and structured metadata disagree.

3. The complete list of workflow-truth mutators and their enforcement points.
   The plans say "close bypasses" without enumerating the authoritative mutation surfaces and naming how each one is intercepted.

4. The managed-surface repair contract.
   The plans do not yet specify which files are replace-only, which are mergeable, which are derived, and which should stop with conflicts.

5. The adversarial test matrix.
   The plans call for stronger tests, but they do not fully define the scenario set or the level at which each scenario is exercised.

6. The OpenCode compatibility boundary.
   "Align with OpenCode" is still too broad. It needs to be broken into tested claims about config precedence, permissions semantics, plugin load order, custom tool behavior, and subagent/task behavior.

## Recommended Structure For The Later Implementation Plan

The later implementation plan should be one document with these workstreams, in this order:

1. Truth and state contract
- Choose the canonical persistence model.
- Define ticket, workflow, artifact-registry, and derived-surface ownership boundaries.
- Define migration behavior from existing repos.

2. Enforcement surface closure
- Enumerate every workflow-truth mutator.
- Define the single enforcement point for each one.
- Define stage, ticket-ownership, and predecessor-proof invariants.

3. Structured artifact and proof contract
- Choose the machine-readable artifact format.
- Define required fields per stage.
- Define contradiction detection and registration failure rules.

4. Derived surfaces and repair semantics
- Make `START-HERE.md`, `BOARD.md`, and other restart/status surfaces derived-only where appropriate.
- Define replace, merge, derive, and conflict-and-stop categories for managed surfaces.

5. Validation harness
- Expand the validator into behavioral checks where necessary.
- Add adversarial generated-repo tests for fake proof, stage jumps, bad handoff publication, and concurrent mutation.

6. OpenCode compatibility pinning
- Convert "alignment" into explicit, tested claims against current OpenCode docs and current runtime assumptions.
- Keep any docs-transition ambiguity out of the implementation by pinning the intended behavior in tests.

## Bottom Line

The two plans should be merged, not kept separate.

The remediation plan and the permissive-guardrails plan are mostly describing the same recovery program from different angles, but the permissive-guardrails plan adds two genuinely necessary workstreams that the remediation plan does not specify well enough:

- transactional state and concurrency
- managed merge versus blunt repair replacement

The next implementation plan should therefore be a single consolidated plan that keeps the remediation plan's validator/hygiene/test rigor and the guardrails plan's enforcement/state/repair precision.

