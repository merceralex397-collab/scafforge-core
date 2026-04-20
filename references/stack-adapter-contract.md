# Stack Adapter Contract

This document defines the shared contract for stack detection, environment bootstrap guidance, and execution-audit coverage across Scafforge.

## Purpose

Scafforge uses stack adapters to keep greenfield bootstrap, generated workflow guidance, target-completion planning, execution proof, and audit coverage aligned across different project types.

An adapter is responsible for three related questions:

1. How do we detect this stack from repo evidence?
2. What host prerequisites and bootstrap commands should be surfaced before development continues?
3. What target-completion or release-proof obligations must exist before the repo can be treated as finished?
4. What execution-surface checks should audit and greenfield verification run before handoff?

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

- Tier 1: detection, bootstrap guidance, target-completion or release-proof coverage, and execution-audit coverage. Current Tier 1 stacks are Python, Node, Rust, Go, Godot, Java or Android, C or C++, and .NET. The authoritative proof-host matrix below defines the required toolchains and command families for those stacks.
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

## Target-completion contract

Tier 1 stacks must also define what "finished" means for the declared target platform, even when bootstrap host gaps still exist on the current machine.

Adapters must be able to answer:

- which host prerequisites are required for the target artifact path
- which repo-local surfaces must exist before export or release work is considered configured
- which backlog lanes or tickets must own target-completion work
- what concrete artifact path proves release readiness

This target-completion metadata is internal package contract state. It should inform bootstrap warnings, ticket generation, repair follow-up, audit routing, and greenfield verification without changing the normalized `environment_bootstrap` output schema.

### Godot Android target-completion expectations

**Repo-managed surfaces** (owned by Scafforge scaffold and managed repair):
- `export_presets.cfg` with an Android preset (rendered from project provenance at scaffold time)
- repo-local `android/` support surfaces when the generated workflow declares the repo owns them
- export path, package name, and version metadata derived from canonical project truth

**Host prerequisites** (detected by bootstrap and audit; Scafforge cannot fabricate these):
- Godot executable
- Java and `javac`
- Android SDK path
- Godot export templates

**Signing inputs** (modeled explicitly; Scafforge must not auto-generate secrets or keystores):
- release keystore path or CI secret reference
- keystore alias and password ownership
- release artifact format (`apk` or `aab`)
- signing-mode decision when the brief requires packaged delivery

