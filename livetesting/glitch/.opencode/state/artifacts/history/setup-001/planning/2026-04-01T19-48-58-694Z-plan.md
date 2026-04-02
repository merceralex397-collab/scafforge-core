# Planning Artifact: SETUP-001

## Ticket
- **ID:** SETUP-001
- **Title:** Bootstrap environment and confirm scaffold readiness
- **Wave:** 0
- **Lane:** repo-foundation
- **Stage:** planning

## 1. Scope

SETUP-001 is the environment bootstrap and scaffold confirmation ticket for the Glitch project. It verifies that the OpenCode operating layer, Godot runtime, and Android export prerequisites are in place before Wave 1 implementation tickets (SYSTEM-001, CORE-001, CORE-002, CORE-003) begin.

This ticket does NOT create the Godot project itself—that is the scope of SYSTEM-001.

## 2. Gameplay or Engine Surfaces Affected

- **Environment:** The OpenCode workflow layer (`.opencode/`)
- **Runtime:** Godot engine availability and Android export tooling
- **Validation:** Headless Godot startup commands, import checks, smoke-test surface

## 3. Current Godot Availability Status

### Godot Runtime Verification

**Status:** UNVERIFIED — No `project.godot` file exists in the repo. The repo is currently a pure OpenCode scaffold with no Godot project.

**Evidence:**
- The bootstrap proof (`.opencode/state/artifacts/history/setup-001/bootstrap/2026-04-01T19-46-00-274Z-environment-bootstrap.md`) reports PASS with "No installable dependency surfaces were detected."
- This means `environment_bootstrap` ran successfully but only confirmed no package-manager dependencies exist—it did NOT verify Godot because there is no Godot project file to validate.
- Glob search for `**/project.godot` returns no matches.

**Required Verification:**
- Run `godot --version` to confirm Godot is installed and note the version
- If `godot: command not found`, record as blocker with specific error message

### Android Export Prerequisites

**Status:** NOT YET IDENTIFIED — Android SDK and export templates are required for building an Android APK but have not been verified.

**Required checks:**
1. `echo $ANDROID_HOME` or `echo $ANDROID_SDK_ROOT` to locate Android SDK
2. Check for `$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager` existence
3. Check for Godot export templates at `~/.local/share/godot/export_templates/<version>/` or equivalent

**If missing, record as blocker with explicit next step:** Install Android SDK / Godot export templates before SYSTEM-001 can produce a runnable APK.

## 4. Canonical Validation Commands for This Repo

Once a Godot project exists, the following validation commands are the canonical check surface:

| Command | Purpose | Expected Outcome |
|---------|---------|------------------|
| `godot --headless --path . --quit` | Verify Godot can open the project and shut down cleanly | Clean exit, no errors |
| `godot --headless --path . --import` | Trigger full resource import pipeline | No import errors |
| `godot --headless --path . --check-only --script <script.gd>` | Syntax/parse check on specific scripts | Pass/fail per script |

**Current status:** Cannot run until `project.godot` exists (blocked by SYSTEM-001).

## 5. Implementation Steps

### Step 1: Verify Godot Runtime
- [ ] Run `godot --version` in shell
- [ ] If succeeds, record version (e.g., Godot 4.x.y)
- [ ] If fails, record exact error and treat as blocker

### Step 2: Verify Android Export Prerequisites
- [ ] Check `ANDROID_HOME` / `ANDROID_SDK_ROOT` environment variables
- [ ] Verify `sdkmanager` is accessible if Android SDK is present
- [ ] Check for Godot export templates installation
- [ ] If Android SDK missing, document as blocker: "Android SDK not found. Install Android SDK and Godot export templates before APK builds can succeed."

### Step 3: Document Canonical Validation Commands
- [ ] Write validation commands table to this artifact (see Section 4 above)
- [ ] Confirm these commands are executable in the current repo context (they will fail until SYSTEM-001 creates the project, but they must be documented)

### Step 4: Confirm Bootstrap Status
- [x] `bootstrap.status` in workflow-state.json is already `ready`
- [x] Bootstrap proof artifact exists at `.opencode/state/artifacts/history/setup-001/bootstrap/2026-04-01T19-46-00-274Z-environment-bootstrap.md`
- [ ] Note: This proof confirms "no package-manager dependencies" but does NOT confirm Godot runtime

### Step 5: Advance to Plan Review
- [ ] Transition SETUP-001 from `planning` to `plan_review`
- [ ] Request explicit approval that the Godot/Android verification approach is acceptable

## 6. Validation Plan

| Acceptance Criterion | Validation Method | Current State |
|---------------------|-------------------|---------------|
| Godot runtime availability is verified or exact blocker recorded | Run `godot --version`; record version or error | **UNVERIFIED — needs shell check** |
| Android-facing export prerequisites identified with missing pieces called out | Check `ANDROID_HOME`, sdkmanager, export templates; document any gaps | **NOT YET DONE — needs shell checks** |
| Canonical validation commands written and executable where possible | Document commands in Section 4; confirm they can be attempted | **DOCUMENTED but CANNOT RUN** (no project.godot) |
| Managed bootstrap proof exists and `ticket_lookup.bootstrap.status` is `ready` | Read workflow-state.json | **CONFIRMED ✅** |
| Repo remains aligned on SETUP-001 as first foreground ticket | Confirm active_ticket in workflow-state.json | **CONFIRMED ✅** |

## 7. Risks and Assumptions

### Risks
1. **Godot may not be installed** on the host system. If `godot --version` fails, SYSTEM-001 and all downstream tickets are blocked.
2. **Android SDK may be missing.** Even if Godot is installed, Android APK export requires Android SDK and Godot export templates.
3. **Bootstrap proof is technically accurate but misleading.** The proof confirms "no dependency surfaces" but users may interpret this as "environment is fully ready." It is not—a Godot project still needs to be created.

### Assumptions
1. The host system intends to install Godot and Android tooling before building the actual game.
2. SYSTEM-001 (Create base Godot project architecture) will be the immediate follow-up once SETUP-001 planning is approved.
3. The Scafforge-generated OpenCode layer is sufficient for the Glitch project workflow.

## 8. Blockers or Required User Decisions

### Blocker: Godot Runtime Not Verified

**If `godot --version` fails**, the following exact blocker must be recorded:

> **BLOCKER:** Godot is not installed or not in PATH. Install Godot 4.x from https://godotengine.org/ and ensure the `godot` command is accessible before proceeding with SYSTEM-001.

### Blocker: Android SDK Not Found

**If `ANDROID_HOME`/`ANDROID_SDK_ROOT` is unset or sdkmanager is missing:**

> **BLOCKER:** Android SDK is not configured. Set `ANDROID_HOME` to a valid Android SDK path and install Godot export templates via Godot's Export menu or manually from https://godotengine.org/.

### No Blocker: Bootstrap Status

The bootstrap proof exists and `bootstrap.status` is `ready`. This satisfies the workflow gate. However, the above runtime blockers must still be resolved before SYSTEM-001 can produce a runnable Godot project and APK.

## 9. Next Stage Gate

Before SETUP-001 can move from `planning` → `plan_review`:

- [ ] Godot version must be confirmed OR exact blocker recorded
- [ ] Android SDK status must be identified and gaps documented
- [ ] This artifact must be registered via `artifact_register`

After plan review approval: SETUP-001 moves to `implementation` (though the implementation here is primarily documenting the verification results rather than creating new files).
