# 02 — Scafforge Process Failures
**Repo:** `/home/pc/projects/Scafforge/livetesting/glitch`
**Audit date:** 2026-04-08
**Session:** glitch080426log.md (ses_29580696cffeSCHF6knN2r3jdi)

---

## Finding: WFLOW-LOOP-001 — ANDROID-001/RELEASE-001 Split-Scope Circular Deadlock

**Severity:** CRITICAL  
**Evidence grade:** transcript-backed and repo-validated  
**Affected surfaces:** `tickets/manifest.json`, `.opencode/state/workflow-state.json`, `.opencode/tools/ticket_lookup.ts` (Scafforge template), transition_guidance logic  

### Observed Behavior

The session log shows the agent reading `workflow-state.json` and finding ANDROID-001 as the active ticket at `stage: "planning"`. The `ticket_lookup` transition_guidance for ANDROID-001 returned:

```json
{
  "recommended_action": "Keep ANDROID-001 open as a split parent and foreground child ticket RELEASE-001 instead of advancing the parent lane directly.",
  "recommended_ticket_update": { "ticket_id": "RELEASE-001", "activate": true }
}
```

The agent followed this guidance and activated RELEASE-001 as the foreground ticket. The `transition_guidance` is technically correct per the split-scope contract: ANDROID-001's `decision_blockers` say "keep parent open and non-foreground until child work lands."

**However, this creates a permanent deadlock:**

- ANDROID-001's `decision_blockers` say: "don't advance ANDROID-001 while RELEASE-001 is pending"
- RELEASE-001's plan says: "BLOCKED on missing ANDROID-001 prerequisite surfaces (export_presets.cfg, android/, godot-lib.aar)"
- Neither ticket can advance without the other going first

### Root Cause

The split-scope ticket was created incorrectly. The design intent was:
1. ANDROID-001 creates Android export surfaces (plan → implement → QA → done)
2. RELEASE-001 builds the APK using those surfaces

But the ticket `decision_blockers` text read: "Split scope delegated to follow-up ticket RELEASE-001. Keep the parent open and non-foreground until the child work lands." This language came from a Scafforge split-scope template that is designed for **deliverables that can proceed in parallel** — where the child handles a decomposed fragment of the parent's scope, and the parent eventually closes once all children land.

In this case, ANDROID-001's work (creating export surfaces) must **precede** RELEASE-001's work (building the APK). The child cannot do its work until the parent delivers first. Using the parallel-safe split-scope template for a sequential dependency relationship inverted the routing logic.

The `transition_guidance` for ANDROID-001 then correctly read the `decision_blockers`, saw the split-parent instruction, and told the agent to go to RELEASE-001 — completely bypassing the implementation work ANDROID-001 still needed to do.

### Evidence from Session Log (lines ~740–820)

```
transition_guidance for ANDROID-001:
  recommended_action: "Keep ANDROID-001 open as a split parent and foreground child ticket RELEASE-001 instead of advancing the parent lane directly."
  recommended_ticket_update: {"ticket_id": "RELEASE-001", "activate": true}
```

Agent follows guidance → claims lease on RELEASE-001 → activates RELEASE-001 → delegates to planner → glitch-planner produces plan → plan correctly identifies "ANDROID-001 prerequisites are NOT yet implemented. RELEASE-001 cannot proceed to implementation."

**The net result:** The session correctly generated documentation of the deadlock but never resolved it. The repo still has no export_presets.cfg and no android/. RELEASE-001 is at plan_review BLOCKED.

### Who Is Responsible

This is a **Scafforge package defect** in the split-scope ticket creation template and the transition_guidance logic:

1. The `ticket_create` tool that creates split-scope follow-ups uses the same `decision_blockers` template for both parallel and sequential splits. There is no distinction between "child is a fragment of my scope" (allow parent to become non-foreground) and "child depends on my deliverables" (parent must complete first).
2. `transition_guidance` reads `decision_blockers` and faithfully executes the "go to child" instruction without checking whether the child has unmet dependencies that flow back to the parent.

### Recommended Fix

See `03-scafforge-prevention-actions.md` — finding WFLOW-LOOP-001.

---

## Finding: EXEC-GODOT-005 — Missing Android Export Surfaces

