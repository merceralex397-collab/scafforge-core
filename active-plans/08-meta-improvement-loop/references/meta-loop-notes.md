# Meta Loop Notes

## Intended Flow

1. downstream failure occurs
2. `scafforge-audit` emits the evidence bundle
3. package-level trigger decides whether investigation is required
4. investigator produces root-cause analysis
5. fixer opens a Scafforge PR
6. PR is reviewed and merged
7. revalidation runs
8. downstream audit/repair and resume happen only after revalidation passes

## Primary Inputs

- `../../_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`
- `../../_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`
- `../../references/competence-contract.md`
- `../../references/authority-adr.md`

## Planning Consequence

This loop should be strict and evidence-heavy. It is a package change-management path, not a convenience automation.
