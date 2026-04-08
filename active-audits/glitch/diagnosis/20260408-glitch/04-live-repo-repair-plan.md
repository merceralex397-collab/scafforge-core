# 04 — Live Repo Repair Plan
**Repo:** `/home/pc/projects/Scafforge/livetesting/glitch`
**Audit date:** 2026-04-08
**Priority:** bring ANDROID-001 and the Android build path to a runnable state

---

## Repair Priority Order

The blocking dependency chain is:
ANDROID-001 must implement → RELEASE-001 can then execute → Android APK produced

Until ANDROID-001 implements its export surfaces, RELEASE-001 is permanently blocked.

---

## Repair Step 1 (CRITICAL): Revert ANDROID-001 Split-Scope Decision Blocker

**Finding:** WFLOW-LOOP-001  
**Action:** Manually correct the ANDROID-001 ticket state in `manifest.json` and `workflow-state.json` so the workflow routes correctly.

### Exact Changes Required

**In `tickets/manifest.json`, find the ANDROID-001 entry and:**

1. Change `"stage": "plan_review"` → `"stage": "planning"` (since the plan has not been APPROVED)
2. Change `"status": "plan_review"` → `"status": "ready"` (plan exists and is ready for review, but the ticket status should not be "plan_review" when approved_plan is false)
3. Replace the `decision_blockers` entry:
   - **Remove:** `"Split scope delegated to follow-up ticket RELEASE-001. Keep the parent open and non-foreground until the child work lands."`
   - **Add:** `"Sequential split: ANDROID-001 must complete implementation (create export_presets.cfg and android/ surfaces) before RELEASE-001 can proceed to implementation."`

4. Change `"active_ticket": "RELEASE-001"` → `"active_ticket": "ANDROID-001"` in the manifest root

**In `.opencode/state/workflow-state.json`:**

1. Change `"active_ticket": "RELEASE-001"` → `"active_ticket": "ANDROID-001"`
2. Change `"stage": "plan_review"` → `"stage": "plan_review"` (keep — ANDROID-001 has a plan that should be reviewed)
3. Change `"approved_plan": true` → `"approved_plan": false` (plan not yet approved)
4. Clear the stale ANDROID-001 lane lease from `lane_leases[]` (it has expired)
5. ANDROID-001 in `ticket_state` should have `"approved_plan": false`

**Rationale:** ANDROID-001 has a valid plan (2026-04-02) that was never reviewed. The correct next step is to run plan_review for ANDROID-001, approve it, then implement the export surfaces.

---

## Repair Step 2 (CRITICAL): Plan Review for ANDROID-001

**After Step 1**, the workflow should route to:
- Active ticket: ANDROID-001
- Stage: plan_review
- Action: `glitch-plan-reviewer` reviews the ANDROID-001 plan artifact

**The ANDROID-001 plan artifact exists at:**
`.opencode/state/artifacts/history/android-001/planning/2026-04-02T15-00-22-444Z-plan.md`

The plan is comprehensive and well-formed. The reviewer should:
1. Confirm the `export_presets.cfg` structure is correct for Godot 4.x Android export
2. Confirm the `android/` directory structure matches Godot 4.6.2.stable requirements
3. Flag the `godot-lib.aar` blocker as a hard pre-QA blocker
4. PASS the plan (it is ready for implementation)

---

## Repair Step 3 (CRITICAL): Implement ANDROID-001 Export Surfaces

**After plan_review PASS**, implement ANDROID-001:

1. Create `export_presets.cfg` at repo root using the exact content in the plan artifact (Section 3, Decision 1)
2. Create the full `android/` directory tree per the plan's Decision 2
3. Create `AndroidManifest.xml` with `package="com.glitch.game"`
4. Create placeholder icon files (real PNG files at `android/res/drawable/icon.png`, not zero-byte)
5. Create Gradle configuration files (`build.gradle`, `settings.gradle`, `gradle.properties`)
6. **Resolve godot-lib.aar blocker:**
   ```bash
   ls ~/.local/share/godot/export_templates/4.6.2.stable/android_source.zip && \
     mkdir -p android/app/libs && \
     unzip -j ~/.local/share/godot/export_templates/4.6.2.stable/android_source.zip \
       "app/libs/godot-lib.aar" -d android/app/libs/
   ```
   If `android_source.zip` does not exist, check:
   ```bash
   find ~/.local/share/godot/export_templates/ -name "godot-lib.aar" 2>/dev/null
   ```
   If neither exists → **hard blocker**. Must download Android export templates from Godot Editor.
7. Create `build/android/` output directory

