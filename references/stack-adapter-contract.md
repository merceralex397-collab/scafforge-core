# Stack Adapter Contract

This document defines the shared contract for stack detection, environment bootstrap guidance, and execution-audit coverage across Scafforge.

## Purpose

Scafforge uses stack adapters to keep greenfield bootstrap, generated workflow guidance, and audit coverage aligned across different project types.

An adapter is responsible for three related questions:

1. How do we detect this stack from repo evidence?
2. What host prerequisites and bootstrap commands should be surfaced before development continues?
3. What execution-surface checks should audit and greenfield verification run before handoff?

## Adapter interface

The generated `environment_bootstrap` tool implements adapters that return one normalized detection record per stack:

- `adapter_id`
- `detected`
- `indicator_files`
- `missing_executables`
- `missing_env_vars`
- `version_info`
- `warnings`
- `commands`
- `blockers`

The adapter output must be safe to persist into canonical workflow state as bootstrap blocker evidence.

## Tier definitions

- Tier 1: detection, bootstrap guidance, and execution-audit coverage. Current Tier 1 stacks are Python, Node, Rust, Go, Godot, Java or Android, C or C++, and .NET.
- Tier 2: detection and bootstrap guidance, but no stack-specific execution audit in the package yet. Current Tier 2 stacks are Flutter or Dart, Swift, Zig, and Ruby.
- Tier 3: detection only with explicit blocker reporting and truthful fallback messaging. Current Tier 3 stacks are Elixir, PHP, and Haskell.
- Tier 4: generic fallback detection for repos that primarily expose Makefile or shell-based entrypoints without a stronger adapter match.

## Detection rules

Adapters must prefer deterministic repo evidence over guesses. Current examples include:

- Python: `pyproject.toml`, `requirements*.txt`, `uv.lock`, or repo-local `.venv`
- Node: `package.json`
- Rust: `Cargo.toml`
- Go: `go.mod`
- Godot: `project.godot`, `*.tscn`, `*.tres`, `*.gd`
- Java or Android: `build.gradle`, `build.gradle.kts`, `settings.gradle`, `pom.xml`
- C or C++: `CMakeLists.txt`, `Makefile`, `meson.build`, or root-level source files
- .NET: `*.csproj`, `*.fsproj`, `*.sln`, `global.json`
- Flutter or Dart: `pubspec.yaml`
- Swift: `Package.swift`, `*.xcodeproj`, `*.xcworkspace`
- Zig: `build.zig`, `build.zig.zon`
- Ruby: `Gemfile`, `*.gemspec`
- Elixir: `mix.exs`
- PHP: `composer.json`
- Haskell: `*.cabal`, `stack.yaml`, `cabal.project`
- Generic fallback: `Makefile`, executable shell entrypoints

## Bootstrap contract

Adapters may recommend commands only when they match the generated bootstrap safety rules.

Bootstrap guidance must:

- surface missing executables and environment variables as explicit blockers
- persist blockers in workflow state until bootstrap reaches `ready`
- stop greenfield continuation when blockers remain
- prefer repo-native package flows where they exist, such as `uv`, repo-local virtualenvs, lockfiles, or package-manager-specific install commands
- degrade truthfully when the package cannot fully bootstrap a stack on the current host

## Execution-audit contract

Tier 1 stacks must have execution-surface audit coverage so greenfield verification can enforce VERIFY010 and VERIFY011 before handoff.

Current audit coverage includes:

- Python
- Node
- Rust
- Go
- Godot
- Java or Android
- C or C++
- .NET

Execution audits should fail on structural build or load defects, not on speculative product-quality opinions.

Reference-integrity checks should fail when canonical config or scene surfaces point at missing files.

## Adding a new adapter

When adding a new stack adapter, update all of these surfaces together:

1. Add detection and bootstrap guidance in `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`.
2. Add or extend smoke and safe-command support where the generated workflow needs it.
3. Add execution-audit coverage in `skills/scafforge-audit/scripts/audit_execution_surfaces.py` if the stack is meant to be Tier 1.
4. Add stack-aware team and skill guidance through `opencode-team-bootstrap` and `project-skill-bootstrap` inputs.
5. Update package docs such as `README.md`, `AGENTS.md`, and this contract.
6. Add or extend regression coverage in `scripts/smoke_test_scafforge.py`.

Do not promote a stack to Tier 1 unless execution-audit coverage and proof coverage both exist.

## Proof expectations

Phase 10 multi-stack proof is the acceptance bar for new adapters.

At minimum, a new adapter should prove:

- detection triggers on the intended indicator files
- bootstrap guidance surfaces real blockers and safe commands
- generated workflow surfaces name the correct stack-specific commands
- audit emits the expected EXEC or REF findings when the stack is deliberately broken
- clean fixtures pass the relevant verification path without false positives