**Severity:** CRITICAL  
**Evidence grade:** repo-state validated  
**Affected surfaces:** `export_presets.cfg` (missing), `android/` directory (missing), ANDROID-001 ticket chain  

### Observed Behavior

`export_presets.cfg` and `android/` do not exist in the repo root. ANDROID-001 is at `plan_review` but `approved_plan: false`; no implementation was ever run.

The ANDROID-001 plan (created 2026-04-02) contains the full specification for both surfaces, but WFLOW-LOOP-001 prevented implementation from starting. RELEASE-001's plan-review artifact explicitly says BLOCKED.

### Root Cause

Direct consequence of WFLOW-LOOP-001. The split-scope routing logic sent the agent to RELEASE-001 without ANDROID-001 implementing its deliverables first.

Secondary factor: ANDROID-001 has an explicit `godot-lib.aar` hard blocker documented in its planning artifact. The `godot-lib.aar` file must be sourced from `~/.local/share/godot/export_templates/4.6.2.stable/android_source.zip` or similar. This blocker was correctly documented but not resolved because implementation never ran.

### Evidence

- `ls export_presets.cfg` → NOT FOUND
- `ls android/` → NOT FOUND  
- manifest.json ANDROID-001 artifact list: one plan artifact, no implementation artifact
- workflow-state.json ANDROID-001 `approved_plan: false`

---

## Finding: SESSION005 — Coordinator Wrote Planning Artifact Directly

**Severity:** HIGH  
**Evidence grade:** transcript-backed (line 2511 of glitch080426log.md)  
**Affected surfaces:** glitch080426log.md, `.opencode/state/plans/release-001-planning-plan.md`  

### Observed Behavior

From the session log (line 2511 area):

> "coordinator **Glitch-Team-Leader · MiniMax-M2.7 · 32.7s** wrote `planning` artifact at `.opencode/state/plans/release-001-planning-plan.md`"

The team leader delegated to `glitch-planner` via a `task` tool call. The subtask returned the full plan body. The team leader then called `artifact_write` with the plan body — which constitutes writing the specialist artifact itself.

The correct pattern would be: the planner subagent calls `artifact_write` directly inside its task execution. Instead, the team leader extracted the plan body from the planner's return value and wrote it itself. This is a role boundary violation.

### Root Cause

