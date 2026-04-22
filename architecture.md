# Scafforge Architecture

## Overview

Scafforge is a **meta-scaffold package** — it generates and maintains OpenCode-oriented repository operating frameworks. It is not a generated project; it is the generator, template source, orchestration engine, and process contract used by host agents to build, audit, and repair generated projects.

The core design goal is **weak-model reliability**: making cheaper or weaker AI models work reliably through deterministic workflow contracts, narrow role boundaries, explicit truth ownership, and proof-backed restart guidance.

Adjacent systems such as the spec factory, model router, orchestration service, and control plane stay outside the package core. They consume Scafforge contracts; they do not replace package authority.

## SDK Layering

Scafforge uses a hybrid layering decision rather than a rewrite-first approach:

- **OpenCode** remains the execution substrate for Scafforge-generated repos, package contracts, and downstream repo work.
- **AI SDK** belongs in adjacent services that need provider routing, provider failover, tool-loop agents, or service-side orchestration.
- **OpenAI Apps SDK** stays bounded to ChatGPT-facing ingress, review, and UI surfaces.
- The executable router contract stays in an adjacent service repo; Scafforge documents the policy boundary but does not embed router logic in package core.

## System Layers

```
┌─────────────────────────────────────────────┐
│      ADJACENT SERVICES / WORKSPACES          │
│  Spec factory, router, orchestration, UI     │
│  Consume package contracts without owning    │
│  Scafforge normalization or generation       │
├─────────────────────────────────────────────┤
│              HOST AGENT (Codex/Copilot)      │
│  Invokes Scafforge skills via prompts        │
├─────────────────────────────────────────────┤
│              SCAFFORGE PACKAGE               │
│  skills/ → 11 orchestrated skills            │
│  references/ → contracts and invariants      │
│  scripts/ → execution harness                │
│  tests/ → validation and proof               │
├─────────────────────────────────────────────┤
│              GENERATED REPO (Output Layer)   │
│  .opencode/ → agents, tools, plugins, state  │
│  tickets/ → manifest, board, ticket files    │
│  docs/ → canonical brief, process docs       │
├─────────────────────────────────────────────┤
│              DOWNSTREAM AGENT (OpenCode)     │
│  Runs inside generated repo using .opencode  │
│  Follows ticket workflow, stage-gate plugin  │
└─────────────────────────────────────────────┘
```

## Skill Architecture

All skills live under `skills/`. The orchestration graph is defined in `skills/skill-flow-manifest.json`.

### Single Entrypoint

`scaffold-kickoff` is the only public entrypoint. It routes to one of 5 run types:

| Run Type | Purpose | Key Skills |
|----------|---------|------------|
| **greenfield** | New repo from scratch | spec-pack → scaffold-factory → skill-bootstrap → team-bootstrap → agent-prompt → ticket-builder → handoff |
| **retrofit** | Add Scafforge to existing repo | spec-pack? → team-bootstrap → skill-bootstrap → ticket-builder → audit → handoff |
| **managed-repair** | Fix workflow drift | repair → skill-bootstrap? → team-bootstrap? → agent-prompt? → ticket-builder? → handoff |
| **pivot** | Midstream design change | pivot → skill-bootstrap? → team-bootstrap? → agent-prompt? → ticket-builder? → repair? → handoff |
| **diagnosis-review** | Audit without edits | audit → handoff |

Approved spec-factory briefs are upstream intake artifacts, not alternate package entrypoints. They still pass through `spec-pack-normalizer` for validator-alignment before the normal greenfield sequence continues.

### Skill Dependency Graph

```
scaffold-kickoff (conductor)
  ├── spec-pack-normalizer (intake)
  │     └── repo-scaffold-factory (scaffold)
  │           ├── project-skill-bootstrap (local-skills)
  │           │     └── opencode-team-bootstrap (agent-team-design)
  │           │           └── agent-prompt-engineering (contract-alignment)
  │           │                 └── ticket-pack-builder (queue)
  │           │                       └── handoff-brief (restart-publication)
  │           └── scafforge-audit (diagnosis-disposition)
  │                 └── scafforge-repair (runtime-mutation)
  └── scafforge-pivot (pivot-state)
```

### Skill Internal Structure

Each skill follows a consistent layout:

```
skills/<skill-name>/
  SKILL.md          # Skill definition (prompt for host agent)
  scripts/          # Python automation scripts
  assets/           # Templates, reference files
```

## Generated Repo Structure

What Scafforge creates for a target repository:

