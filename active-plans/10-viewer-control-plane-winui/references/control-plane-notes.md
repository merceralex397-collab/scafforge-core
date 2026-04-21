# Control Plane Notes

## Core Requirement

The app is a viewer and orchestrator, not the canonical owner of repo state.

## Required Integrations

- orchestration service APIs
- model router configuration
- WSL command execution bridge
- SSH-based remote execution bridge
- archive and history data surfaces

## Primary Inputs

- `../../_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`
- `../../_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`
- WinUI planning skill guidance loaded for this planning pass

## Planning Consequence

Build this after the service boundaries are locked. Otherwise the UI will absorb too much unstable backend design work and become a moving target.
