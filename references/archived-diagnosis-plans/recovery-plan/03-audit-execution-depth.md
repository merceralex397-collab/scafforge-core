# Phase 03: Audit Execution Depth

**Priority:** P0 — Critical
**Goal:** Expand audit beyond Python-only execution checking; add real code quality assessment

---

## Problem Statement

`audit_execution_surfaces.py` contains one language-specific deep check: `audit_python_execution()`. This function runs `python -c "import <package>"` and `pytest --collect-only` to verify Python projects actually work. Every other language gets zero equivalent checking.

The Glitch diagnosis run (the only livetesting run we have) found 4 findings — all workflow-surface issues. It found zero code quality issues despite the generated code containing:
- Duplicate autoload registrations
- Scenes referencing non-existent scripts
- Type mismatches in GDScript
- Missing export configurations

The audit literally cannot see code problems because it has no code-inspection capability beyond Python imports.

---

## Fix 03-A: Add Stack-Specific Execution Auditors

### Architecture

Extend `audit_execution_surfaces.py` with a stack adapter dispatch similar to Phase 02's environment bootstrap. Each adapter answers: "Can this project build? Can it run its test suite? Are there obvious broken references?"

### Tier 1 Adapters (Match Phase 02 priority)

#### Node.js execution auditor
- Detect: `package.json` exists
- Checks:
  - `node -e "require('./index')"` or `node -e "require('./src/index')"` — can the entry point load?
  - `npm test` or equivalent — does the test command exit non-zero?
  - Do `dependencies` in `package.json` have matching entries in `node_modules/`? (or `npm ls --json` produces no missing)
  - Finding codes: `EXEC-NODE-001` (entry load failure), `EXEC-NODE-002` (test failure), `EXEC-NODE-003` (missing dependencies)

#### Rust execution auditor
- Detect: `Cargo.toml` exists
- Checks:
  - `cargo check` — does the project compile without errors?
  - `cargo test --no-run` — can tests compile?
  - Finding codes: `EXEC-RUST-001` (compile failure), `EXEC-RUST-002` (test compile failure)

#### Go execution auditor
- Detect: `go.mod` exists
- Checks:
  - `go vet ./...` — static analysis passes?
  - `go build ./...` — does it compile?
  - `go test -run ^$ ./...` — can test binary compile? (runs no tests, just compiles)
  - Finding codes: `EXEC-GO-001` (vet failure), `EXEC-GO-002` (build failure), `EXEC-GO-003` (test compile failure)

#### Godot execution auditor
- Detect: `project.godot` exists
- Checks:
  - Parse `project.godot` for `autoload/*` entries — do the referenced scripts exist?
  - Scan `*.tscn` files for `[ext_resource` lines — do the referenced paths exist?
  - Scan `*.gd` files for `extends` lines — do the referenced base classes exist?
  - If `godot` is available: `godot --headless --check-only` or `godot --headless --script res://check.gd --quit` (if supported by version)
  - Finding codes: `EXEC-GODOT-001` (missing autoload scripts), `EXEC-GODOT-002` (broken scene references), `EXEC-GODOT-003` (broken GDScript extends), `EXEC-GODOT-004` (headless check failure)

#### Java/Android execution auditor
- Detect: `build.gradle` or `pom.xml` exists
- Checks:
  - `./gradlew check --dry-run` or `gradle check --dry-run` — is the build script valid?
  - `javac` on a sample source file if no build tool — does it compile?
  - For Android: does `local.properties` reference a valid `sdk.dir`?
  - Finding codes: `EXEC-JAVA-001` (build script invalid), `EXEC-JAVA-002` (compile failure), `EXEC-JAVA-003` (missing Android SDK path)

#### C/C++ execution auditor
- Detect: `CMakeLists.txt` or `Makefile` exists
- Checks:
  - For CMake: `cmake -S . -B build_check` — does configuration succeed?
  - For Make: `make -n` — does a dry-run pass?
  - Finding codes: `EXEC-CPP-001` (cmake configuration failure), `EXEC-CPP-002` (make dry-run failure)

#### .NET execution auditor
- Detect: `*.csproj` or `*.sln` exists
- Checks:
  - `dotnet build --no-restore` (if restore already ran) — does it compile?
  - `dotnet test --no-build --list-tests` — are tests discoverable?
  - Finding codes: `EXEC-DOTNET-001` (build failure), `EXEC-DOTNET-002` (test discovery failure)

### Dispatch Pattern

Add a `run_stack_execution_audits(repo_path, stack_profile)` function that:
1. Detects which stacks are present (reuse indicator-file logic from Phase 02)
2. Runs the appropriate auditors
3. Collects findings with the new `EXEC-<STACK>-NNN` codes
4. Returns them in the standard findings format

### Files to Change

- `skills/scafforge-audit/scripts/audit_execution_surfaces.py` — add stack auditors

---

## Fix 03-B: Add Static Reference-Integrity Checking

### Problem

Many code quality issues are not about "does it compile" but "are all internal references valid." This is especially critical for game engines and framework-heavy projects where configuration files reference code files.

### Required Changes

Add a `audit_reference_integrity(repo_path)` function that checks cross-file references without needing to compile:

1. **Scene → Script references:** Scan `.tscn`, `.tres` files for `path=` or `script=` attributes. Check that referenced `.gd`, `.cs` files exist.

2. **Config → Code references:** Scan `project.godot`, `AndroidManifest.xml`, `Info.plist`, `.csproj`, `package.json` for path references. Check that referenced files exist.

