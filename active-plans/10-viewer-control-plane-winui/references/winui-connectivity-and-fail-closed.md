# WinUI Connectivity And Fail-Closed

This document is the Phase 3 exit artifact for plan `10-viewer-control-plane-winui`.

## Connectivity principle

The WinUI app talks to the same orchestration API and event stream in both local and remote cases. WSL and SSH are transport concerns, not alternate mutation authorities.

## WSL transport choice

The chosen WSL transport is:

- the orchestration service runs inside WSL
- the WinUI app connects over loopback HTTPS plus SSE through WSL localhost forwarding
- optional read-only WSL discovery may use `wsl.exe --status` and `wsl.exe --list --verbose`

Why this choice:

- it keeps the same HTTP/SSE contract as remote hosts
- it avoids using `wsl.exe` as a mutation path
- it supports fast local build/run loops on a Windows workstation while leaving repo execution inside the Linux environment where Scafforge runs naturally

The app may use `wsl.exe` only for read-only environment discovery or diagnostics. It must never dispatch mutable repo or orchestration commands through `wsl.exe`.

## SSH transport choice

The chosen SSH transport is:

- the app establishes or reuses an SSH tunnel to a remote orchestration service
- the WinUI shell then talks to the remote service over the same loopback HTTPS plus SSE contract used for local WSL
- SSH host verification uses pinned host keys and operator-approved trust enrollment

This keeps remote connectivity aligned with the same backend API contract instead of inventing a second remote-command protocol.

The app must not use ad hoc SSH shell sessions as a mutation path for approvals, pause/resume, retries, merges, or repo edits.

## Observation vs mutation channels

| Channel | Allowed use | Forbidden use |
| --- | --- | --- |
| WSL discovery | read-only health checks, distro enumeration, connectivity diagnostics | repo mutation, ticket mutation, merge control, provider-policy changes |
| SSH tunnel | transport for backend HTTPS/SSE, host reachability checks, trust verification | remote shell mutation outside orchestration APIs |
| Backend HTTPS/SSE | snapshots, event feed, approvals, pause/resume, retry, router-policy changes | none beyond backend policy limits |

All operator mutations must flow through the orchestration API.

## App-to-backend authentication decision

Three approaches were compared:

| Option | Strengths | Weaknesses | Decision |
| --- | --- | --- | --- |
| Shared API key | simple for single-machine bootstrap | weak attribution, weak revocation, easy accidental reuse, poor remote-host posture | allowed only for localhost development bootstrap |
| OAuth 2.0 client credentials | common service-to-service pattern | models the app as a service, not a human operator; weak fit for per-operator attribution | rejected for the desktop operator app |
| mTLS | strong transport identity, good remote-host fit, supports explicit trust enrollment | more setup overhead than a shared key | chosen as the steady-state app-to-backend trust mechanism |

Chosen path:

1. **localhost development** may start with a short-lived shared bootstrap token stored in the app's secure local store.
2. **remote or multi-machine use** requires mTLS with pinned service certificates.
3. **operator permissions** remain backend-owned and must be tied to the authenticated operator/session record, not inferred from local app settings alone.

## Host trust model

The app keeps explicit trust records for:

- WSL distro label and expected backend endpoint
- SSH host fingerprint
- backend service certificate thumbprint or pinset
- last successful authenticated session timestamp

If any trust record changes unexpectedly, the app enters `read-only-degraded` until the operator re-establishes trust.

## Fail-closed rules

The app must fail closed whenever trust, auth, or connectivity is ambiguous.

### Triggers

- backend auth expired or rejected
- service certificate mismatch
- SSH host-key mismatch
- WSL target unavailable or routed to a different distro than expected
- event stream stalled beyond the allowed freshness window
- backend cannot confirm operator permission mode

### Required behavior

1. Disable every mutation control.
2. Leave cached read models visible only with an explicit stale marker.
3. Surface the exact reason for degraded mode.
4. Preserve reconnect and diagnostics actions.
5. Do not silently fall back to direct GitHub, repo shell, WSL, or SSH mutation.

### Minimum stale-state presentation

Every stale view should show:

- `last_successful_sync_at`
- `stale_reason`
- `currently_displaying_cached_data: true`
- `mutation_controls_disabled: true`

## Recovery flow

To leave `read-only-degraded`, the app must:

1. re-establish transport
2. re-validate trust material
3. refresh backend auth
4. fetch a fresh snapshot from the orchestration service
5. re-enable only the controls allowed by the backend's current operator mode
