# Curated Fixtures

This directory holds small, intentional regression fixtures for Scafforge package verification.

It replaces the previous pattern of keeping bulk audit dumps, raw session logs, and churn archives in the main product tree.

Rules for this directory:

- Keep fixtures minimal and purpose-built.
- Prefer indexed evidence notes and synthetic setup instructions over raw log dumps.
- Record original archive paths when preserving historical provenance matters.
- Wire every new fixture family to validator or integration coverage.
- Keep corpus registration explicit in `scripts/integration_test_scafforge.py`; do not rely on directory scanning for active fixture families.

Current curated corpora:

- `gpttalker/` for workflow-contract and restart-surface regressions
- `womanvshorse/` for downstream Godot boot/config truth failures
- `spinner/` for viewport/layout truth failures
