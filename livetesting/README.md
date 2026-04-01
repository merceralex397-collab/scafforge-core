# Live Testing Workspace

This folder is dedicated to live project testing of Scafforge inside the IDE. It is not the final product repository, but an experimental sandbox for validating the toolchain end-to-end in the workspace itself.

## Purpose

- Use Scafforge greenfield flow from within this repository to generate, build, and iterate test apps.
- Verify scafforge behavior in a real development loop using the integrated IDE terminal.
- Capture tooling and process artifacts to identify automation gaps and stability issues.

## Current Live Test Project: Glitch

The first live project is glitch, a simple 2D Android platformer concept. It is a working proof of concept for how a generated app can be bootstrapped and evolved using Scafforge architecture in the same repo.

## Workflow Notes

1. Run Scafforge commands from livetesting with the integrated terminal.
2. Follow standard greenfield Scafforge pipeline:
   - scaffold-kickoff
   - spec-pack-normalizer
   - epo-scaffold-factory
   - project-skill-bootstrap
   - opencode-team-bootstrap
   - gent-prompt-engineering
   - 	icket-pack-builder
   - handoff-brief
3. Use opencode and .opencode conventions to inspect generated tickets, state, and restart surface.
4. Use the Glitch project as a stress test target for running, rebuilding, and versioning in the IDE.

## Goal

Prove that Scafforge can safely bootstrap and iterate an Android game inside its own repository while maintaining an OpenCode-oriented workflow and a single legal next move.
