# Phase 02: Environment Bootstrap Universality

**Priority:** P0 — Critical
**Goal:** Detect and bootstrap dependencies for ANY project stack, not just Python/Node/Rust/Go

---

## Problem Statement

`environment_bootstrap.ts` currently only detects four stacks:
- Node.js (via `detectNodeBootstrap()`)
- Python (via `detectPythonBootstrap()`)
- Rust (via `detectRustBootstrap()`)
- Go (via `detectGoBootstrap()`)

Any other project type — Godot, Java/Android, C/C++, .NET, Flutter, Swift, Zig, Elixir, Ruby, PHP, Haskell, or custom toolchains — gets zero detection and zero bootstrap guidance. The Glitch project transcript proves the failure mode: "Android tools missing on this system" was never surfaced or sorted during greenfield because environment_bootstrap had no Godot or Android detection.

---

## Architecture Decision: Stack Adapter Registry

Rather than adding one function per language in an ever-growing if/else chain, adopt a **stack adapter registry** pattern:

```
interface StackAdapter {
  id: string                     // e.g. "godot", "java-android", "dotnet"
  detect(projectRoot: string): Promise<DetectionResult>
  bootstrapCommands(detection: DetectionResult): BootstrapCommand[]
}
```

Each adapter:
1. Scans the project root for indicator files (e.g., `project.godot`, `build.gradle`, `*.csproj`)
2. Returns a `DetectionResult` with version constraints, missing executables, and required environment variables
3. Returns a list of `BootstrapCommand` objects with install/configure commands and user-readable descriptions

The registry iterates over all adapters and returns a combined result. Multiple adapters can trigger for multi-stack projects (e.g., a Python backend + Node frontend).

---

## Fix 02-A: Refactor Existing Detection into Adapter Pattern

### Required Changes

1. **In `environment_bootstrap.ts`:** Extract the existing `detectNodeBootstrap()`, `detectPythonBootstrap()`, `detectRustBootstrap()`, `detectGoBootstrap()` into standalone adapter objects that implement the `StackAdapter` interface.

2. **Create a `detectCommands()` replacement** that iterates over a `STACK_ADAPTERS` array and returns combined results. This replaces the hardcoded four-function call chain.

