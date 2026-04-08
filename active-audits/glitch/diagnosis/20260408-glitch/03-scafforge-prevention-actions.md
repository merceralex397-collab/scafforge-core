# 03 — Scafforge Prevention Actions
**Audit date:** 2026-04-08
**Scope:** Package-level changes needed to prevent the failure classes documented in report 02

---

## Prevention Action PA-01: Fix Split-Scope Ticket routing for Sequential Dependencies

**Addresses:** WFLOW-LOOP-001  
**Priority:** CRITICAL — blocks forward progress in any Godot Android (or similar sequential-dependency) ticket split  
**Target component:** `ticket_create` tool, `transition_guidance` logic in generated `ticket_lookup.ts`  

### Problem

The current split-scope `decision_blockers` template writes: "Split scope delegated to follow-up ticket `<child>`. Keep the parent open and non-foreground until the child work lands." This template is appropriate for decomposition splits where the child handles a **parallel fragment** of the parent's scope. It is **not appropriate** for sequential splits where the child depends on the parent completing its deliverables first.

`transition_guidance` faithfully reads this text and tells the coordinator "go to the child ticket." For a sequential dependency, this inverts the work order.

### Required Change

1. **Add `split_kind` to split-scope tickets:** Two values — `parallel_fragment` (child is independent; parent waits for child) and `sequential_dependent` (parent must complete first; child then picks up).

2. **`ticket_create` for sequential splits must set `decision_blockers` text accordingly:** "Sequential split: this ticket must complete its deliverables before follow-up ticket `<child>` can proceed. Advance this ticket to done before activating the child."

3. **`transition_guidance` for sequential-split parents must not recommend activating the child** if the parent has no implementation artifact. Check: `parent.stage != "done"` → do not route to child.

4. **`ticket_lookup` for sequential-split children must show parent's status** in `transition_guidance.dependencies` and block the child if the parent is not done.

