# Phase 10: Multi-Stack Proof Program

**Priority:** P2 — Medium (this is validation, not implementation)
**Depends on:** Phases 01–08 (all implementation must land before proof targets can validate anything)
**Goal:** Prove the hardened Scafforge works for multiple project types end-to-end

---

## Problem Statement

Scafforge currently has one livetesting target: Glitch (a Godot 2D platformer). One test project is not enough to prove universal stack support. The Glitch livetesting exposed critical gaps precisely because it was the first non-Python/Node project to go through the pipeline.

A multi-stack proof program runs the greenfield pipeline against a representative set of project types and validates that each one produces a functional, non-contradictory, immediately-continuable scaffold.

---

## Proof Target Design

Each proof target is a minimal project concept — just enough to exercise the stack adapter, environment bootstrap, execution audit, and smoke test for that stack. These are NOT full applications. They are scaffold-viability probes.

### Target 01: Python CLI Tool

**Concept:** A minimal Python CLI that accepts a command-line argument and prints a formatted result.

**Why it matters:** Python is the most-tested path. This target validates that existing Python support was not regressed by the multi-stack changes.

**Stack indicators:** `requirements.txt`, `pyproject.toml`, `src/__main__.py`

**Validation criteria:**
- [ ] `environment_bootstrap` detects Python and pip
- [ ] `smoke_test` recognizes `pytest` pattern
- [ ] `audit_python_execution()` can import the main module
- [ ] VERIFY001–VERIFY011 all pass
- [ ] Generated code actually runs: `python -m <package> --help` exits 0

---

### Target 02: Node.js REST API

**Concept:** A minimal Express.js (or Fastify) API with one GET endpoint that returns JSON.

**Why it matters:** Node is the second most-tested path. Tests the npm/pnpm detection and TypeScript compilation check.

**Stack indicators:** `package.json`, `tsconfig.json`, `src/index.ts`

**Validation criteria:**
- [ ] `environment_bootstrap` detects Node and npm/pnpm
- [ ] `smoke_test` recognizes `npm test` or `pnpm run test` pattern
- [ ] Execution auditor confirms `node -e "require('./dist')"` works (post-build)
- [ ] VERIFY001–VERIFY011 all pass
- [ ] Generated code starts: `npm start` runs without crashing for 5 seconds

---

### Target 03: Rust CLI Tool

**Concept:** A minimal Rust CLI that reads stdin and writes transformed output.

**Why it matters:** Validates cargo-based stack detection and compilation checking.

**Stack indicators:** `Cargo.toml`, `src/main.rs`

**Validation criteria:**
- [ ] `environment_bootstrap` detects rustc and cargo
- [ ] `smoke_test` recognizes `cargo test` pattern
- [ ] Execution auditor confirms `cargo check` passes
- [ ] VERIFY001–VERIFY011 all pass
- [ ] Generated code compiles: `cargo build` exits 0

---

### Target 04: Go HTTP Service

**Concept:** A minimal Go HTTP server with one handler.

**Why it matters:** Validates go module detection.

**Stack indicators:** `go.mod`, `main.go`

**Validation criteria:**
- [ ] `environment_bootstrap` detects go
- [ ] `smoke_test` recognizes `go test` pattern
- [ ] Execution auditor confirms `go vet ./...` and `go build ./...` pass
- [ ] VERIFY001–VERIFY011 all pass
- [ ] Generated code compiles: `go build .` exits 0

---

### Target 05: Godot 2D Game

**Concept:** A minimal Godot 4.x project with one scene, one script, and one autoload.

**Why it matters:** This is the Glitch stack. It validates the new Godot adapter and catches the exact failures that Glitch exposed.

**Stack indicators:** `project.godot`, `scenes/main.tscn`, `scripts/main.gd`

**Validation criteria:**
- [ ] `environment_bootstrap` detects Godot (or reports it as a blocker if not installed)
- [ ] Reference integrity check confirms all scene→script references resolve
- [ ] Autoload entries in `project.godot` point to existing scripts
- [ ] `smoke_test` recognizes `godot --headless` pattern (if Godot is available)
- [ ] VERIFY001–VERIFY011 all pass
- [ ] If Godot is installed: `godot --headless --script res://check.gd --quit` exits 0

---

### Target 06: C/CMake Library

**Concept:** A minimal C library with CMake build and one test.

**Why it matters:** Validates the C/C++ adapter, cmake detection, and compilation checking.

**Stack indicators:** `CMakeLists.txt`, `src/lib.c`, `include/lib.h`, `test/test_lib.c`

