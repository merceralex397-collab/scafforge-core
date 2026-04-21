# Orchestration Notes

## Core Split

- spec factory creates approved briefs
- Scafforge performs one-shot generation
- downstream orchestration runs ticket or phase execution after generation

## Key Boundaries To Preserve

- `scaffold-kickoff` remains the public package entrypoint
- generated repo state remains owned by the runtime workflow layer
- the orchestration service may trigger work, but it should not become a second mutation authority inside the repo

## Primary Inputs

- `../../_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`
- `../../_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`
- `../../references/one-shot-generation-contract.md`
- `../../references/authority-adr.md`

## Planning Consequence

The orchestration layer must wrap the package. It must not erase Scafforge’s current contract model in order to automate it.