**Canonical backlog ownership:**
- `ANDROID-001` in lane `android-export` — owns repo-managed export surfaces and first non-placeholder android/` support surfaces
- `SIGNING-001` in lane `signing-prerequisites` — owns signing prerequisites when the brief requires a packaged Android product; must be resolved before `RELEASE-001` may close
- `RELEASE-001` in lane `release-readiness` — owns runnable proof and, when packaged delivery is required, deliverable proof

**Runnable proof** (answers: can the repo produce and validate a first runnable Android build?):
- `godot --headless --quit --path .` or the resolved equivalent
- debug export success for the canonical Android export command
- debug APK present at `build/android/<project-slug>-debug.apk`

**Deliverable proof** (answers: can the repo produce the packaged Android artifact the brief actually requires? — only relevant when brief declares a packaged Android product):
- a signed release APK or AAB
- explicit signing ownership already satisfied via `SIGNING-001`
- artifact path declared in canonical truth

Debug APK proof is valid runnable proof. It must not be treated as deliverable proof when the brief requires a packaged Android product.

Treat explicit target facts from `docs/spec/CANONICAL-BRIEF.md` and `.opencode/meta/bootstrap-provenance.json` as authoritative even before repo-local export files such as `export_presets.cfg` exist.

## Package-Level Validation Versus Release Proof

The package validators are still `npm run validate:contract`, `npm run validate:smoke`, `python3 scripts/integration_test_scafforge.py`, and `python3 scripts/validate_gpttalker_migration.py`.

- Those commands prove the Scafforge package and its harnesses.
- They do not replace stack-specific release proof in generated repos.
- Later proof tickets should point at the stack matrix below when they need the authoritative release command for a given Tier 1 stack.

## Tier 1 Proof-Host Matrix

| Stack | Required host/toolchain | Authoritative release-proof command family | Best-effort local check | Truthful degradation |
| --- | --- | --- | --- | --- |
| Python | Python 3.10+ plus the project-selected environment manager and test runner | `python -m pytest -q` or the repo-native equivalent surfaced by the adapter | Package smoke or harness checks are not release proof substitutes | Report missing interpreter or environment manager as a blocker |
| Node | Node.js 20+ plus the repo-selected package manager | `npm test` or the repo-native equivalent surfaced by the adapter | Package smoke or harness checks are not release proof substitutes | Report missing Node or package manager as a blocker |
| Rust | Rust toolchain (`cargo` and `rustc`) | `cargo test` or the repo-native equivalent surfaced by the adapter | Package smoke or harness checks are not release proof substitutes | Report missing Rust toolchain as a blocker |
| Go | Go toolchain | `go test ./...` or the repo-native equivalent surfaced by the adapter | Package smoke or harness checks are not release proof substitutes | Report missing Go as a blocker |
| Godot | Godot editor plus any release/export prerequisites named by the project | `godot --headless --quit --path .` plus the project-specific export or test command when release proof depends on export readiness | Package smoke or harness checks are not release proof substitutes | Report missing Godot or export prerequisites as a blocker |
| Java or Android | JDK, Gradle wrapper or build tooling, and Android SDK when the target is Android | `./gradlew test` or `./gradlew assembleDebug` when the project evidence makes that the canonical proof path | Package smoke or harness checks are not release proof substitutes | Report missing JDK, Gradle, or Android SDK prerequisites as blockers |
| C or C++ | Compiler toolchain and the repo-selected build system such as CMake, Make, or Meson | `cmake --build .`, `make`, `meson test`, or the repo-native equivalent surfaced by the adapter | Package smoke or harness checks are not release proof substitutes | Report missing compiler or build-system prerequisites as blockers |
| .NET | .NET SDK | `dotnet test` or the repo-native equivalent surfaced by the adapter | Package smoke or harness checks are not release proof substitutes | Report missing .NET SDK as a blocker |

The adapter may narrow each family to the repo-native command that the project evidence supports, but it must not downgrade release proof into a generic smoke check.

## Adding a new adapter

When adding a new stack adapter, update all of these surfaces together:

1. Add detection and bootstrap guidance in `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`.
2. Add or extend smoke and safe-command support where the generated workflow needs it.
3. Add target-completion or release-proof guidance to backlog generation, repair follow-up, and verification surfaces if the stack is meant to be Tier 1.
4. Add execution-audit coverage in `skills/scafforge-audit/scripts/audit_execution_surfaces.py` if the stack is meant to be Tier 1.
5. Add stack-aware team and skill guidance through `opencode-team-bootstrap` and `project-skill-bootstrap` inputs.
6. Update package docs such as `README.md`, `AGENTS.md`, and this contract.
7. Add or extend regression coverage in `scripts/smoke_test_scafforge.py`.

Do not promote a stack to Tier 1 unless execution-audit coverage and proof coverage both exist.

## Proof expectations

Phase 10 multi-stack proof is the acceptance bar for new adapters.

At minimum, a new adapter should prove:

- detection triggers on the intended indicator files
- bootstrap guidance surfaces real blockers and safe commands
- target-completion expectations define the canonical backlog owner and release artifact path for the declared platform
- generated workflow surfaces name the correct stack-specific commands
- audit emits the expected EXEC or REF findings when the stack is deliberately broken
- clean fixtures pass the relevant verification path without false positives

## Stub-free acceptance requirement

Execution audits for Tier 1 stacks must detect and report runtime stub patterns as EXEC findings. This applies to:

- Rust: `todo!()`, `unimplemented!()`, `// Stub`, `// For now`, `not_implemented` status fields, placeholder return values in product-spine code
- Python: `raise NotImplementedError`, `pass  #`, `# TODO: implement`, placeholder returns
- TypeScript/JavaScript: `throw new Error('not implemented')`, `// TODO`, placeholder returns

Stub detection must scan the full module tree (all crates or source directories), not only files whose paths match a narrow set of name tokens. Product-spine stubs in any module are EXEC findings.

A ticket that closes with runtime stubs in its changed module is not a valid closeout. Review and QA agents must run a mandatory stub-detection grep for runtime-integration tickets and treat stubs in the changed module's files as blockers. Stubs in other modules must be noted as follow-on items, not used to block unrelated tickets.
