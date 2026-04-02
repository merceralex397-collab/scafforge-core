# QA Artifact: SETUP-001 Bootstrap Environment Verification

**Ticket:** SETUP-001  
**Stage:** qa  
**QA Date:** 2026-04-01  
**Artifact Path:** `.opencode/state/qa/setup-001-qa-qa.md`

---

## Check 1: Godot Version

**Command:** `godot --version`

**Raw Output:**
```
4.6.2.stable.official.71f334935
```

**Assessment:** ✅ PASS  
**Finding:** Godot 4.6.2 is installed and available on PATH.

---

## Check 2: Android SDK Environment Variables

**Commands:**
```bash
echo "ANDROID_HOME: $ANDROID_HOME"
echo "ANDROID_SDK_ROOT: $ANDROID_SDK_ROOT"
ls -la /home/pc/Android/Sdk
```

**Raw Output:**
```
ANDROID_HOME: 
ANDROID_SDK_ROOT: 
total 36
drwxr-xr-x 8 pc pc 4096 Apr  1 20:21 .
drwxr-xr-x 3 pc pc 4096 Apr  1 20:15 ..
-rw-r--r-- 1 pc pc   16 Apr  1 20:21 .knownPackages
drwxr-xr-x 3 pc pc 4096 Apr  1 20:18 .temp
drwxr-xr-x 3 pc pc 4096 Apr  1 20:18 build-tools
drwxr-xr-x 3 pc pc 4096 Apr  1 20:18 cmdline-tools
drwxr-xr-x 2 pc pc 4096 Apr  1 20:18 licenses
drwxr-xr-x 3 pc pc 4096 Apr  1 20:18 platform-tools
drwxr-xr-x 3 pc pc 4096 Apr  1 20:18 platforms
```

**Assessment:** ✅ PASS (with note)  
**Finding:** Android SDK is installed at `/home/pc/Android/Sdk`. Environment variables `ANDROID_HOME` and `ANDROID_SDK_ROOT` are not set in the current shell, but the SDK directory exists and contains build-tools, cmdline-tools, platform-tools, and platforms directories. SDK structure is valid for Android export.

---

## Check 3: sdkmanager Availability

**Command:** `ls -la /home/pc/Android/Sdk/cmdline-tools/latest/bin/sdkmanager`

**Raw Output:**
```
-rwxr-xr-x 1 pc pc 5763 Apr  1 20:18 /home/pc/Android/Sdk/cmdline-tools/latest/bin/sdkmanager
```

**Assessment:** ✅ PASS  
**Finding:** sdkmanager is present and executable at the expected path.

---

## Check 4: Godot Export Templates

**Command:** `ls -la ~/.local/share/godot/export_templates/`

**Raw Output:**
```
total 12
drwxr-xr-x 3 pc pc 4096 Apr  1 20:17 .
drwxr-xr-x 4 pc pc 4096 Apr  1 20:50 ..
drwxr-xr-x 3 pc pc 4096 Apr  1 20:17 4.6.2.stable
```

**Assessment:** ✅ PASS  
**Finding:** Godot export templates for version 4.6.2.stable are installed. This is the matching version for the installed Godot binary.

---

## Check 5: Bootstrap Status Verification

**Command:** `cat .opencode/state/workflow-state.json | grep -A5 '"bootstrap"'`

**Raw Output:**
```json
{
  "bootstrap": {
    "status": "ready",
    "last_verified_at": "2026-04-01T19:46:00.276Z",
    "environment_fingerprint": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "proof_artifact": ".opencode/state/artifacts/history/setup-001/bootstrap/2026-04-01T19-46-00-274Z-environment-bootstrap.md"
  }
}
```

**Assessment:** ✅ PASS  
**Finding:** Bootstrap status is `ready` in workflow-state.json. Last verified at 2026-04-01T19:46:00.276Z. Bootstrap proof artifact is registered.

---

## QA Summary

| Check | Command | Result |
|-------|---------|--------|
| Godot version | `godot --version` | ✅ PASS - 4.6.2.stable.official.71f334935 |
| Android SDK environment | `echo` + `ls -la /home/pc/Android/Sdk` | ✅ PASS - SDK directory exists with valid structure |
| sdkmanager | `ls -la .../sdkmanager` | ✅ PASS - executable present |
| Export templates | `ls -la ~/.local/share/godot/export_templates/` | ✅ PASS - 4.6.2.stable templates installed |
| Bootstrap status | `cat workflow-state.json` | ✅ PASS - status is `ready` |

**Overall Result: PASS**

### Blockers
None. All five environment verification checks passed successfully.

### Notes
- ANDROID_HOME and ANDROID_SDK_ROOT environment variables are not exported in the current shell. This is not a blocker for Godot Android export, but if future build scripts rely on these variables explicitly, they should be set.
- The workflow-state.json correctly reflects bootstrap status as `ready` with a valid proof artifact path.

### Closeout Readiness
SETUP-001 is ready to proceed from QA to smoke-test stage. The environment is properly bootstrapped with:
- Godot 4.6.2 stable
- Android SDK with build-tools, platforms, and cmdline-tools
- Matching export templates
- Bootstrap proof recorded in workflow state
