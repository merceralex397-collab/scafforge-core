# Spec Factory Intake And Approval Flow

This document explains how ChatGPT and MCP-facing idea intake should interact with the adjacent spec factory without weakening package boundaries.

## Transport model

- MCP is the transport and artifact-exposure layer for the spec factory.
- A ChatGPT-facing surface should use the Apps SDK widget/app layer only for intake, attachment UX, and review rendering.
- Durable business state lives in the file-backed spec-factory workspace, not in widget state or chat memory.

## Recommended ingress operations

- submit idea
- attach file or reference
- inspect item status
- request review view
- record persisted human approval
- publish approved handoff bundle

These operations are bounded to factory workflow. None of them should call `scaffold-kickoff` directly.

## State ownership

- authoritative intake, draft, decision, approval, and handoff state lives in persisted factory files
- derived indices or retrieval caches may exist, but they do not outrank the files
- widget-only state remains ephemeral UI state

## Approval rule

- the review surface may present an approval action
- the actual authority change happens only when the factory writes approval metadata with approver identity and timestamp
- a UI action without a persisted approval artifact is not sufficient

## Handoff boundary

Once the approved bundle exists, the item is eligible for the later orchestration layer to present to `scaffold-kickoff`.

That later orchestration layer is responsible for:

- deciding when to invoke Scafforge
- carrying the approved bundle pointer into the greenfield flow
- handling rejection or retry routing when `spec-pack-normalizer` rejects the bundle

The spec factory stops at “approved and addressable handoff bundle exists.”

