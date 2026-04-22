# Orchestration Transport Decision

This document is the shared transport coordination artifact for plans `07-autonomous-downstream-orchestration` and `10-viewer-control-plane-winui`.

## Decision

The orchestration service should expose:

- **HTTPS JSON** request/response endpoints for snapshots and control actions
- **Server-Sent Events (SSE)** for live updates to dashboards and operator clients
- **polling only as a reconnect or recovery fallback**

## Why this is the shared choice

This choice satisfies plan `10`'s client requirements without turning the WinUI app into a special protocol endpoint:

- the control plane mostly needs server-to-client live updates
- command dispatch should stay explicit and replayable as API calls
- CLI and other non-GUI clients can consume the same API without a WinUI-only session model
- SSE reconnect semantics plus `Last-Event-ID` style resume fit long-running dashboard feeds and fail-closed stale detection

## Rejected alternatives

### WebSocket as the primary transport

Rejected for the first contract because:

- the client does not need to own a long-lived bidirectional command channel
- it creates extra protocol complexity before the backend job model is settled
- it increases the risk that UI session state becomes a hidden authority

### Polling only

Rejected as the primary live-update mechanism because:

- it is noisy for active factory dashboards
- it increases operator-visible lag for approvals, failures, and package-investigation updates
- it weakens precise stale-state handling compared with an explicit stream

## Minimum transport requirements

1. Snapshot endpoints must be queryable without opening the event stream first.
2. Event streams must carry stable event IDs and sequence numbers.
3. Control actions must remain ordinary API calls, not stream-side ad hoc commands.
4. CLI fallback must be able to use the same snapshot and control endpoints.
5. Clients must be able to detect stream staleness and fall closed to read-only mode.