3. **Preserve backward compatibility:** The output shape should remain the same — a list of bootstrap commands with descriptions. The refactor is internal.

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`

---

## Fix 02-B: Add Stack Adapters for Missing Languages

### Priority Order

Add adapters roughly in this order, based on likelihood of use and severity of the Glitch failure:

#### Tier 1 — Most impactful gaps

1. **Godot adapter** — Detect `project.godot`, check for `godot` executable, detect GDScript version (3.x vs 4.x), detect export templates, detect Android SDK if android export is configured
   - Indicator files: `project.godot`, `*.tscn`, `*.tres`, `*.gd`
   - Required executables: `godot` (or `godot4`)
   - Optional: Android SDK (`ANDROID_HOME` or `ANDROID_SDK_ROOT`), Java (`java`, `javac`)
   - Version detection: parse `project.godot` for `config_version` line

2. **Java/Android adapter** — Detect `build.gradle`, `build.gradle.kts`, `pom.xml`, `settings.gradle`, check for `java`, `javac`, `gradle`, `mvn`, detect `JAVA_HOME`, `ANDROID_HOME`
   - Indicator files: `build.gradle`, `build.gradle.kts`, `pom.xml`, `settings.gradle`, `settings.gradle.kts`
   - Required executables: `java`, `javac`
   - Build tools: `gradle` or `./gradlew` (check for wrapper), `mvn`
   - Optional: `ANDROID_HOME`/`ANDROID_SDK_ROOT` for Android projects (detect `com.android.application` plugin in gradle)
   - Version detection: parse `build.gradle` for `sourceCompatibility`, `targetSdkVersion`

3. **C/C++ adapter** — Detect `CMakeLists.txt`, `Makefile`, `configure`, `meson.build`, `*.c`, `*.cpp`, `*.h`, check for `gcc`/`g++`/`clang`/`clang++`, `cmake`, `make`, `meson`, `ninja`
   - Indicator files: `CMakeLists.txt`, `Makefile`, `configure`, `meson.build`, `*.c`, `*.cpp` (at project root or in `src/`)
   - Required executables: at least one of `gcc`, `g++`, `clang`, `clang++`
   - Build tools: `cmake`, `make`, `ninja`, `meson` depending on indicator
   - Version detection: parse `CMakeLists.txt` for `cmake_minimum_required`, check compiler version

4. **.NET/C# adapter** — Detect `*.csproj`, `*.fsproj`, `*.sln`, `global.json`, check for `dotnet`
   - Indicator files: `*.csproj`, `*.fsproj`, `*.sln`, `global.json`
   - Required executables: `dotnet`
   - Version detection: parse `global.json` for SDK version, or `*.csproj` for `TargetFramework`

#### Tier 2 — Important but less common

5. **Flutter/Dart adapter** — Detect `pubspec.yaml` with flutter dependency, check for `flutter`, `dart`
   - Indicator files: `pubspec.yaml`
   - Required executables: `flutter`, `dart`
   - Version detection: parse `pubspec.yaml` for `environment.sdk`

6. **Swift adapter** — Detect `Package.swift`, `*.xcodeproj`, `*.xcworkspace`, check for `swift`, `swiftc`, `xcodebuild`
   - Indicator files: `Package.swift`, `*.xcodeproj/`, `*.xcworkspace/`
   - Required executables: `swift`, `swiftc`
   - Version detection: parse `Package.swift` for `.macOS` or `.iOS` platform requirements

7. **Zig adapter** — Detect `build.zig`, `build.zig.zon`, check for `zig`
   - Indicator files: `build.zig`, `build.zig.zon`
   - Required executables: `zig`
   - Version detection: `zig version`

8. **Ruby adapter** — Detect `Gemfile`, `*.gemspec`, check for `ruby`, `gem`, `bundler`
   - Indicator files: `Gemfile`, `*.gemspec`
   - Required executables: `ruby`, `gem`, `bundler`
   - Version detection: parse `.ruby-version` or `Gemfile` for `ruby` constraint

#### Tier 3 — Nice to have

9. **Elixir adapter** — Detect `mix.exs`, check for `elixir`, `mix`, `erl`
10. **PHP adapter** — Detect `composer.json`, check for `php`, `composer`
11. **Haskell adapter** — Detect `*.cabal`, `stack.yaml`, `cabal.project`, check for `ghc`, `cabal`, `stack`

#### Tier 4 — Generic fallback

12. **Generic Makefile adapter** — Detect `Makefile` at project root without any other adapter triggering. Report available `make` targets from `make -qp`. This catches custom build systems.

13. **Generic shell adapter** — Detect `build.sh`, `install.sh`, `bootstrap.sh`, `setup.sh`. Report these as manual bootstrap candidates.

### Implementation Guidance

Each adapter should be a self-contained object or function group. Do NOT put all detection logic into one enormous function. Keep each adapter between 30-60 lines.

The detection result for each adapter should include:
```typescript
interface DetectionResult {
  adapter_id: string
  detected: boolean
  indicator_files: string[]         // which files triggered detection
  missing_executables: string[]     // executables not found in PATH
  missing_env_vars: string[]        // environment variables not set
  version_info: Record<string, string>  // detected version constraints
  warnings: string[]                // non-blocking issues
}
```

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`

---

## Fix 02-C: Bootstrap Command Safety

### Problem

Current bootstrap commands are generated but not safety-checked. An adapter could theoretically emit `sudo rm -rf /` as a bootstrap command.

### Required Changes

1. **Add a `SAFE_BOOTSTRAP_PATTERNS` allowlist** that bootstrap commands must match. This is separate from the `SAFE_BASH` patterns in stage-gate-enforcer.ts — it covers install commands specifically:
   - `apt-get install|apt install` (with `--yes` or `-y`)
   - `brew install`
   - `pip install|pip3 install`
   - `npm install -g|pnpm add -g`
   - `cargo install`
   - `go install`
   - `gem install`
   - `sdkmanager` (for Android SDK)
   - `dotnet tool install`
   - `flutter pub get`
   - `mix deps.get`
   - `composer install`
   - `bundler install`
   - `rustup component add|rustup target add`
   - `zig` (no install verb — zig is usually prebuilt)

2. **Reject any command** that does not match a SAFE_BOOTSTRAP_PATTERNS entry. Log a warning for rejected commands.

3. **Never run `sudo`** without explicit user confirmation. If a bootstrap command needs elevated privileges, surface it as a manual step rather than auto-executing.

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`

---

## Fix 02-D: Extend `SAFE_BASH` in Stage-Gate Enforcer

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/stage-gate-enforcer.ts`
**Problem:** `SAFE_BASH` patterns cover Python, Node, Rust, Go run/test commands but not commands for other stacks. When agents try to run Godot scene validation, Android builds, or C++ compilation, the stage-gate enforcer blocks them.

### Required Changes

Add patterns for all Tier 1 and Tier 2 stacks:

