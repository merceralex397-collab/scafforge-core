# Bug and Structural Flaw Register

## Critical Bugs (Fixed)

### BUG-001: Missing hasPendingRepairFollowOn Import
- **Severity**: CRITICAL — killed all tool calls in all 3 downstream repos
- **Location**: stage-gate-enforcer.ts (template)
- **Root cause**: RC-001 added call to hasPendingRepairFollowOn() but forgot the import
- **Fix**: Added import statement (commit 686cc74a)
- **Validation**: All 3 repos can now execute tool calls

### BUG-002: .venv Symlinks Crash Copytree
- **Severity**: HIGH — repair fails on Python repos with virtual environments
- **Location**: run_managed_repair.py copytree calls
- **Root cause**: shutil.copytree follows symlinks by default; .venv contains circular symlinks
- **Fix**: Added .venv*, node_modules, __pycache__ to copytree ignore (commit 6e9bb3dc)

### BUG-003: Model Prefix Doubling
- **Severity**: HIGH — generates invalid model references like minimax-coding-plan/minimax-coding-plan/MiniMax-M2.7
- **Location**: apply_repo_process_repair.py load_metadata()
- **Root cause**: Provenance stores "provider/model" but bootstrap prepends provider again
- **Fix**: Strip provider prefix before rendering (commit 7ead92e0)

### BUG-004: Provenance Round-Trip Failure
- **Severity**: HIGH — repair uses "framework-agnostic" instead of actual stack_label
- **Location**: apply_repo_process_repair.py load_metadata()
- **Root cause**: load_metadata() used hardcoded defaults instead of reading from provenance
- **Fix**: Recover stack_label and product_finish_contract from bootstrap-provenance.json (commit 03adb917)

### BUG-005: REMED-RELEASE-GATE Duplicate Crash
- **Severity**: MEDIUM — repair crashes on re-run when ticket already exists
- **Location**: apply_remediation_follow_up.py ensure_android_target_completion_tickets()
- **Root cause**: No existence check before creating REMED-RELEASE-GATE ticket
- **Fix**: Added existence check (commit c8bb368f)

### BUG-006: Unhelpful managed_blocked Error
- **Severity**: MEDIUM — agents stuck in loops because they don't know how to self-unblock
- **Location**: stage-gate-enforcer.ts BLOCKER message
- **Root cause**: Message said "report to operator" — unhelpful in headless mode
- **Fix**: Message now lists allowed tools and explains repair_follow_on_refresh (commit 9460cc63)

## Structural Flaws (Addressed)

### FLAW-001: RC-002 — deterministic-refresh Injected as Stage Name
- **Severity**: MEDIUM — contaminates completed_stages
- **Location**: run_managed_repair.py
- **Fix**: Track as internal_only, not as a stage (commit 906dc002)

### FLAW-002: RC-005 — WFLOW031 Predictive Repair Trap
- **Severity**: MEDIUM — agents fall into repair loops
- **Location**: team-leader template
- **Fix**: Added WFLOW031 anti-pattern guidance (commit 906dc002)

## Structural Flaws (Open)

### FLAW-003: RC-003 — asserted_completed_stages Not Re-validated
- **Severity**: LOW — historical assertions accepted without re-check
- **Status**: OPEN (low priority)
- **Notes**: Only matters if assertions were wrong; current agents seem to handle correctly

### FLAW-004: RC-006 — Backward Routing During managed_blocked
- **Severity**: LOW — backward skill routing doesn't account for blocked state
- **Status**: OPEN (low priority)

### FLAW-005: RC-008 — Python-Only Validation Gap for Godot
- **Severity**: MEDIUM — smoke test validation is Python-centric
- **Status**: OPEN
- **Notes**: Godot repos need headless export validation

### FLAW-006: RC-007 — Smoke Test Monolithic
- **Severity**: LOW — single monolithic test file
- **Status**: DEFERRED
- **Notes**: Not blocking current work

## Config Surface Issues (Handled by Audit)

### CONFIG-001 through CONFIG-005
- Model field presence and format validation
- default_agent presence
- external_directory permission
- bash command allowlist
- Wildcard bash allow detection
- All implemented in audit_config_surfaces.py