**Validation after implementation:**
```bash
# Verify export_presets.cfg exists and has correct preset name
grep 'name="Android Debug"' export_presets.cfg

# Verify AndroidManifest.xml
grep 'package="com.glitch.game"' android/src/main/AndroidManifest.xml

# Verify godot-lib.aar
file android/app/libs/godot-lib.aar  # should show "Zip archive data"

# Verify icon PNG
file android/res/drawable/icon.png  # should show "PNG image data"
```

---

## Repair Step 4 (HIGH): Fix GlitchPhysicsModifier WARNING

**Finding:** EXEC-WARN-001  
**Current state:** `godot-headless.log` shows WARNING despite REMED-002 review claiming it's fixed.

**Two options:**

**Option A (Preferred):** Fix the lookup path in `PlayerController.gd`:
```gdscript
# Current (wrong):
physics_modifier = get_node_or_null("/root/GlitchPhysicsModifier")

# Fixed approach — get from GlitchEventManager if it exposes the modifier:
var event_manager = get_node_or_null("/root/GlitchEventManager")
if event_manager and event_manager.has_method("get_physics_modifier"):
    physics_modifier = event_manager.get_physics_modifier()
else:
    push_warning("[PlayerController] GlitchEventManager does not expose get_physics_modifier")
```

**Option B:** Register `GlitchPhysicsModifier` as a standalone autoload in `project.godot`:
```
GlitchPhysicsModifier="*res://scripts/glitch/GlitchPhysicsModifier.gd"
```

Either option must be followed by a fresh headless run to confirm the WARNING no longer appears in output.

**Also required:**
- Mark REMED-002's latest review artifact as `"trust_state": "suspect"` in manifest.json
- REMED-002 needs a re-review with actual headless output evidence

---

## Repair Step 5 (MEDIUM): Fix project.godot Version Format

**Finding:** PROJ-VER-001

Change `project.godot`:
```
# From:
config_version=2
config/features=PackedStringArray("4.2", "GLES2")
quality/driver/driver_name="GLES2"

# To:
config_version=5
config/features=PackedStringArray("4.2", "Forward Plus")
```

Remove the `[rendering]` section's `quality/driver/driver_name="GLES2"` line. Godot 4.x rendering is configured differently.

**Verify** with headless startup after change — all 4 autoloads should still initialize.

---

## Repair Step 6 (LOW): Clean Up Stale ANDROID-001 Lease

Already handled in Step 1 (remove from `lane_leases[]`). The lease expired at 2026-04-08T02:39:14.277Z and is no longer active regardless.

---

## Repair Step 7 (LOW): Address REF-003

**Finding:** REF-003 (stale zod TypeScript imports)

This is a node_modules installation issue, not a user-authored defect. Options:

1. Run `bun install` or `npm install` inside `.opencode/` to regenerate the compiled outputs
2. Or: add `.opencode/node_modules/` to `.gitignore` and instruct the setup step to run `bun install` after clone
3. The `.opencode/bun.lock` file exists — the package is correctly declared, just incompletely installed

**Recommended:** Add `.opencode/node_modules/` to the repo's `.gitignore` and document that `bun install` or `npm install` inside `.opencode/` is required after clone.

---

## Sequenced Repair Checklist

| # | Step | Priority | Dependency |
|---|---|---|---|
| 1 | Fix ANDROID-001 ticket state in manifest.json + workflow-state.json | CRITICAL | None |
| 2 | Run ANDROID-001 plan_review | CRITICAL | Step 1 |
| 3 | Implement ANDROID-001 export surfaces | CRITICAL | Step 2 |
| 4 | Run ANDROID-001 QA (validate export surfaces + dry-run export) | CRITICAL | Step 3 |
| 5 | Close ANDROID-001, activate RELEASE-001 | CRITICAL | Step 4 |
| 6 | Implement RELEASE-001 APK build | CRITICAL | Step 5 |
| 7 | Fix GlitchPhysicsModifier WARNING + re-run REMED-002 review | HIGH | None (parallel) |
| 8 | Fix project.godot config_version | MEDIUM | None (parallel) |
| 9 | Clean stale lease | LOW | Done in Step 1 |
| 10 | Fix REF-003 (bun install) | LOW | None (parallel) |

---

## Expected State After Repairs

- `export_presets.cfg` exists at repo root with Android Debug preset
- `android/` directory exists with AndroidManifest, Gradle files, godot-lib.aar
- `build/android/glitch-debug.apk` exists after RELEASE-001 implementation
- `godot-headless.log` shows no WARNING
- ANDROID-001: closed
- RELEASE-001: in_progress or beyond
- Active next work: CORE-002 completion (REMED-002 still needs QA to pass), or CORE-003 once CORE-002 is resolved