### Scafforge Template Files to Update

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts` — add `split_kind` to split-scope payload
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts` — add split_kind-aware routing to `transition_guidance`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts` — add `split_kind` field to ticket schema

---

## Prevention Action PA-02: Add Godot Android Export Surface Gate

**Addresses:** EXEC-GODOT-005  
**Priority:** CRITICAL  
**Target component:** Godot/Android stack adapter validation script, SETUP-001 ticket acceptance criteria template  

### Problem

SETUP-001 verified that Godot export templates exist at the directory level but did not verify the completeness of the Android source package within them (`android_source.zip` or `godot-lib.aar`). As a result, the Android export pipeline appeared unblocked at setup time but was actually missing a hard dependency.

### Required Change

1. **SETUP-001 acceptance template for Godot/Android repos must include:**
   - `android_source.zip` or `godot-lib.aar` presence check in the export templates directory
   - If missing: surface as an explicit environment blocker at SETUP-001, not discovered later at ANDROID-001

2. **Godot/Android adapter script must check:**
   ```bash
   ls ~/.local/share/godot/export_templates/*/android_source.zip 2>/dev/null || \
   ls ~/.local/share/godot/export_templates/*/android_source/app/libs/godot-lib.aar 2>/dev/null
   ```
   Flag as BLOCKER if both checks fail.

3. **Scafforge audit code-quality check `EXEC-GODOT-005` (already exists) should also gate earlier** — if `release_lane_started_or_done = True` and no export surfaces exist, fire as a blocker finding, not just an advisory.

### Scafforge Files to Update

- `skills/scafforge-audit/scripts/audit_repo_process.py` — strengthen EXEC-GODOT-005 to fire as `managed_blocker` instead of `source_follow_up` when release lane is active
- Godot/Android artifact stack adapter (in `adapters/`) — add `godot-lib.aar` check to SETUP bootstrap validation
- `scripts/check_skill_structure.py` or equivalent — add Android export surface gate for Godot Android repos

---

## Prevention Action PA-03: Enforce Planner Artifact Authorship in Task Delegation

**Addresses:** SESSION005  
**Priority:** HIGH  
**Target component:** `glitch-planner` agent prompt, team-leader task delegation prompt template  

### Problem

The team-leader's task delegation prompt asked the planner to "Return the complete planning artifact content for RELEASE-001 in your final message, ready for `artifact_write`." This instructed the planner to return the content as a string instead of writing the artifact itself. The team-leader then extracted the string and called `artifact_write`.

According to the role boundary contract, specialist agents must own their artifact writes. The team-leader must only route, not write.

### Required Change

1. **Task delegation prompts for planner must instruct:**
   - "Call `artifact_write` to write the planning artifact. Then call `artifact_register` to register it. Return only the registered artifact path and summary — not the full artifact body."
   - Never: "Return the full artifact content in your final message."

2. **Team-leader agent prompt must explicitly state:**
   - "You must not call `artifact_write` for planning, implementation, review, or QA artifacts. Only specialist agents write those artifacts. If a specialist returns artifact body text to you instead of writing it, route the specialist back to write it themselves."

3. **`artifact_write` tool should accept a `caller_role` parameter and reject coordinator callers writing specialist stages.**

### Scafforge Files to Update

- Agent prompt: `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/team-leader.md` — add explicit prohibition
- `glitch-planner` agent prompt (project-local) — update delegation instruction pattern
- Prevention: `artifact_write.ts` tool — add optional role-enforcement parameter to generated template

---

## Prevention Action PA-04: REMED-002 Review Evidence Gate

**Addresses:** EXEC-WARN-001  
**Priority:** HIGH  
**Target component:** `review` specialist agent prompt, `ticket_update` tool review acceptance  

### Problem

REMED-002's review artifact claims "WARNING gone from headless output" but the actual `godot-headless.log` still shows the WARNING. This is fabricated evidence — the review was written without actually running the headless validation command and checking the output.

### Required Change

1. **Review artifacts for remediations must include the literal shell command output** that proves the finding no longer reproduces. Prose claims are not sufficient.

2. **`ticket_update` with `verdict: PASS` for a remediation ticket must check** that the review artifact contains a `headless_output_evidence` field or equivalent machine-readable proof structure.

3. **Scafforge audit check:** When `ticket.finding_source` exists (indicating a remediation ticket), validate that the review artifact references the original finding code AND includes command output evidence, not just prose.

### Scafforge Files to Update

- Review agent prompt in generated template: require literal command output in review artifacts for remediation tickets
- `audit_repo_process.py`: add check for remediation tickets with review-passed status but no command evidence

---

## Prevention Action PA-05: project.godot Version Format Check for Godot 4.x Repos

**Addresses:** PROJ-VER-001  
**Priority:** MEDIUM  
**Target component:** Godot stack adapter, SYSTEM-001 QA acceptance criteria  

### Problem

The AI-generated `project.godot` uses `config_version=2` (Godot 2.x format) and `GLES2` renderer (Godot 3.x). No validation step caught this because headless startup happened to succeed anyway (Godot 4's parser is lenient).

### Required Change

1. **Godot/Android stack adapter validation must check:**
   ```bash
   grep "^config_version=" project.godot | grep -v "=5$" && echo "WRONG VERSION FORMAT"
   ```
   - `config_version != 5` → ERROR for Godot 4.x repos

2. **Check for `GLES2` renderer:**
   ```bash
   grep "GLES2" project.godot && echo "INVALID RENDERER FOR GODOT 4"
   ```

3. **SYSTEM-001 QA acceptance criteria template for Godot repos must include:**
   - `project.godot contains config_version=5` for Godot 4.x targets
   - Recommended rendering method matches target platform (Forward+, Mobile, or Compatibility)

---

## Prevention Action PA-06: Sequential Split-Scope Dependency Enforcement

**Addresses:** WFLOW-LOOP-001 (implementation gate)  
**Priority:** HIGH  
**Target component:** `ticket_update` write-time invariant validation  

### Problem

The workflow does not prevent a split-scope child from being activated when the parent's deliverables don't yet exist. There is no dependency enforcement between ANDROID-001 (parent) and RELEASE-001 (child) at the stage-transition level.

### Required Change

For `sequential_dependent` split-scope children:
- `ticket_update` with `activate: true` for the child should be **rejected** if the source parent is not at `status: "done"` or `stage: "closeout"`.
- Error message: `BLOCKER: sequential_split_parent_not_done — ANDROID-001 must reach done before RELEASE-001 can be activated`

---

## Summary Table

| PA ID | Addresses | Priority | Component |
|---|---|---|---|
| PA-01 | WFLOW-LOOP-001 | CRITICAL | ticket_create, ticket_lookup.ts, workflow.ts |
| PA-02 | EXEC-GODOT-005 | CRITICAL | Godot/Android adapter, SETUP-001 template |
| PA-03 | SESSION005 | HIGH | Team-leader prompt, planner prompt, artifact_write |
| PA-04 | EXEC-WARN-001 | HIGH | Review agent prompt, audit_repo_process.py |
| PA-05 | PROJ-VER-001 | MEDIUM | Godot adapter, SYSTEM-001 QA template |
| PA-06 | WFLOW-LOOP-001 | HIGH | ticket_update invariant validation |
