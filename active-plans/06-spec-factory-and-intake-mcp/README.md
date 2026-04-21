# Spec Factory And Intake MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Create a separate idea-to-spec system that can accept rough concepts, attachments, and prompts, turn them into Scafforge-ready brief material, and hand off approved outputs without weakening package boundaries.

**Architecture:** Build the spec factory as an adjacent workspace or service, not as hidden package logic. It owns intake, enrichment, drafting, decision packets, and approval state. Scafforge still owns normalization against its canonical brief contract and the actual greenfield scaffold. ChatGPT/MCP ingress should feed the factory through a reviewed workflow, not bypass it.

**Tech Stack / Surfaces:** adjacent spec-factory workspace or repo, MCP server, ChatGPT-facing app surface, package contract references, `spec-pack-normalizer`, `scaffold-kickoff`.
**Depends On:** `09-sdk-model-router-and-provider-strategy` should land before implementation, but contract design can begin now.
**Unblocks:** `07-autonomous-downstream-orchestration`, parts of the WinUI control plane, and user-facing idea intake.
**Primary Sources:** `_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`, `_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`, `skills/spec-pack-normalizer/references/brief-schema.md`, `chatgpt-apps` guidance, current Apps SDK docs and MCP/App patterns.

---

## Problem statement

The “Spec Maker Workspace” currently exists as a concept, not an implementation contract. Without a defined state model and ownership boundary, idea intake will drift into one of two bad outcomes:

- raw ideas bypass review and become pseudo-specs
- the spec factory silently duplicates or mutates Scafforge’s canonical normalization logic

This plan exists to prevent both.

## Required deliverables

- a state machine for the spec factory
- an input object model for rough ideas, attachments, and references
- a clearly defined approved-output contract aligned to Scafforge’s canonical brief expectations
- a ChatGPT/MCP ingress design that still routes through review states
- package docs that explain where the factory ends and Scafforge begins

## Proposed factory state model

The factory should converge on an explicit workflow such as:

`inbox -> triage -> drafting -> decision-needed -> review -> approved -> handed-off`

Optional side states:

- `rejected`
- `needs-more-input`
- `superseded`

The critical rule is that `approved` is the only state allowed to trigger Scafforge generation.

## Package and adjacent surfaces likely to change during implementation

### Scafforge package surfaces

- `skills/spec-pack-normalizer/SKILL.md`
- `skills/spec-pack-normalizer/references/brief-schema.md`
- `skills/scaffold-kickoff/SKILL.md`
- `architecture.md`
- `AGENTS.md`
- new package reference docs describing spec-factory handoff contracts

### Adjacent workspace/service surfaces

- spec-factory workspace/repo layout
- MCP server for intake and artifact exposure
- ChatGPT-facing app or widget surface for idea submission and approval review
- storage model for inbox, drafts, approvals, and attachments

## Ownership boundaries this plan must preserve

- The spec factory owns idea intake, research, creative expansion, drafting, and approval workflow.
- `spec-pack-normalizer` owns the package-side canonical brief normalization contract.
- Scafforge owns generation, ticketing, downstream repo scaffolding, and repair/audit loops.
- ChatGPT/MCP ingress is a transport and UI surface, not the authority for spec approval.

## Phase plan

### Phase 1: Freeze the input and output contracts

- [ ] Define the intake object model for raw ideas, text notes, links, files, and reference assets.
- [ ] Define the minimum approved output schema and map it to `skills/spec-pack-normalizer/references/brief-schema.md`.
- [ ] Decide which fields may remain unresolved and must become explicit decision packets instead of silent guesses.
- [ ] Document exactly what metadata accompanies a handoff into Scafforge.

### Phase 2: Define internal factory roles and state transitions

- [ ] Split responsibilities between research, creative expansion, technical architecture drafting, and editorial normalization.
- [ ] Define who is allowed to transition an item into `decision-needed`, `review`, or `approved`.
- [ ] Specify how conflicting agent outputs are reconciled and recorded.
- [ ] Define what evidence must be attached to an approved brief before handoff.

### Phase 3: Design the MCP and ChatGPT ingress surface

- [ ] Define the MCP-facing intake operations: submit idea, attach files, inspect draft status, request approval view.
- [ ] Design the ChatGPT-facing app as an ingress/review surface rather than as the hidden source of truth.
- [ ] Follow current Apps SDK patterns for MCP server plus widget separation and keep the app bounded to intake/review flows.
- [ ] Ensure the ingress surface cannot bypass the state model and directly trigger generation without an approved artifact.

### Phase 4: Define handoff semantics into Scafforge

- [ ] Specify exactly how the spec factory calls `scaffold-kickoff` or its wrapper once a brief is approved.
- [ ] Define the artifact the downstream orchestration layer receives: brief, provenance, approval timestamp, decision packet residue, and attachments.
- [ ] Ensure Scafforge can reject malformed or incomplete approved briefs cleanly.
- [ ] Define how rejected handoffs route back to the factory without corrupting state.

### Phase 5: Validate the contract with short-idea scenarios

- [ ] Test a very short idea and ensure the factory produces a proper decision-rich brief instead of improvising too much.
- [ ] Test an ambiguous idea and ensure the factory emits a batched decision packet rather than guessing.
- [ ] Test an attachment-heavy idea and ensure references remain linked through approval and handoff.
- [ ] Confirm the approved artifact is sufficient for `scaffold-kickoff` and `spec-pack-normalizer` to consume.

## Validation and proof requirements

- the factory has an explicit state model and cannot skip straight from raw idea to scaffold
- approved outputs align to Scafforge’s canonical brief expectations
- ambiguous inputs produce visible decisions instead of silent assumptions
- ChatGPT/MCP ingress works as a bounded transport/review surface, not a workflow bypass

## Risks and guardrails

- Do not embed the spec factory inside the Scafforge package repo.
- Do not duplicate `spec-pack-normalizer` logic; the factory should enrich inputs, not redefine package truth.
- Do not let chat-based convenience bypass approval and artifact storage.
- Keep the factory’s role narrow enough that it can be tested independently from downstream generation.

## Documentation updates required when this plan is implemented

- a package reference explaining the spec-factory handoff contract
- `architecture.md` and `AGENTS.md` updates for the boundary
- operator docs for ChatGPT/MCP intake and approval flow
- downstream orchestration docs that describe how approved briefs arrive

## Completion criteria

- the spec factory has a real state model and handoff contract
- ChatGPT/MCP idea ingress is possible without boundary confusion
- approved outputs are acceptable to Scafforge
- ambiguous ideas remain visible as decisions instead of becoming pseudo-specs
