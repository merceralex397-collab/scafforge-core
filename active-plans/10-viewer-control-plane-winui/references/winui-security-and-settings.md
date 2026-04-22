# WinUI Security And Settings

This document is the Phase 5 exit artifact for plan `10-viewer-control-plane-winui`.

## Security model

The app manages three separate trust domains:

1. **provider credential enrollment** for model/router services
2. **app-to-backend auth** for the control plane itself
3. **remote connectivity trust** for SSH hosts, service certificates, and WSL target identity

Those domains must remain separate in storage, UI, and logs.

## Secret and settings classes

| Class | Examples | Storage rule |
| --- | --- | --- |
| Non-sensitive preferences | theme, window layout, last-opened screen, known repo labels | plain JSON in the app data folder is acceptable |
| Backend bootstrap token | localhost development token, refresh token handle | DPAPI-encrypted user-scoped store for unpackaged mode; PasswordVault only after packaged deployment exists |
| mTLS material | client certificate reference, certificate thumbprint | private key in Windows certificate store; app stores only thumbprint/reference |
| Provider credential enrollment | provider API keys, router service tokens entered for backend use | capture only in transient UI memory, submit directly to a backend enrollment endpoint over authenticated TLS, then clear local buffers; do not persist in local secret stores |
| SSH trust | host fingerprints, tunnel profile, key reference | fingerprint and profile in settings; private key stays in Windows OpenSSH agent or an encrypted DPAPI-backed import store |

## Storage decision

Because the first implementation wave is unpackaged/internal-tool first:

- **DPAPI-backed user-scoped encrypted storage** is the default steady-state secret store
- **PasswordVault** is a future packaged-mode option once the app has package identity
- **provider credentials are not part of the app's steady-state local secret store**; the app only brokers enrollment into backend-managed storage

The app must not assume PasswordVault is available during the initial unpackaged loop.

## Provider credential rule

The control plane may expose provider-credential enrollment UX, but it must not become the long-lived holder of those credentials.

Rules:

1. The app may collect a provider credential only long enough to submit it to a backend enrollment endpoint over the authenticated control-plane channel.
2. The app must clear in-memory buffers after submission or cancellation.
3. The app must never write provider credentials to DPAPI blobs, PasswordVault entries, JSON settings, logs, screenshots, or crash bundles.
4. Backend-owned secret storage and backend-owned audit records remain the durable source of truth for provider credential custody and rotation.

## Prohibitions

The following are not allowed as steady-state storage for provider keys, backend auth tokens, or SSH credentials:

- plaintext config files
- `.env` files
- environment variables as the long-lived source of truth
- screenshots or export bundles containing unredacted secrets
- local caches that store raw credentials next to read-model snapshots

## Audit logging contract

Backend results remain the authoritative record for operator mutations, but the app should also keep a local operator-action log for supportability.

Each operator action record should capture:

- `timestamp`
- `operator_identity`
- `connection_profile`
- `job_id` or `package_investigation_id`
- `action_kind`
- `requested_payload_summary`
- `backend_result`
- `correlation_id`

The log must capture what action was requested and whether it succeeded, but it must not contain raw secrets.

## Redaction rules

Always redact:

- full provider API keys
- backend bootstrap tokens or refresh tokens
- private-key material
- mTLS private-key locations
- raw authorization headers

When showing diagnostics, exports, or screenshots:

- show only the last 4 to 6 characters of tokens or thumbprints when needed for support
- prefer credential-lane labels instead of secret values
- separate user-entered reasons or notes from any backend auth metadata so they can be exported safely

## Local operator setup path

1. Install the WinUI app and the Windows App SDK runtime required by the adjacent app repo.
2. Create or import a connection profile for local WSL or a remote SSH-tunneled backend.
3. Enroll trust material:
   - local bootstrap token or client certificate
   - backend certificate pin
   - SSH host fingerprint when applicable
4. Verify the connection in read-only mode first.
5. Only then enable backend-mediated mutation controls allowed by the active operator mode.

## Machine-scoped exception rule

If the app later supports a locked-down kiosk or shared-operator workstation:

- machine-scoped secrets may use DPAPI machine scope only with explicit file ACL hardening and operator review
- machine-scoped secrets should remain the exception, not the default

User-scoped storage remains the normal posture for internal use.