**Validation criteria:**
- [ ] `environment_bootstrap` detects cmake and gcc/clang
- [ ] `smoke_test` recognizes `cmake --build` or `make test` pattern
- [ ] Execution auditor confirms `cmake -S . -B build_check` succeeds
- [ ] VERIFY001–VERIFY011 all pass
- [ ] Generated code compiles: `cmake -S . -B build && cmake --build build` exits 0

---

### Target 07: .NET Console App

**Concept:** A minimal .NET 8 console application.

**Why it matters:** Validates .NET adapter.

**Stack indicators:** `*.csproj`, `Program.cs`

**Validation criteria:**
- [ ] `environment_bootstrap` detects dotnet
- [ ] `smoke_test` recognizes `dotnet test` pattern
- [ ] Execution auditor confirms `dotnet build --no-restore` passes
- [ ] VERIFY001–VERIFY011 all pass
- [ ] Generated code runs: `dotnet run` exits 0

---

### Target 08: Java/Gradle CLI

**Concept:** A minimal Java CLI with Gradle build.

**Why it matters:** Validates Java/Android adapter (without Android-specific complexity).

**Stack indicators:** `build.gradle`, `settings.gradle`, `src/main/java/Main.java`

**Validation criteria:**
- [ ] `environment_bootstrap` detects java, javac, gradle (or gradlew)
- [ ] `smoke_test` recognizes `gradle test` or `./gradlew test` pattern
- [ ] Execution auditor confirms `gradle check --dry-run` passes
- [ ] VERIFY001–VERIFY011 all pass
- [ ] Generated code compiles: `gradle build` exits 0

---

## Proof Program Execution

### How to Run

1. For each target, create a minimal spec input (project name, concept description, stack)
2. Run `scaffold-kickoff` in greenfield mode
3. Let the full pipeline complete (or fail)
4. Collect results: which VERIFY checks passed/failed, which tools succeeded/failed, which agent prompts triggered confusion

### Success Criteria

A proof target PASSES when:
- All VERIFY001–011 checks pass (or fail with user-actionable blockers for missing system tools)
- The generated scaffold contains no unsubstituted placeholders
- The generated scaffold's ticket system is internally consistent
- The generated code passes basic stack-specific execution checks
- An agent can read START-HERE.md, find the active ticket, and understand the next legal move

A proof target FAILS when:
- Any VERIFY check fails with a non-user-actionable error
- The generated scaffold contains contradictory tool output
- The generated code fails basic structural checks (broken references, unresolvable imports)
- An agent cannot determine the next legal move from the restart surface

### Regression Test

After all proof targets pass, create a regression test in `scripts/integration_test_scafforge.py` that:
- Scaffolds each target in a temp directory
- Runs verify_generated_scaffold.py
- Runs the stack execution audit
- Confirms VERIFY001–011 pass
- Cleans up

This regression test should run in CI (when CI exists) to catch future regressions.

---

## Proof Target Priority

| Target | Stack | New Adapter? | Priority |
|--------|-------|-------------|----------|
| 01 | Python | No (existing) | Regression check |
| 02 | Node.js | No (existing) | Regression check |
| 03 | Rust | No (existing) | Regression check |
| 04 | Go | No (existing) | Regression check |
| 05 | Godot | Yes (new) | Critical — validates Glitch fix |
| 06 | C/CMake | Yes (new) | Important — validates new adapter |
| 07 | .NET | Yes (new) | Important — validates new adapter |
| 08 | Java/Gradle | Yes (new) | Important — validates new adapter |

Run targets 01–04 first to confirm no regressions, then 05–08 to validate new adapters.

---

## Livetesting Integration

The existing `livetesting/glitch/` project serves as Target 05's predecessor. After the hardening phases land:

1. Run a fresh greenfield scaffold against a clean Glitch spec
2. Compare the result against the current `livetesting/glitch/` state
3. Document which issues from the original Glitch diagnosis are now prevented vs. which still appear
4. Use the comparison to validate the recovery plan's completeness

New proof targets (01–04, 06–08) can be added to `livetesting/` if they prove useful for ongoing stress-testing.

---

## Summary Checklist

| Target | Spec Created | Scaffold Run | VERIFY Pass | Execution Pass | Regression Test |
|--------|-------------|-------------|-------------|----------------|-----------------|
| 01: Python CLI | | | | | |
| 02: Node.js API | | | | | |
| 03: Rust CLI | | | | | |
| 04: Go HTTP | | | | | |
| 05: Godot 2D | | | | | |
| 06: C/CMake | | | | | |
| 07: .NET Console | | | | | |
| 08: Java/Gradle | | | | | |