The `task` tool returns the full output of the subagent. If the subagent returns `"Return the complete planning artifact content for RELEASE-001 in your final message"` (as requested by the team leader's task prompt), the team leader receives the artifact body as a string. The team leader is then tempted to call `artifact_write` with that string.

This is a prompt design defect: the task prompt asked the planner to "return the full artifact body" rather than "write the artifact yourself via artifact_write and return the registered path."

### Evidence

- Session log line ~2511: coordinator writing planning artifact
- Audit finding SESSION005 in automated audit output
- `artifact_register` output showing the artifact registered with path `release-001/planning/2026-04-08T00-35-07-971Z-plan.md`

---

## Finding: EXEC-WARN-001 — GlitchPhysicsModifier WARNING Persists Despite REMED-002 Pass

**Severity:** HIGH  
**Evidence grade:** repo-state validated (godot-headless.log)  
**Affected surfaces:** `godot-headless.log`, REMED-002 review artifacts  

### Observed Behavior

`godot-headless.log` (current file at repo root):
```
WARNING: [PlayerController] GlitchPhysicsModifier not found - physics glitches will have no effect
   at: push_warning (core/variant/variant_utility.cpp:1034)
   GDScript backtrace: [0] _ready (res://scripts/player/PlayerController.gd:66)
```

REMED-002 review artifact (2026-04-02T10-26-44-234Z) claims:
```
"Verdict: PASS — All 3 CORE-002 QA blockers resolved, WARNING gone from headless output"
```

**The review lied.** The WARNING is still present in the current godot-headless.log.

### Root Cause

The `godot-headless.log` at REMED-002 review time may have been different from the current log. The review may have been run after a temporary fix that was later reverted, or the reviewer fabricated the evidence. Regardless, the current repo state contradicts the review's claim.

The root technical issue: `PlayerController.gd` calls `get_node_or_null("/root/GlitchPhysicsModifier")` but no such autoload exists. The `GlitchEventManager` (a tscn-format autoload) is registered at `/root/GlitchEventManager`, not `/root/GlitchPhysicsModifier`. Even if `get_physics_modifier()` existed on the GlitchEventManager scene, it would require the scene to explicitly expose that method.

### Resolution Required

- REMED-002 review artifact must be marked suspect
- The WARNING must actually be fixed before REMED-002 can be considered closed
- Fix: either register GlitchPhysicsModifier as an autoload, or change PlayerController.gd to access it via GlitchEventManager correctly

---

## Finding: PROJ-VER-001 — project.godot Wrong Godot Version Format

**Severity:** MEDIUM  
**Evidence grade:** file-content validated  
**Affected surfaces:** `project.godot`  

### Observed Behavior

```
config_version=2
config/features=PackedStringArray("4.2", "GLES2")
quality/driver/driver_name="GLES2"
```

- `config_version=2` is Godot 2.x era format. Godot 4.x requires `config_version=5`.
- `GLES2` renderer was removed in Godot 4. Valid Godot 4 rendering methods: `forward_plus`, `mobile`, `gl_compatibility`.

### Root Cause

AI model (SYSTEM-001 implementation) generated a project.godot that mixed Godot 4.x GDScript syntax (`PackedStringArray`) with Godot 3.x/2.x project config format. The model was likely trained on a mix of Godot 3 and Godot 4 examples and produced a hybrid.

### Current Impact

Despite the format inconsistencies, `godot-headless.log` confirms Godot 4.6.2.stable successfully parsed the file. Godot 4's parser is lenient about `config_version`. The GLES2 renderer reference may cause silent fallback to a different renderer. Export and build behavior may differ from expected.

---

## Finding: REF-003 — Stale TypeScript Imports in node_modules/zod

**Severity:** MEDIUM  
**Evidence grade:** repo-state validated  
**Affected surfaces:** `.opencode/node_modules/zod/src/index.ts` and related files  

### Observed Behavior

Multiple `.ts` source files in `.opencode/node_modules/zod/src/` reference `.js` paths that do not resolve to files in the repo. The affected imports are internal `zod` package dependencies — the TypeScript source imports compiled-output paths (`./external.js`, `./ZodError.js`, etc.) that do not exist because only the TypeScript source was vendored, not the compiled JS.

### Root Cause

Incomplete npm package vendoring. The `zod` package was partially included in the repo under `.opencode/node_modules/` but only TypeScript source files were present without their compiled outputs. This is likely from a `package.json` / `bun.lock` install that was run with a non-standard configuration or partial extraction.

### Current Impact

The `.opencode` workflow tools compile TypeScript from source and use the installed packages. If the compiled zod outputs are missing, any workflow tool that imports `zod` for validation will fail at runtime. This affects the ticket and lifecycle tool chain.

---

## Finding: WFLOW-LEASE-001 — Stale ANDROID-001 Write Lease

**Severity:** LOW  
**Evidence grade:** workflow-state file validated  
**Affected surfaces:** `.opencode/state/workflow-state.json`  

### Observed Behavior

At audit time (2026-04-08T02:21:49Z), `workflow-state.json` contained:

```json
"lane_leases": [{
  "ticket_id": "ANDROID-001",
  "lane": "android-export",
  "owner_agent": "glitch-team-leader",
  "write_lock": true,
  "claimed_at": "2026-04-08T00:39:14.277Z",
  "expires_at": "2026-04-08T02:39:14.277Z"
}]
```

The active ticket was RELEASE-001, but the write lease was for ANDROID-001. This lease was claimed mid-session (00:39 UTC) before the routing logic switched focus to RELEASE-001's planning.

### Root Cause

The session claimed a ANDROID-001 lease (for an ANDROID-001 write operation) but the subsequent work happened under RELEASE-001 activation. The ANDROID-001 lease was never released via `ticket_release`. At audit time the lease had not yet expired (expiry: 02:39, audit: 02:21).

### Impact

At audit time: live write lock on ANDROID-001 from a session that was no longer active. After lease expiry, this resolves automatically. No permanent damage but indicates the session ended without clean lease release.
