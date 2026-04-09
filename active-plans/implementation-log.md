# Implementation Log

## Commits (Chronological)

### c7546b95 — Template opencode.jsonc + CONFIG audit
- **What**: Added model, default_agent, external_directory, bash allowlist to template opencode.jsonc. Created audit_config_surfaces.py with CONFIG001-005 checks. Wired into audit and disposition routing.
- **Why**: Downstream repos missing critical config fields. Audit had no way to detect config problems.
- **Evidence**: All 3 repos had incomplete opencode.jsonc; agents couldn't start properly.
- **Validates**: Repair now generates correct config; audit catches missing fields.

### 906dc002 — RC-001, RC-002, RC-005 fixes
- **What**: Added managed_blocked enforcement to stage-gate-enforcer (RC-001). Stopped injecting "deterministic-refresh" into completed_stages (RC-002). Added WFLOW031 anti-pattern guidance to team-leader template (RC-005).
- **Why**: managed_blocked was declared but not enforced; deterministic-refresh polluted stage tracking; agents fell into repair prediction loops.
- **Evidence**: Root cause analysis of agent loops and stuck states.
- **Validates**: Agents now blocked when they should be; stage tracking clean; team leader warned about repair traps.

### 03adb917 — Repair provenance round-trip + pivot normalization + audit depth
- **What**: Fixed load_metadata() to recover stack_label and product_finish_contract from bootstrap-provenance.json. Added pivot state normalization. Added model format and CONFIG005 audit checks.
- **Why**: Repair rendered "framework-agnostic" everywhere instead of actual stack labels. Pivot state inconsistencies blocked handoff.
- **Evidence**: Repair output showed wrong stack labels; provenance had correct data but wasn't being read.
- **Validates**: Repair now renders correct project-specific values.

### 6e9bb3dc — Exclude .venv/node_modules from copytree
- **What**: Added .venv*, node_modules, __pycache__ to shutil.copytree ignore patterns in repair.
- **Why**: .venv contains circular symlinks that crash copytree; node_modules and __pycache__ are never repair targets.
- **Evidence**: Repair crashed on GPTTalker with shutil.copytree error.
- **Validates**: Repair completes on repos with virtual environments.

### 7ead92e0 — Strip provider prefix from provenance model names
- **What**: Before re-rendering template, strip provider prefix from model names stored in provenance.
- **Why**: Provenance stores "provider/model" but template rendering prepends provider again.
- **Evidence**: Rendered output showed "minimax-coding-plan/minimax-coding-plan/MiniMax-M2.7".
- **Validates**: Model references in rendered output are correct.

### aad675cb — Widen venv exclusion pattern
- **What**: Changed .venv to .venv* in copytree ignore to catch .venv310, .venv312, etc.
- **Why**: Some repos use version-specific venv names.
- **Evidence**: Edge case found during testing.

### 686cc74a — CRITICAL: Add missing hasPendingRepairFollowOn import
- **What**: Added import of hasPendingRepairFollowOn to stage-gate-enforcer.ts.
- **Why**: RC-001 enforcement called this function but forgot to import it. Since the plugin runs before ALL tool calls, every single tool invocation crashed.
- **Evidence**: All 3 repos showed "hasPendingRepairFollowOn is not defined" on every tool call.
- **Validates**: Tool calls work again in all downstream repos.

### c8bb368f — Skip REMED-RELEASE-GATE creation when ticket exists
- **What**: Added existence check before creating REMED-RELEASE-GATE in apply_remediation_follow_up.py.
- **Why**: Re-running repair crashed with "Ticket already exists" at remediation ticket creation step.
- **Evidence**: Spinner and glitch repairs failed at this step.
- **Validates**: Repair is idempotent for ticket creation.

### 9460cc63 — Improve managed_blocked error message
- **What**: Changed BLOCKER message to list allowed tools, mention repair_follow_on_refresh, and explain how to handle host-agent skills.
- **Why**: Old message said "report to operator" — unhelpful for headless agents. Agents got stuck in loops.
- **Evidence**: GPTTalker agent tried artifact_write, task, ticket_claim repeatedly. Spinner agent figured it out by luck.
- **Validates**: Glitch agent immediately used repair_follow_on_refresh after seeing the improved message.

### 3464bd98 — Documentation: architecture.md + scafforge-context.json
- **What**: Added comprehensive architecture documentation and machine-readable context JSON.
- **Why**: Fast agent bootstrapping and human understanding of the system.