```
<repo>/
  AGENTS.md                          # Operating rules
  START-HERE.md                      # Current-state restart surface
  README.md                          # Project overview
  opencode.jsonc                     # OpenCode configuration
  .opencode/
    agents/                          # Role-specific agent prompts
      <prefix>-team-leader.md        # Main orchestrator agent
      <prefix>-implementer.md        # Code writer
      <prefix>-planner.md            # Planning specialist
      <prefix>-tester-qa.md          # QA specialist
      <prefix>-reviewer-*.md         # Code/security reviewers
      <prefix>-lane-executor.md      # Parallel lane worker
      <prefix>-utility-*.md          # Utility agents
    tools/                           # TypeScript tool implementations
      ticket_read.ts                 # Read ticket state
      ticket_create.ts               # Create new tickets
      ticket_lifecycle.ts            # Advance ticket stages
      transition_guidance.ts         # Stage transition rules
      repair_follow_on_refresh.ts    # Repair follow-up management
    plugins/
      stage-gate-enforcer.ts         # CRITICAL: Runs before every tool call
    lib/
      workflow.ts                    # Core workflow state machine
    state/
      workflow-state.json            # Runtime workflow state
    meta/
      bootstrap-provenance.json      # Bootstrap configuration record
    skills/                          # Repo-local skills
    commands/                        # Slash commands
  tickets/
    manifest.json                    # Ticket index + state
    BOARD.md                         # Visual board
    <TICKET-ID>.md                   # Individual ticket files
  docs/
    spec/
      CANONICAL-BRIEF.md             # Project specification
    process/                         # Process documentation
```

## Key Contracts

### Adjacent spec-factory boundary

The spec factory is an adjacent workspace or service that owns:

- rough idea intake
- attachments and reference indexing
- drafting and decision packets
- review workflow and persisted human approval
- approved handoff bundle publication

Scafforge owns the downstream contract:

- `spec-pack-normalizer` validates an approved handoff bundle against the canonical brief contract
- `scaffold-kickoff` remains the single package entrypoint for generation
- the later orchestration layer, not the spec factory, decides when to invoke Scafforge

ChatGPT or MCP ingress is therefore transport and review only, not a hidden authority layer.

### Adjacent orchestration boundary

The adjacent orchestration service is the wrapper that sits between approved briefs, Scafforge generation, downstream PR phases, and pause or resume controls.

- It may invoke `scaffold-kickoff` once an approved-brief bundle is persisted and addressable.
- It owns job envelopes, idempotency or retry tokens, PR automation, reviewer assignment, and operator permission modes.
- It may read `docs/spec/CANONICAL-BRIEF.md`, `tickets/manifest.json`, `.opencode/state/workflow-state.json`, `START-HERE.md`, and `.opencode/meta/bootstrap-provenance.json`.
- It must stay read-only over generated canonical repo truth. Phase grouping, PR state, and `package-change-pending` remain orchestration-owned overlay state.
- It treats `scaffold-verified` as VERIFY009 persistence confirmation plus zero blocking VERIFY010 and VERIFY011 findings before downstream PR work begins.

### Adjacent model-router boundary

The model router is an adjacent service concern, even when it uses the AI SDK.

- Scafforge documents provider categories, fallback rules, and model-update policy.
- The executable router interface, provider credentials, and runtime selection logic belong in an adjacent service repo.
- The router may intentionally choose between native SDK lanes, AI SDK provider lanes, compatible-adapter lanes, and OpenCode execution lanes for the same model family.
- Provider, model-family, exact model ID, and transport-path evidence should be recorded in orchestration or service-side job records, not frozen into package docs as long-lived truth.

### Stage-Gate Enforcer (Plugin)

The most critical component in generated repos. It intercepts **every tool call** and enforces:

1. **Ticket lifecycle compliance** — tools can only be used if consistent with current ticket stage
2. **Managed-blocked enforcement** — when `managed_blocked` is active, only safe read/diagnostic tools are allowed
3. **Repair follow-on tracking** — pending repair follow-ons block normal work until resolved

If this plugin has a bug, **all tool calls in the downstream repo fail**.

### Workflow State Machine

`workflow.ts` manages the ticket lifecycle state:

```
planning → plan_review → implementation → review → qa → done
```

Key functions:
- `loadWorkflow()` / `saveWorkflow()` — state persistence
- `validateTicketGraph()` — dependency validation
- `hasPendingRepairFollowOn()` — repair state check
- `isAllowedFollowOnTicket()` — ticket creation rules

### Bootstrap Provenance

`.opencode/meta/bootstrap-provenance.json` records the scaffold configuration:
- runtime model selections (provider category, tier, and exact model IDs chosen for that run)
- stack label, project identifiers
- product finish contract
- Scafforge version

This is runtime provenance, not package policy. Repair uses it to reconstruct the correct template rendering context for the exact run that created the repo.

## Repair Flow

```
1. run_managed_repair.py
   ├── Copy repo to temp dir (excluding .git, .venv*, node_modules)
   ├── apply_repo_process_repair.py
   │   ├── Load metadata from bootstrap-provenance.json
   │   ├── Render fresh template with correct placeholders
   │   ├── Diff-replace managed surfaces
   │   └── Normalize pivot state if needed
   ├── Copy temp back to repo
   ├── Run verification
   └── Create remediation follow-up tickets if needed
```