3. **Import → Module references:** For Python: scan `import` statements, check that imported modules exist in the project or in `requirements.txt`. For TypeScript/JavaScript: scan `import`/`require` statements, check that referenced files or packages exist.

4. **Each broken reference produces a finding:** `REF-001` (scene→script missing), `REF-002` (config→code missing), `REF-003` (import→module missing).

### Scope Limitation

This is NOT a full linter. It only checks that referenced files and identifiers exist. It does NOT check type correctness, logic errors, or style issues. Keep it simple — existence checks only.

### Files to Change

- `skills/scafforge-audit/scripts/audit_execution_surfaces.py` — add `audit_reference_integrity()`

---

## Fix 03-C: Add Code Quality Signal to Diagnosis Reports

### Evidence

**File:** `skills/scafforge-audit/scripts/audit_reporting.py`
**Problem:** The four-diagnosis-report format does not include code quality findings. Report 1 covers workflow, Report 2 covers process, Report 3 covers ticket recommendations, Report 4 covers executive summary. None of them have a section for code issues.

### Required Changes

1. **Extend Report 1** (Findings Report) to include a `## Code Quality Findings` section after the existing workflow findings. This section should include:
   - Execution audit findings (EXEC-*) with the specific error output
   - Reference integrity findings (REF-*) with the broken reference details
   - Severity classification: EXEC findings that prevent building are CRITICAL; REF findings are HIGH; warnings are MEDIUM

2. **Extend Report 3** (Ticket Recommendations) to include remediation tickets for EXEC and REF findings:
   - Each CRITICAL EXEC finding should generate a blocked ticket targeting the specific file/module
   - REF findings should be grouped into one or more fix tickets
   - The ticket recommendations should specify which agent should own the ticket (typically the implementer)

3. **Update `build_ticket_recommendations()`** to route EXEC-* and REF-* findings to project-specific remediation tickets, not to `scafforge-repair` (since these are code issues, not workflow issues).

4. **Update `prevention_action()`** to include prevention text for the new finding families.

### Files to Change

- `skills/scafforge-audit/scripts/audit_reporting.py`

---

## Fix 03-D: Add Audit Finding Routing Precision

### Evidence

**File:** `skills/scafforge-audit/scripts/audit_reporting.py`
**Problem:** `build_ticket_recommendations()` routes almost everything to `scafforge-repair`. But many findings — especially EXEC, REF, ENV, and BOOT findings — are subject-repo issues that should generate local remediation tickets, not Scafforge package repairs.

### Required Changes

1. **Classify finding families by repair target:**
   - **Package-first (needs Scafforge change before repo repair):** WFLOW* (workflow tool contradictions), SKILL* (skill template defects), MODEL* (model profile bugs), CYCLE* (lifecycle contract violations)
   - **Subject-repo-repair:** BOOT* (bootstrap command issues), ENV* (environment prerequisites), EXEC* (execution failures), REF* (reference integrity), SESSION* (session-level issues)
   - **Both (needs triage):** VERIFY* (some are package gates, some are subject-repo truth)

2. **Update `build_ticket_recommendations()`** to apply this classification when generating the ticket target. Package-first findings should say "Scafforge package change required before subject-repo repair" instead of routing directly to scafforge-repair.

3. **Add a triage section to Report 4** (Executive Summary) that groups findings by repair target, giving the operator a clear "fix this first" priority list.

### Files to Change

- `skills/scafforge-audit/scripts/audit_reporting.py`

---

## Fix 03-E: Make Audit Available for Non-OpenCode Contexts

### Problem

The audit scripts are Python and run via the Scafforge host. But the SKILL.md for `scafforge-audit` assumes OpenCode as the execution surface. If a future adapter or manual run needs the audit, the scripts should work standalone.

### Required Changes

1. **Verify all audit scripts can run as standalone Python:** Confirm they take `repo_path` as an argument (or read from a config file) and do not require OpenCode-specific runtime.

2. **Add a `scripts/run_audit.py` entry point** (if not already present) that takes a repo path and runs the full audit suite, outputting the diagnosis pack to a specified directory. This should be usable from any shell without OpenCode.

3. **Document the standalone usage** in a brief comment at the top of `run_audit.py`.

### Files to Change

- `skills/scafforge-audit/scripts/` — add or verify `run_audit.py`

---

## Integration with Greenfield Flow

After Phase 03, the greenfield proof chain should include:

1. **VERIFY009** (from Phase 02): Environment bootstrap ran, zero unresolved blockers
2. **VERIFY010** (new): Stack-specific execution audit ran, zero CRITICAL EXEC findings
3. **VERIFY011** (new): Reference integrity audit ran, zero REF-001/REF-002 findings

These checks should be added to `shared_verifier.py` and referenced in the `scaffold-kickoff/SKILL.md` greenfield flow documentation.

---

## Summary Checklist

| Fix | Done? |
|-----|-------|
| 03-A: Node.js execution auditor | |
| 03-A: Rust execution auditor | |
| 03-A: Go execution auditor | |
| 03-A: Godot execution auditor | |
| 03-A: Java/Android execution auditor | |
| 03-A: C/C++ execution auditor | |
| 03-A: .NET execution auditor | |
| 03-A: Stack dispatch function | |
| 03-B: Reference integrity checker | |
| 03-C: Code quality section in diagnosis reports | |
| 03-D: Finding routing precision | |
| 03-E: Standalone audit runner | |
| Greenfield VERIFY010/011 integration | |
