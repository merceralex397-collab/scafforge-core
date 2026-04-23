# Worker Host Contract

This document freezes the minimum contract for host-resident workers in the Scafforge ecosystem.

## Boundary

- The orchestration service dispatches work to worker hosts.
- Workers are host-resident processes or daemons, not app-resident agents.
- The Windows control plane is a client of worker and host state; it is not the execution surface.
- WSL and SSH are transport and trust mechanisms, not alternate sources of mutation authority.

## Supported host kinds

The first contract supports:

- `windows`
- `wsl`
- `ssh-linux`

Hybrid support is first-class. Hosts must present a common backend-facing registration shape even when their local runtimes differ.

## Minimum host record

Each registered host should expose at least:

- `host_id`
- `host_kind`
- `display_name`
- `connectivity_state`
- `worker_state`
- `worker_version`
- `worker_capabilities`
- `reachable_repo_roots`
- `default_generated_repo_root`
- `supported_autonomy_levels`
- `active_agent_count`

## Worker responsibilities

Workers should:

- receive job claims from the backend
- execute work against host-local repo paths
- report capability and health state
- report live agent sessions, ticket ownership, and stop or pause evidence
- surface failure and progress evidence back to the backend
- avoid inventing canonical repo truth outside generated repo contracts

Workers must not:

- accept mutation commands directly from the control plane
- bypass orchestration APIs for canonical job control
- treat a local repo checkout as permission to invent inventory state

## Repo path model

- Worker hosts may use host-local repo roots such as `ScafforgeProjects/`.
- The same repo may have different absolute paths on Windows, WSL, and SSH Linux hosts.
- Those differences are normalized through orchestration-owned `PathBinding` records, not by forcing identical absolute paths.

## Health and capability rule

Worker health and capability reporting remain backend-owned operational state.

Examples of capability signals include:

- toolchain availability
- runtime presence
- network posture
- stack-specific execution capability
- artifact storage reachability

The control plane may render these summaries, but it must not derive them by direct shell probing as its canonical source of truth.

## Lifecycle control rule

Host-resident workers must support backend-mediated lifecycle actions for running sessions:

- start
- pause
- resume
- stop

Those controls may be exposed in the Windows app, but only as backend-mediated requests. The app must never become the direct lifecycle authority over host processes.