## Audit Flow

```
1. audit_repo_process.py
   ├── Structural checks (files, directories)
   ├── Workflow state validation
   ├── Config surface checks (CONFIG001-005)
   ├── Template drift detection
   └── Emit diagnosis pack with disposition bundle
```

## Model Configuration

- Template placeholder: `__FULL_PLANNER_MODEL__` renders as `provider/model`
- Durable package docs should describe model families, provider categories, and routing rules rather than hard-code volatile model IDs
- Exact model IDs belong in adjacent service config, environment-specific settings, explicit fixtures, or runtime provenance for a concrete scaffold run
- Provenance may store full `provider/model` strings for an actual run
- Repair strips provider prefix before re-rendering to avoid doubling

## Execution Harness

`scripts/run_agent.sh` provides three modes:
- **opencode** (default): Runs headless opencode agent for ticket work
- **--audit**: Runs codex with scafforge-audit skill
- **--repair**: Runs codex with scafforge-repair skill

All modes use `< /dev/null` to prevent stdin EBADF errors.

## Smoke Test Tool

The smoke_test tool (`tools/smoke_test.ts`) handles command detection, execution, failure classification, artifact generation, and orchestration.

### Key behaviors

- **`smoke_deferred_until`**: When a ticket's acceptance smoke test requires functionality from a later ticket, use `smoke_deferred_until: [ticket_ids]`. The tool emits a DEFERRED artifact and leaves the ticket at `smoke-test` stage. Normal smoke execution is skipped until all listed tickets are `done`. This is the correct escape hatch for circular smoke dependencies — use it instead of `command_override` scope-narrowing.
- **`command_override` scope constraint**: If `command_override` is supplied but acceptance criteria reference executables not covered by the override, the tool throws a configuration error and returns FAIL. Use `smoke_deferred_until` when the dependency is genuinely a later ticket; fix acceptance criteria via `ticket_update` when the acceptance scope is wrong.
- **DEFERRED state in workflow**: `workflow.ts` recognizes DEFERRED smoke artifacts. `validateSmokeTestArtifactEvidence()` returns an actionable message for DEFERRED (blocks closeout, gives clear recovery path). Handoff-publish also blocks on DEFERRED. `ticket_lookup` routes DEFERRED to `work_other_tickets` with `next_action_tool: null`.

### Decomposition note

The module conflates several responsibilities (command detection, execution, failure classification, artifact generation). The architecture is functional but would benefit from separation into: CommandDetector, CommandExecutor, FailureClassifier, ArtifactGenerator, and SmokeTestOrchestrator layers.

## Asset Pipeline

Extends Scafforge with game/creative asset support via explicit source routes plus required pipeline stages:

| Capability | Kind | Example |
|-------|--------|---------|
| `source-open-curated` | curated open sourcing | Kenney sprites, Quaternius props, Google Fonts |
| `source-mixed-license` | sourced assets with attribution or commercial-policy review | OpenGameArt audio, Freesound clips |
| `procedural-2d` / `procedural-layout` / `procedural-world` | repo-authored deterministic generation | shaders, particles, TileMap/WFC, terrain noise |
| `local-ai-2d` / `local-ai-audio` | local/open AI generation | pinned local image or audio workflows |
| `reconstruct-3d` / `dcc-assembly` | reconstruction, DCC cleanup, and Blender export | low-poly GLB props, reconstructed meshes |

All routes require machine-checkable provenance and QA. Managed game repos also carry machine-readable asset truth and starter capture surfaces:
- `assets/requirements.json`
- `assets/pipeline.json`
- `assets/manifest.json`
- `assets/ATTRIBUTION.md`
- `assets/PROVENANCE.md`
- `.opencode/meta/asset-pipeline-bootstrap.json`
- `.opencode/meta/asset-provenance-lock.json`
- `assets/workflows/`
- `assets/previews/`
- `assets/workfiles/`
- `assets/licenses/`
- `assets/qa/import-report.json`
- `assets/qa/license-report.json`

`opencode.jsonc` must enable `blender_agent` only when the current route map requires `dcc-assembly` and the current host exposes the Blender MCP prerequisites.

## Testing

- `tests/` contains validation harnesses
- Active audit collections under `active-audits/`
- Agent runner logs under `reports/agent-runs/`

## Key Invariants

1. **Package ≠ Output**: Never import generated-repo surfaces into the package root
2. **Template is truth**: All managed surfaces in generated repos derive from templates
3. **Provenance round-trip**: Repair must recover scaffold context from provenance, not defaults
4. **Idempotent repair**: Running repair twice must not crash or corrupt state
5. **Stage-gate never crashes**: Plugin errors kill all downstream tool calls
6. **Smoke all, not fail-fast**: Smoke tests should run all commands before classifying
7. **Asset provenance**: Every external asset must have a PROVENANCE.md entry
