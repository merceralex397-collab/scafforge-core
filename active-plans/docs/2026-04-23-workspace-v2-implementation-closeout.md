# Workspace V2 Implementation Closeout

## Scope completed

This closeout covers full implementation of plans `15` through `19`.

The implementation landed across:

- the Scafforge bootstrap/workspace repo
- `scafforge-core`
- `scafforge-control-plane`
- `scafforge-archive`
- `mcode`
- `meta-skill-engineering`

## What changed

### Plan 15: generated repo root and inventory architecture

- the workspace layout now keeps generated repos outside the factory workspace under `ScafforgeProjects`
- the bootstrap repo documents that generated repos are tracked by orchestration inventory, not by folder scan
- `scafforge-core` now documents tracked repo, host, path binding, agent session, and ticket contracts

### Plan 16: existing-machine migration and adoption

- migration docs now cover the old standalone `Scafforge` root-name collision explicitly
- the workspace helper documents the one-time normalization pass required on existing machines
- the current local durable/generated repos were moved into `ScafforgeProjects` to match the canonical layout

### Plan 17: worker fabric and host registration

- `scafforge-core` and the control-plane contracts now model Windows, WSL, and SSH Linux worker hosts explicitly
- the control-plane demo/live contracts now show worker health, connection profile IDs, capabilities, and generated repo roots

### Plan 18: control-plane project tracking

- the control-plane app now exposes tracked repos, hosts, agent sessions, tickets, repo lifecycle controls, agent lifecycle controls, direct project creation, prompt profiles, model-role routing, theme settings, and walkthrough onboarding
- dev mode and release mode now exist as explicit app postures
- both dev and release build outputs can now be published with bootstrap profiles

### Plan 19: generated repo lifecycle policy

- the product contracts no longer hardcode a personal durable repo list
- durable adoption is now criteria-based and documented
- local machine state can still include durable repos such as `spinner` or `womanvshorse*`, but those remain machine state, not product defaults

## Adjacent ecosystem updates

- `scafforge-archive` now has a structured ingest and catalog surface for retained bundles plus the two research paths
- `meta-skill-engineering` is now documented as the owner of the `skill-faults` path
- `mcode` is now documented as the long-range replacement candidate for the mixed orchestration/runtime SDK stack

## Validation performed

- workspace validation scripts
- `dotnet build` for `scafforge-control-plane`
- archive ingest/catalog script execution
- local generated repo move verification into `ScafforgeProjects`

## Notes

- generated repo names from the current local machine are not baked into the product as shipped defaults
- the control-plane demo data uses generic sample inventory
