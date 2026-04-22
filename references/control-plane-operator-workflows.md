# Control Plane Operator Workflows

This document captures the package-level operator rules for connectivity, auth, and override flows used by an adjacent control plane.

## Connectivity

The recommended connectivity shape is:

- local Windows app to WSL-hosted orchestration service over loopback HTTPS plus event stream
- remote Windows app to SSH-tunneled orchestration service over the same HTTPS plus event stream contract

The app may perform read-only environment discovery, but it must not use direct WSL or SSH shell mutation as a fallback control path.

## Auth

- unpackaged internal-tool mode should use DPAPI-backed user-scoped secret storage
- packaged mode may use PasswordVault for user-scoped secrets once the app has package identity
- remote or multi-machine control should use mTLS as the steady-state app-to-backend trust mechanism
- localhost development may use a short-lived bootstrap token, but not as the long-lived production posture

Provider credentials, backend auth, and SSH trust records remain separate trust domains. Provider credentials may be enrolled through the app, but they must be handed straight to backend-managed storage and not retained in local steady-state secret storage.

## Override and approval flows

The operator may approve or reject:

- spec or intake decisions exposed by the backend
- merge approvals
- retry or resume actions that policy requires a human to approve
- explicit override requests raised by backend workflows

Every approval or override must travel through the backend API and be attributable to an operator/session record.

## Fail-closed rule

When auth, trust, or connectivity is ambiguous:

The app switches to read-only mode until trust is restored.

1. the app switches to read-only mode
2. cached state may remain visible only with a stale marker
3. mutation controls stay disabled until trust is restored
4. the app must not fall back to GitHub mutation, repo-local mutation, or direct shell dispatch

## Evidence and supportability

Operator workflows should leave:

- backend-owned action evidence
- local redacted operator-action logs
- clear stale-state reasons when the app is in degraded mode

This keeps the control plane observable and supportable without making it the source of truth.