- **Godot:** `godot --headless --script`, `godot --headless --export`, `godot --check-only`
- **Java/Android:** `gradle`, `./gradlew`, `mvn`, `javac`, `java -jar`
- **C/C++:** `cmake`, `make`, `ninja`, `gcc`, `g++`, `clang`, `clang++`
- **.NET:** `dotnet build`, `dotnet test`, `dotnet run`, `dotnet publish`
- **Flutter:** `flutter build`, `flutter test`, `flutter analyze`, `dart analyze`
- **Swift:** `swift build`, `swift test`, `swift run`, `xcodebuild`
- **Zig:** `zig build`, `zig test`, `zig run`
- **Ruby:** `ruby`, `rake`, `rspec`, `bundler exec`
- **Elixir:** `mix test`, `mix compile`, `mix run`
- **Generic:** `make`, `make test`, `make check`, `make install`

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/stage-gate-enforcer.ts`

---

## Fix 02-E: Extend `SMOKE_COMMAND_PATTERNS` in Smoke Test

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`
**Problem:** `SMOKE_COMMAND_PATTERNS` only recognizes 8 patterns for Python/Rust/Go/Node. Smoke tests for other stacks are rejected as unknown.

### Required Changes

Add patterns for:

- `godot --headless`
- `gradle test|./gradlew test`
- `mvn test`
- `dotnet test`
- `flutter test`
- `swift test`
- `xcodebuild test`
- `zig test`
- `make test|make check`
- `ruby|rspec|rake test`
- `mix test`
- `php|phpunit`
- `cmake --build` (build verification — not strictly a test but a valid smoke)
- `gcc|g++|clang|clang++` followed by `&& ./a.out` (compile-and-run)

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`

---

## Fix 02-F: Surface Missing Dependencies as Environment Blockers

### Problem

When environment_bootstrap detects missing dependencies, the result is returned but there is no workflow-level mechanism to prevent agents from proceeding to implementation with missing tools. The agent sees "Android SDK not found" in the bootstrap output but the ticket system does not block advancement.

### Required Changes

1. **In `environment_bootstrap.ts`:** When detection finds missing executables that are REQUIRED (not optional), set a top-level `blockers` array in the tool response:
   ```
   {
     blockers: [
       { executable: "godot", reason: "Required by project.godot", install_command: "..." },
       { executable: "android-sdk", reason: "Required by Android export template", install_command: "..." }
     ],
     warnings: [...],
     bootstrap_commands: [...]
   }
   ```

2. **In the team-leader agent template:** Add instructions: "After running `environment_bootstrap`, if the response contains `blockers`, do NOT proceed to implementation. Instead, attempt to resolve the blockers by running the suggested install_command, or surface them as a manual prerequisite to the user."

3. **In `workflow.ts`:** Add a `bootstrap_blockers` field to workflow state. When the environment_bootstrap tool detects blockers, the agent should write them to workflow state so they persist across sessions.

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`

---

## Universal Bootstrap During Greenfield

### How This Integrates with the Greenfield Flow

1. `repo-scaffold-factory` generates the repo with the updated `environment_bootstrap.ts`
2. The bootstrap-lane proof (step 4 in the greenfield chain) should now INCLUDE running `environment_bootstrap` and confirming no unresolved blockers
3. In `shared_verifier.py`, add a `VERIFY009` check: "Environment bootstrap ran and returned zero unresolved blockers"
4. If blockers exist, the greenfield proof fails with a clear message: "Cannot complete greenfield scaffold — missing environment dependencies: [list]"
5. The host agent surfaces this to the user for resolution before continuing

### Files to Change

- `skills/scafforge-audit/scripts/shared_verifier.py` (add VERIFY009)
- `skills/scaffold-kickoff/SKILL.md` (update greenfield flow to reference environment bootstrap verification)

---

## Summary Checklist

| Fix | Done? |
|-----|-------|
| 02-A: Refactor existing detection into adapter pattern | |
| 02-B: Add Tier 1 stack adapters (Godot, Java, C/C++, .NET) | |
| 02-B: Add Tier 2 stack adapters (Flutter, Swift, Zig, Ruby) | |
| 02-B: Add Tier 3 stack adapters (Elixir, PHP, Haskell) | |
| 02-B: Add Tier 4 generic fallback adapters | |
| 02-C: Bootstrap command safety allowlist | |
| 02-D: Extend SAFE_BASH in stage-gate-enforcer | |
| 02-E: Extend SMOKE_COMMAND_PATTERNS in smoke_test | |
| 02-F: Surface missing dependencies as environment blockers | |
| Greenfield integration with VERIFY009 | |
