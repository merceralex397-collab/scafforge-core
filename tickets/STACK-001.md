# STACK-001: Define Tier 1 proof-host matrix and release-gate command contract

## Summary

Freeze the proof-host expectations for Python, Node, Rust, Go, Godot, Java or Android, C or C++, and .NET so later validation tickets know which hosts must provide real execution proof and which hosts must degrade truthfully.

## Why

The rewrite promises Tier 1 execution proof, but later validation tickets cannot be meaningful until the package defines which hosts and commands actually count as release proof.

## Package Boundary

- Define release-proof policy in package docs and validation surfaces.
- Do not add fake host-state files to track toolchains.

## Do This

1. Document the Tier 1 proof-host matrix and the required toolchains for each stack.
2. Define the authoritative proof commands for each Tier 1 stack and distinguish them from best-effort local checks.
3. Record truthful degradation behavior for hosts that lack one or more toolchains.
4. Link the matrix from the package contract and validation docs that later proof tickets will use.

## Files To Update

- `references/stack-adapter-contract.md`
- `references/competence-contract.md`
- `README.md`
- validation docs or comments referenced by `scripts/integration_test_scafforge.py`

## Verify

1. Confirm each Tier 1 stack has a named proof host expectation and one or more authoritative proof commands.
2. Confirm the package docs distinguish release proof from local smoke checks.
3. Confirm later proof tickets can point to this matrix without redefining stack policy.

## Wave

0

## Lane

release-proof

## Parallel Safety

- parallel_safe: true
- overlap_risk: low

## Stage

complete

## Status

done

## Trust

- resolution_state: completed
- verification_state: verified
- finding_source: None
- source_ticket_id: None
- source_mode: None

## Depends On

- SETUP-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [x] The Tier 1 proof-host matrix names the required toolchains and executable proof commands for all Tier 1 stacks
- [x] Release-gate expectations distinguish proof hosts from best-effort hosts and document truthful degradation behavior
- [x] Package validation surfaces know which commands are authoritative for release proof versus local smoke proof
- [x] The proof-host matrix is referenced from the contract or validation docs used by later tickets

## Artifacts

- [references/stack-adapter-contract.md](../references/stack-adapter-contract.md)
- [README.md](../README.md)

## Notes

- RFC coverage: Tier 1 execution proof policy and release-gate host contract.
- Primary surfaces: package validation docs, `references/stack-adapter-contract.md`, `references/competence-contract.md`, and later proof harness tickets.
- This ticket defines the command contract that `STACK-002` will operationalize.
