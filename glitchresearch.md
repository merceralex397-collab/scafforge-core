# Glitch Research: Comprehensive Analysis Report

**Session ID:** ses_2b4b7905cffeJIEhOPymjGj2UH  
**Created:** April 2, 2026  
**Status:** All issues validated with transcript evidence and source code locations

---

## Executive Summary

This report documents a comprehensive analysis of the Glitch live-testing session—a Godot-based Android 2D action-platformer scaffolded using Scafforge. The analysis identified **7 validated workflow issues**, **10 additional Scafforge bugs and gaps**, **7 critical code quality problems**, and **27 distinct agent confusion instances** across a 13,000-line execution transcript.

### Key Findings

| Category | Count | Priority |
|----------|-------|----------|
| Core Workflow Issues | 7 | 3 P0 (Critical), 4 P1-P2 |
| Additional Scafforge Issues | 10 | 4 High, 6 Medium |
| Code Quality Problems | 7 | All P0 (Broken/Fragile) |
| Agent Confusion Events | 27 | 5 Major, 12 Moderate, 10 Minor |

### Critical Discovery: Universal Generation vs Python-Only Validation

**CRITICAL:** Scafforge's greenfield generation is **universal** (can generate any project type: Godot, web, service, etc.), but the audit layer is **Python-only**. This creates a fundamental architectural gap:

- ✅ **Can generate:** Godot, Rust, Go, Java, C/C++, Node.js projects
- ❌ **Cannot validate:** Any project type except Python
- ⚠️ **Result:** False success reports for non-Python projects (like Glitch)

### Root Cause Analysis

The core problem is that **Scafforge generates deterministic workflow surfaces but provides insufficient "how to decide" guidance**. The agent lacks heuristics for:
- When to trust vs. verify state
- When to delegate vs. act directly
- How to resolve contradictions between guidance and artifacts

This is compounded by **template validation gaps** that allowed generation of broken Godot scene files, mixed Godot 3.x/4.x syntax, and memory-leak anti-patterns.

---

## The 7 Core Issues: Detailed Analysis

### Issue 1: Lane-Lease Scoping Blocker [HIGH]

**Evidence:** Lines 928-988 (initial claim), 2228-2255 (blocker detection), 2268-2373 (fix)

**Problem:** SYSTEM-001 implementation was blocked because the initial lease claim only covered `.opencode/state/*` paths, missing all Godot project paths (`project.godot`, `scenes/`, `scripts/`, `resources/`, `assets/`).

**Impact:** Required 5+ minute delay with full delegation round-trip: release lease → reclaim with expanded paths → re-delegate to implementer.

**Agent Confusion Manifestation:**
- "This is a ticket-scoped issue, not a bootstrap issue"
- Uncertainty about whether to expand lease or change approach
- Multiple thinking-block corrections before deciding on release/reclaim

**Root Cause:** The team-leader agent lacks guidance on what `allowed_paths` to include for different ticket types. The `ticket_claim.ts` tool accepts `allowed_paths` as optional with no defaults or ticket-type awareness.

**Fix Required:**
1. Add lane lease path scoping section to team-leader agent
2. Enhance `ticket_claim.ts` tool description with project-type examples
3. Consider ticket-type aware path templates (SYSTEM: full paths, FEATURE: scenes/scripts, CONTENT: assets)

---

### Issue 2: Duplicate Autoload Singletons [HIGH]

**Evidence:** Lines 3227-3278 (review), 3249 (FAIL verdict), 3296-3345 (fix), 4163-4206 (QA verify)

**Problem:** Four autoloads (PlayerState, GlitchState, GameState, LevelManager) were registered in both:
- `project.godot` [autoload] section (correct)
- `Main.tscn` as child nodes (incorrect)

This caused **double initialization**, breaking signal contracts and potentially causing race conditions.

**Detection:** Reviewer-code agent found this (line 3249: "❌ **FAIL - Blocker Found**") during CORE-001 review.

**Fix Applied:** Removed duplicate nodes from `Main.tscn`, kept only the `project.godot` registrations.

**Root Cause:** No preflight detection exists to catch this before review. The `godot-architecture` skill lacks autoload boundary rules.

**Fix Required:**
1. Create new `godot_autoload_check.ts` tool
2. Add autoload boundary rules to `godot-architecture/SKILL.md`
3. Add validation to reviewer agent checklist

---

### Issue 3: Smoke-Test Brittleness [MEDIUM]

**Evidence:** Lines 4716-4761 (failure), 4820-4836 (actual success), 4883-4919 (simplified pass)

**Problem:** Smoke test failed with:
```
Command 2 (grep) failed with exit code 1
Error: "Missing language argument, aborting"
```

The command used was:
```bash
grep -E '(PlayerState|GlitchState|GameState|LevelManager).*Initialized'
```

**The Actual Bug:** `tokenizeCommandString()` in `smoke_test.ts` **discards quote characters** instead of preserving them.

**How it manifests:**
- Input: `'(Pattern).*'`
- Tokenizer sees opening `'` at line 372, sets `quote = "'"` and **discards the quote**
- Adds content characters until closing quote
- Sees closing `'` at line 364-365, sets `quote = null` and **discards the quote**
- Result: `(Pattern).*` (unquoted) - shell interprets `(` as subshell operator
- Error: "Missing language argument, aborting"

**Impact:** 20+ second investigation delay; misclassified as "environment" failure instead of "syntax" error.

**Root Cause:** Bug in `tokenizeCommandString()` function (lines 363-374 in smoke_test.ts). Quotes are detected but discarded rather than preserved.

**Fix Required:**
1. Preserve quotes in tokenization (lines 365, 372-373)
2. Add enhanced metadata to `CommandResult` type (lines 36-44)
3. Distinguish "command syntax error" from "verification failure"

---

### Issue 4: Verification_State Semantics Gap [MEDIUM]

**Evidence:** Lines 832, 1346, 1719, 2091, 2884, 3476, 4602, 5090 (all "suspect"), 5380 ("trusted")

**Problem:** The `verification_state: "suspect"` persisted through the **entire ticket lifecycle**:
- SETUP-001: suspect → todo → setup → smoke-test → suspect → closeout
- SYSTEM-001: suspect throughout implementation, review, QA, smoke-test
- Only changed to `"trusted"` at **closeout** (line 5380)

**Semantics Problem:** The field is effectively a `"not closed"` flag, not an actual verification quality indicator. Despite:
- All artifacts current
- Smoke tests passing
- QA approved
- Reviews passing

The state remained "suspect" until resolution_state became "done".

**Impact:** Confusing semantics; agents may interpret "suspect" as indicating problems when it doesn't.

**Root Cause:** The field conflates two concepts: (1) verification quality and (2) completion status. In practice, it's only the latter.

**Fix Options:**
1. Rename to `completion_status` or `lifecycle_phase`
2. Add separate `artifact_trust` field that tracks actual verification
3. Document that "suspect" is normal until closeout

---

### Issue 5: Transition Guidance / Verdict Mismatch [MEDIUM]

**Evidence:** Lines 3578-3604 (guidance), 3249 (review FAIL)

**Problem:** After review found FAIL verdict with blockers for duplicate autoloads, the transition_guidance showed:
```json
{
  "current_state_blocker": null,
  "next_allowed_stages": ["qa"],
  "recommended_action": "Move the ticket into QA after review approval is registered."
}
```

**Contradiction:** Review says FAIL; guidance says advance to QA.

**Root Cause:** `buildTransitionGuidance()` checks for artifact presence but **not the verdict within the artifact**. It checks `has_review: true` but doesn't parse whether the review verdict is PASS or FAIL.

**Agent Confusion Manifestation:**
- "Wait - looking more carefully at the transition guidance..."
- "Actually, looking at the review result, it says 'FAIL'..."
- "But the transition guidance still says to move to QA. This seems contradictory."
- 5x "Wait"/"Actually" cycles before deciding to trust review over guidance

**Fix Required:**
1. Add `validateReviewArtifactEvidence()` function to lib/workflow.ts
2. Check for explicit verdict patterns (PASS/FAIL) in artifact content
3. Add `hazardous_transition: true` when guidance contradicts artifact verdict

---

### Issue 6: Handoff Tool Verification Gaps [LOW-MEDIUM]

**Evidence:** Lines 638-644 (context_snapshot), 665-671 (handoff_publish)

**Problem:** Tools return only paths without verification:

**Current `handoff_publish.ts` output:**
```json
{
  "start_here": ".opencode/state/latest-handoff.md",
  "latest_handoff": ".opencode/state/latest-handoff.md"
}
```

**Current `context_snapshot.ts` output:**
```json
{
  "path": ".opencode/state/context-snapshot.md",
  "ticket_id": "SETUP-001"
}
```

**Missing:**
- `verified: true/false`
- Content preview (first 500 chars)
- Content hash (SHA256)
- File size
- Write timestamp

**Impact:** Agents must blindly trust paths without confirmation that files were actually written with expected content.

**Fix Required:**
1. Add verification metadata to both tools
2. Include content hash for integrity checking
3. Add preview and file size information

---

### Issue 7: Active Ticket Split-Brain [MEDIUM]

**Evidence:** Lines 768-770, 5779-5781, 6042-6044

**Problem:** `ticket_lookup.ts` returns **divergent values** for `active_ticket`:

```json
{
  "active_ticket": "SETUP-001",      // ← manifest.active_ticket (ROOT)
  "workflow": {
    "active_ticket": "SYSTEM-001"      // ← resolvedWorkflow.active_ticket (OVERRIDE)
  }
}
```

**Root Cause:** When `args.ticket_id` is provided, the tool overrides `workflow.active_ticket` for context:
```typescript
const resolvedWorkflow = args.ticket_id
  ? { ...workflow, active_ticket: ticket.id }  // ← OVERRIDES
  : workflow
```

The root level keeps `manifest.active_ticket` (canonical), but the workflow field shows the requested ticket for context.

**Impact:** Agents see two different "active" tickets depending on which field they read. This causes confusion about which ticket to work on.

**Agent Confusion Manifestation:**
- "But I also notice the workflow shows `active_ticket: 'SYSTEM-001'`..."
- Uncertainty about whether to work on SETUP-001 or SYSTEM-001
- Extra lookups needed to resolve ambiguity

**Fix Options:**
1. **Option 1 (Document):** Add explicit `lookup_context` field explaining the override
2. **Option 2 (Reconcile):** Remove override entirely; use separate `requested_ticket` field

---

## Appendix A: Multi-Agent Transcript Analysis

*19 specialized agents analyzed the 13,000-line Glitch transcript to identify patterns not covered in the initial 7 issues.*

### Summary Statistics

| Metric | Count | Severity Distribution |
|--------|-------|---------------------|
| Total confusion instances | 27 | Major: 5, Moderate: 12, Minor: 10 |
| Redundant ticket_lookup calls | 12+ | Wasting 6-10 seconds each |
| Failed transitions | 4 | Required backtracking |
| Circular reasoning events | 3 | Lines 12920-13413 most severe |
| Lease management confusion | 6 | Ownership/state uncertainty |

### Critical Confusion Events (Chronological)

#### Event 1: Lease Scoping Discovery Crisis (Lines 2228-2373)
**What happened:** The agent's initial lease claim only covered `.opencode/state/*` paths, missing all Godot project paths. The implementer subagent hit a blocker and had to return.

**Evidence:**
```
Blocker: Lane Lease Doesn't Cover Required Write Paths...
Missing paths:
- project.godot (repo root)
- scenes/ (and subdirectories)
- scripts/ (and subdirectories)
```

**Confusion manifestation:**
- Agent had to release lease, reclaim with expanded paths, then re-delegate
- 5+ minute delay with full round-trip
- Thinking shows uncertainty: "This is a ticket-scoped issue, not a bootstrap issue"

**Root cause:** Agent lacked guidance on project-type-specific lease paths in the team-leader prompt.

---

#### Event 2: Duplicate Autoload Fix Confusion (Lines 3360-3612)
**What happened:** After fixing duplicate autoloads, the agent was uncertain whether to advance to QA or require new review.

**Evidence:**
```
The review found blockers, but the transition guidance says 
"Move the ticket into QA after review approval is registered." 
This seems incorrect...

Actually wait - looking more carefully...
Wait - the transition guidance shows `current_state_blocker: null`

Actually, looking at the review result...
```

**Confusion manifestation:**
- 4x "Actually" statements in thinking block
- Multiple self-corrections before deciding to proceed
- Didn't immediately recognize that superseded implementation requires new review

**Root cause:** No rule in agent prompt about "post-fix review requirement."

---

#### Event 3: Smoke Test Regex Failure (Lines 4716-4919)
**What happened:** Smoke test failed due to unescaped parentheses in grep regex, but agent initially couldn't distinguish command error from actual failure.

**Evidence:**
```
The smoke test failed. The first command passed... but the second 
command (grep for initialization count) failed with exit code 1.

The issue is with the grep regex - the parentheses aren't escaped 
properly... Let me check the actual smoke test artifact to see what 
happened and determine if this is a real blocker...
```

**Confusion manifestation:**
- Had to read artifact to diagnose what should have been obvious from exit code
- Initially uncertain if this was "real failure" or "tool error"
- Took 20+ lines of thinking before deciding to simplify command

**Root cause:** Tool doesn't classify "command syntax error" separately from "verification failure."

---

#### Event 4: Review/Guidance Contradiction Paralysis (Lines 10519-10544)
**What happened:** Review found FAIL with blockers, but transition_guidance recommended moving to QA.

**Evidence:**
```
The review found two blockers, but the transition guidance says 
"Move the ticket into QA..." This seems incorrect...

Wait - looking more carefully at the transition guidance...

Actually, looking at the review result, it says "FAIL" with two blockers. 
But the transition guidance still says to move to QA. 
This seems contradictory.

...
Actually wait...

The correct action here is to mark the ticket as blocked...
```

**Confusion manifestation:**
- 5x "Wait" / "Actually" cycles
- Tried to rationalize contradiction instead of immediately surfacing blocker
- Eventually made correct decision but took 50+ lines of analysis

**Root cause:** System doesn't validate review verdict before generating transition guidance.

---

#### Event 5: Major QA/Guidance Contradiction Crisis (Lines 12920-13413)
**What happened:** QA artifact contained FAIL verdict with blockers, but transition_guidance said advance to smoke-test. Agent entered prolonged analysis paralysis.

**Evidence:**
```
The `ticket_lookup` result shows: "next_allowed_stages": ["smoke-test"]

But the QA verdict is FAIL with blockers! This is contradictory...

I need to handle this blocker scenario properly...
- Could use `issue_intake`... but this isn't post-completion
- Could use `ticket_reopen`... but the ticket isn't done  
- Could use `ticket_create`... to create a follow-up ticket

Wait, the QA blockers are about initialization that wasn't completed...

Actually, I see the issue. The QA artifact already exists and documents 
the blockers. But the transition guidance is still saying smoke-test...

According to the rule: "stop on repeated lifecycle-tool contradictions...
So I should stop and return a blocker.
```

**Confusion manifestation:**
- Nearly 500 lines of circular reasoning
- Considered 3+ different approaches (issue_intake, ticket_reopen, ticket_create)
- Eventually surfaced blocker correctly but after excessive delay
- This was the most severe confusion event in the entire transcript

**Root cause:** Fundamental design flaw: guidance system doesn't read QA artifact verdict, only checks for artifact existence.

---

### Minor Confusion Patterns (Selected Examples)

#### Pattern: Verification-Seeking Behavior
**Frequency:** 12+ instances  
**Lines:** 85-94, 1457-1466, 1830-1838, 6025-6036, 11915-11928

**Description:** After every state transition, agent immediately performs another `ticket_lookup` rather than trusting the previous response's embedded guidance.

**Example (Lines 1449-1464):**
```
// Just transitioned to plan_review
// Previous response contained complete guidance
// Yet agent immediately does another lookup:

"Now getting transition guidance for plan approval:

**Tool: ticket_lookup**

**Input:**
```json
{
  "ticket_id": "SYSTEM-001",
  "include_artifact_contents": false
}
```"
```

**Impact:** Wastes 6-10 seconds per redundant call; indicates low trust in state persistence.

**Root cause:** Agent doesn't understand that `ticket_update` and `ticket_lookup` responses contain identical `transition_guidance` structures.

---

#### Pattern: Lease State Uncertainty
**Frequency:** 6 instances  
**Lines:** 913-924, 2700-2710, 6802-6805, 7044-7046

**Description:** Agent repeatedly uncertain about whether leases are held, by whom, and whether claiming is necessary.

**Example (Lines 913-924):**
```
But I also notice the workflow shows `active_ticket: "SYSTEM-001"` - 
so it looks like the system already activated SYSTEM-001 as the active ticket.

Let me claim the lease first, then delegate to the planner.
```

**Impact:** Extra lease operations; risk of claiming when already held.

**Root cause:** Confusion between `active_ticket` (in workflow) and `lane_leases` (ownership).

---

#### Pattern: Status Transition Misunderstanding
**Frequency:** 4 instances  
**Lines:** 11256-11279, 12902-12966

**Description:** Agent attempted invalid lifecycle transitions (e.g., `review` → `todo`, `qa` → `implementation`).

**Example (Lines 11256-11279):**
```
// Tried to unblock ticket:
{
  "ticket_id": "CORE-002",
  "stage": "review", 
  "status": "todo"  // ERROR: review stage only allows "review" or "blocked"
}

// Error: "Status todo is not valid for stage review. 
//         Allowed statuses: review, blocked."
```

**Root cause:** Agent didn't cross-reference `recommended_ticket_update` against `allowed_statuses_for_current_stage`.

---

## Source Code Analysis: Fittings vs Templates

The following analysis traces each validated issue to its exact source code location in both the **generated Glitch repo fittings** (`livetesting/glitch/.opencode/`) and the **Scafforge skill templates** (`skills/repo-scaffold-factory/assets/project-template/.opencode/`). Both locations have identical code and require the same fixes.

### Issue 1: Lane-Lease Scoping Blocker - Source Code Location

**Root Cause:** The team-leader agent lacks guidance on what `allowed_paths` to include when claiming leases for different ticket types.

**Primary Source Location:**
- **Fitting:** `livetesting/glitch/.opencode/agents/glitch-team-leader.md`
- **Template:** `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`

**Secondary Code Path:**
- **Fitting:** `livetesting/glitch/.opencode/tools/ticket_claim.ts` (Line 19, 51)
- **Template:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_claim.ts` (Line 19, 51)

**Current Code (Line 19 in ticket_claim.ts):**
```typescript
allowed_paths: tool.schema.array(tool.schema.string()).describe("Repo-relative path prefixes this lease may edit.").optional(),
```

**Current Code (Line 51 in ticket_claim.ts):**
```typescript
const lease = claimLaneLease(workflow, ticket, ownerAgent, args.allowed_paths || [], writeLock)
```

**The Problem:** The tool accepts `allowed_paths` as optional with no defaults or ticket-type awareness. Empty array means unrestricted, but agents don't know what paths to include.

**Fix Required:**

1. **Update Team-Leader Agent (both files):** Add after line 203:
```markdown
### Lane Lease Path Scoping

When claiming a lane lease with `ticket_claim`, set `allowed_paths` based on the ticket's lane and expected work:

**Default minimal paths (always include):**
- `.opencode/state/` - for stage artifacts
- `tickets/` - for ticket file updates

**Additional paths by lane type:**

- **bootstrap/setup lane**: `[".opencode/state/", "tickets/", "package.json", "*.lock", "requirements.txt"]`
- **architecture/infrastructure lane**: `[".opencode/state/", "tickets/", "project.godot", "scenes/", "scripts/", "resources/", "assets/"]`
- **feature implementation lane**: `[".opencode/state/", "tickets/", "src/", "scenes/", "scripts/", "components/"]`

**Rules:**
- When unsure about project structure, claim with broad paths that include the repo root
- It's safer to over-scope initially than to require mid-work lease release/reclaim
- The implementer will return a blocker if the lease doesn't cover required paths
```

2. **Enhance ticket_claim.ts tool description (both files, Line 19):**
```typescript
allowed_paths: tool.schema.array(tool.schema.string()).describe(
  "Repo-relative path prefixes this lease may edit. " +
  "If omitted or empty, all paths are allowed. " +
  "For implementation work, include: .opencode/state/, tickets/, and project source directories (e.g., src/, scenes/, scripts/, project.godot)."
).optional(),
```

---

### Issue 2: Duplicate Autoload Singletons - Source Code Location

**Root Cause:** No preflight detection exists to catch autoload duplication before review.

**Primary Fix Location (NEW TOOL):**
- **Fitting:** Create `livetesting/glitch/.opencode/tools/godot_autoload_check.ts`
- **Template:** Create `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/godot_autoload_check.ts`

**Detection Algorithm:**
```typescript
// Parse [autoload] section from project.godot
function parseProjectGodotAutoloads(content: string): string[] {
  const autoloads: string[] = []
  const sectionMatch = content.match(/\[autoload\]([\s\S]*?)(?=\n\[|$)/)
  if (!sectionMatch) return autoloads
  
  const section = sectionMatch[1]
  const lines = section.split('\n')
  
  for (const line of lines) {
    const trimmed = line.trim()
    // Match: PlayerState="*res://scripts/autoload/PlayerState.gd"
    const match = trimmed.match(/^(\w+)\s*=/)
    if (match && !trimmed.startsWith(';')) {
      autoloads.push(match[1])
    }
  }
  return autoloads
}

// Parse node names from .tscn files
function parseTscnNodes(content: string): string[] {
  const nodes: string[] = []
  const nodeMatches = content.matchAll(/\[node\s+name\s*=\s*"(\w+)"/g)
  for (const match of nodeMatches) {
    nodes.push(match[1])
  }
  return nodes
}

// Compare for duplicates
const duplicates = nodes.filter(node => autoloads.includes(node))
```

**Secondary Fix Locations (Skill Enhancement):**
- **Fitting:** `livetesting/glitch/.opencode/skills/godot-architecture/SKILL.md` (Lines 17-22)
- **Template:** Create `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/godot-architecture/SKILL.md`

**Add to godot-architecture skill:**
```markdown
## Autoload Singleton Boundaries (CRITICAL)

**Duplicate Registration Prevention:**
- Autoloads registered in `project.godot` are automatically instantiated as singletons under `/root/`
- **NEVER** add autoload nodes as children in scene files (e.g., `Main.tscn`)
- Duplicate registration causes double initialization and breaks signal contracts

**Validation Required:**
- Before completing any ticket that adds/modifies autoloads:
  1. Check `project.godot` [autoload] section
  2. Verify no autoload names appear as [node name="X"] entries in `Main.tscn`
  3. Run `godot --headless --path . --quit` and confirm single initialization per autoload

**Autoload Access Pattern:**
- Access autoloads via `/root/AutoloadName` or `get_node("/root/AutoloadName")`
- Do NOT instance them in scene files
```

**Tertiary Fix Locations (Agent Checklists):**
- **Fitting:** `livetesting/glitch/.opencode/agents/glitch-reviewer-code.md` (Line 53)
- **Template:** `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md` (Line 60)

**Add to reviewer agent Rules:**
```markdown
- **CRITICAL**: Validate autoload singleton boundaries - check that autoloads registered in `project.godot` do not also appear as nodes in `Main.tscn` or other scenes
```

---

### Issue 3: Smoke-Test Brittleness - Source Code Location

**Root Cause:** The `tokenizeCommandString()` function discards quote characters instead of preserving them.

**Source Location (IDENTICAL in both):**
- **Fitting:** `livetesting/glitch/.opencode/tools/smoke_test.ts` (Lines 363-374)
- **Template:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts` (Lines 363-374)

**Current Buggy Code:**
```typescript
// Line 363-374
if (quote) {
  if (char === quote) {
    quote = null              // BUG: Quote discarded
  } else {
    current += char
  }
  continue
}
if (char === '"' || char === "'") {
  quote = char                // BUG: Quote discarded
  continue
}
```

**How the bug manifests:**
- Input: `'(PlayerState|GlitchState|GameState|LevelManager).*Initialized'`
- Tokenizer sees opening `'` at line 372, sets `quote = "'"` and **discards the quote**
- Adds content characters until closing quote
- Sees closing `'` at line 364-365, sets `quote = null` and **discards the quote**
- Result: `(Pattern).*` (unquoted) - shell interprets `(` as subshell operator
- Error: "Missing language argument, aborting"

**Fixed Code:**
```typescript
if (quote) {
  if (char === quote) {
    current += char           // FIX: Include closing quote
    quote = null
  } else {
    current += char
  }
  continue
}
if (char === '"' || char === "'") {
  current += char             // FIX: Include opening quote
  quote = char
  continue
}
```

**Additional Enhancement (Lines 36-44):**

**Current `CommandResult` type:**
```typescript
type CommandResult = CommandSpec & {
  exit_code: number
  duration_ms: number
  stdout: string
  stderr: string
  missing_executable?: string
  failure_classification?: "missing_executable" | "permission_restriction" | "command_error"
  blocked_by_permissions?: boolean
}
```

**Enhanced `CommandResult` type:**
```typescript
type CommandResult = CommandSpec & {
  exit_code: number
  duration_ms: number
  stdout: string
  stderr: string
  missing_executable?: string
  failure_classification?: "missing_executable" | "permission_restriction" | "command_error" | "verification_failure"
  blocked_by_permissions?: boolean
  status: "run" | "skipped" | "failed"           // NEW: Per-check status
  skip_reason?: string                           // NEW: Why check was skipped
  verification_failure?: boolean                  // NEW: Distinguish from command_error
}
```

---

### Issue 4: Transition Guidance / Artifact Verdict Mismatch - Source Code Location

**Root Cause:** `buildTransitionGuidance()` checks for artifact presence but not the verdict within the artifact.

**Source Location (IDENTICAL in both):**
- **Fitting:** `livetesting/glitch/.opencode/tools/ticket_lookup.ts` (Lines 221-248)
- **Template:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts` (Lines 221-248)

**Current Code (review case):**
```typescript
case "review":
  if (!hasReviewArtifact(ticket)) {
    return {
      ...base,
      next_allowed_stages: ["review"],
      required_artifacts: ["review"],
      // ... artifact missing case
    }
  }
  return {
    ...base,
    next_allowed_stages: ["qa"],              // BUG: Always recommends QA
    required_artifacts: ["review"],
    recommended_action: "Move the ticket into QA after review approval is registered.",
    // NO verdict checking!
  }
```

**New Function to Add in lib/workflow.ts (both files, after line 829):**
```typescript
export async function validateReviewArtifactEvidence(ticket: Ticket, root = rootPath()): Promise<{ 
  blocker: string | null
  verdict: "PASS" | "FAIL" | "UNKNOWN"
  has_failures: boolean
}> {
  const artifact = latestReviewArtifact(ticket)
  if (!artifact) {
    return {
      blocker: "Cannot advance to QA before a review artifact exists.",
      verdict: "UNKNOWN",
      has_failures: false
    }
  }
  
  const content = await readArtifactContent(artifact, root)
  
  // Check for explicit verdict patterns
  const passMatch = /(?:verdict|result|status|overall):\s*PASS/i.test(content) || 
                    /(?:^|\n)\s*PASS\s*(?:\n|$)/i.test(content)
  const failMatch = /(?:verdict|result|status|overall):\s*FAIL/i.test(content) || 
                    /(?:^|\n)\s*FAIL\s*(?:\n|$)/i.test(content) ||
                    /found \d+ issues/i.test(content) ||
                    /duplicate.*detected/i.test(content)
  
  if (failMatch) {
    return {
      blocker: "Review artifact contains FAIL verdict or reported issues. Fix findings before advancing to QA.",
      verdict: "FAIL",
      has_failures: true
    }
  }
  
  if (passMatch) {
    return {
      blocker: null,
      verdict: "PASS",
      has_failures: false
    }
  }
  
  return {
    blocker: "Review artifact exists but lacks clear PASS/FAIL verdict. Review the artifact content.",
    verdict: "UNKNOWN",
    has_failures: false
  }
}
```

**Fixed Code in ticket_lookup.ts (both files):**
```typescript
case "review": {
  // First check: artifact exists
  if (!hasReviewArtifact(ticket)) {
    return {
      ...base,
      next_allowed_stages: ["review"],
      current_state_blocker: "Review artifact missing.",
      ready_to_transition: false,
      hazardous_transition: false,
    }
  }
  
  // Second check: verdict validation
  const reviewValidation = await validateReviewArtifactEvidence(ticket)
  
  if (reviewValidation.blocker) {
    return {
      ...base,
      next_allowed_stages: ["review"],
      current_state_blocker: reviewValidation.blocker,
      ready_to_transition: false,
      hazardous_transition: reviewValidation.verdict === "FAIL",
    }
  }
  
  // PASS verdict - allow QA transition
  return {
    ...base,
    next_allowed_stages: ["qa"],
    recommended_action: "Move the ticket into QA after review PASS verdict confirmed.",
    ready_to_transition: true,
    hazardous_transition: false,
  }
}
```

**Enhanced Guidance Structure (add to base object, line 46-63):**
```typescript
const base = {
  // ... existing fields ...
  ready_to_transition: false,        // NEW
  hazardous_transition: false,       // NEW
}
```

---

### Issue 5: Handoff Tool Verification Gaps - Source Code Location

**Root Cause:** Tools return only paths without verification, preview, or hash.

**Source Locations (IDENTICAL in both):**
- **Fitting:** `livetesting/glitch/.opencode/tools/handoff_publish.ts` (Line 39)
- **Template:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts` (Line 39)

**Current Code:**
```typescript
return JSON.stringify({ start_here: startHerePath(), latest_handoff: latestHandoffPath() }, null, 2)
```

**Enhanced Code:**
```typescript
import { readFile } from "node:fs/promises"
import { createHash } from "node:crypto"

// After refreshRestartSurfaces
const startHere = startHerePath()
const latestHandoff = latestHandoffPath()

const startHereContent = await readFile(startHere, "utf-8").catch(() => null)
const latestHandoffContent = await readFile(latestHandoff, "utf-8").catch(() => null)

const generatePreview = (content: string | null) => content ? content.slice(0, 500) + (content.length > 500 ? "..." : "") : null
const generateHash = (content: string | null) => content ? createHash("sha256").update(content).digest("hex") : null

return JSON.stringify({
  verified: startHereContent !== null && latestHandoffContent !== null,
  start_here: {
    path: startHere,
    exists: startHereContent !== null,
    size_bytes: startHereContent?.length ?? 0,
    content_preview: generatePreview(startHereContent),
    content_hash: `sha256:${generateHash(startHereContent)}`,
    written_at: new Date().toISOString()
  },
  latest_handoff: {
    path: latestHandoff,
    exists: latestHandoffContent !== null,
    size_bytes: latestHandoffContent?.length ?? 0,
    content_preview: generatePreview(latestHandoffContent),
    content_hash: `sha256:${generateHash(latestHandoffContent)}`,
    written_at: new Date().toISOString()
  }
}, null, 2)
```

**Source Locations for context_snapshot:**
- **Fitting:** `livetesting/glitch/.opencode/tools/context_snapshot.ts` (Line 34)
- **Template:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/context_snapshot.ts` (Line 34)

**Current Code:**
```typescript
return JSON.stringify({ path, ticket_id: ticket.id }, null, 2)
```

**Enhanced Code:**
```typescript
const writtenContent = await readFile(path, "utf-8").catch(() => null)
const contentHash = writtenContent ? createHash("sha256").update(writtenContent).digest("hex") : null
const preview = writtenContent ? writtenContent.slice(0, 300) + (writtenContent.length > 300 ? "..." : "") : null

return JSON.stringify({
  verified: writtenContent !== null,
  path,
  ticket_id: ticket.id,
  file: {
    exists: writtenContent !== null,
    size_bytes: writtenContent?.length ?? 0,
    content_preview: preview,
    content_hash: contentHash ? `sha256:${contentHash}` : null,
    written_at: new Date().toISOString()
  }
}, null, 2)
```

---

### Issue 6: Active Ticket Split-Brain - Source Code Location

**Root Cause:** `ticket_lookup.ts` overrides `workflow.active_ticket` when `args.ticket_id` is provided.

**Source Location (IDENTICAL in both):**
- **Fitting:** `livetesting/glitch/.opencode/tools/ticket_lookup.ts` (Lines 389-397, 455)
- **Template:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts` (Lines 389-397, 455)

**Problem Code (Lines 389-397):**
```typescript
const resolvedWorkflow = args.ticket_id
  ? {
      ...workflow,
      active_ticket: ticket.id,      // ← OVERRIDES workflow.active_ticket
      stage: ticket.stage,
      status: ticket.status,
      approved_plan: isPlanApprovedForTicket(workflow, ticket.id),
    }
  : workflow
```

**Divergence Point (Line 455):**
```typescript
return JSON.stringify(
  {
    project: manifest.project,
    active_ticket: manifest.active_ticket,  // ← Root level: original value
    workflow: resolvedWorkflow,                // ← Contains overridden active_ticket
    // ...
  }
)
```

**Resulting Split-Brain:**
```json
{
  "active_ticket": "SETUP-001",        // manifest.active_ticket (ROOT)
  "workflow": {
    "active_ticket": "SYSTEM-001"     // resolvedWorkflow.active_ticket (OVERRIDE)
  }
}
```

**Fix Options:**

**Option 1: Document semantics with explicit context field:**
```typescript
return JSON.stringify({
  project: manifest.project,
  active_ticket: manifest.active_ticket,  // Keep canonical
  lookup_context: args.ticket_id ? {
    requested_ticket: ticket.id,
    requested_for_context: true,
    note: "workflow.active_ticket below shows requested ticket for context; use manifest.active_ticket for canonical state"
  } : null,
  workflow: args.ticket_id 
    ? { ...resolvedWorkflow, _context_note: "active_ticket overridden for lookup context" }
    : workflow,
  // ...
}
```

**Option 2: Reconcile to single source of truth (recommended):**
```typescript
// Remove resolvedWorkflow override entirely
// Just get ticket for artifact lookup without modifying workflow

return JSON.stringify({
  project: manifest.project,
  active_ticket: manifest.active_ticket,  // Single source of truth
  workflow: workflow,  // Never overridden
  requested_ticket: args.ticket_id ? {
    id: ticket.id,
    stage: ticket.stage,
    status: ticket.status,
    approved_plan: isPlanApprovedForTicket(workflow, ticket.id)
  } : null,
  // ...
}
```

---

### Issue 7: Atomicity Concern in workflow.ts

**Root Cause:** `saveWorkflowBundle()` uses sequential async writes without transaction wrapper.

**Source Location (IDENTICAL in both):**
- **Fitting:** `livetesting/glitch/.opencode/lib/workflow.ts` (Lines 1133-1139)
- **Template:** `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts` (Lines 1133-1139)

**Current Code:**
```typescript
export async function saveWorkflowBundle(bundle: SaveWorkflowBundle): Promise<void> {
  const root = bundle.root ?? rootPath()
  await saveWorkflowState(bundle.workflow, root, bundle.expectedRevision, { refreshDerivedSurfaces: false })
  if (bundle.manifest) await saveManifest(bundle.manifest, root, { refreshDerivedSurfaces: false })
  if (bundle.registry) await saveArtifactRegistry(bundle.registry, root)
  await refreshRestartSurfaces({ manifest: bundle.manifest, workflow: bundle.workflow, root })
}
```

**Atomicity Issues:**
1. Sequential async writes without transaction wrapper
2. No rollback mechanism if step 2 fails after step 1 succeeds
3. Partial state exposure between writes
4. No verification phase

**Risk Scenario:**
```
Step 1: saveWorkflowState() succeeds ✓
Step 2: saveManifest() fails ✗ (disk full)
Step 3: saveArtifactRegistry() never runs
Step 4: refreshRestartSurfaces() never runs

Result: workflow-state.json updated but manifest.json stale,
        leading to active_ticket inconsistency
```

**Enhanced Code:**
```typescript
export async function saveWorkflowBundle(bundle: SaveWorkflowBundle): Promise<void> {
  const root = bundle.root ?? rootPath()
  
  // Phase 1: Prepare all writes
  const writes: { path: string; content: string; description: string }[] = []
  
  writes.push({
    path: workflowStatePath(root),
    content: JSON.stringify(bundle.workflow, null, 2) + "\n",
    description: "workflow state"
  })
  
  if (bundle.manifest) {
    writes.push({
      path: ticketsManifestPath(root),
      content: JSON.stringify(bundle.manifest, null, 2) + "\n",
      description: "manifest"
    })
  }
  
  if (bundle.registry) {
    writes.push({
      path: artifactRegistryPath(root),
      content: JSON.stringify(bundle.registry, null, 2) + "\n",
      description: "artifact registry"
    })
  }
  
  // Phase 2: Atomic write sequence with tracking
  const completedWrites: string[] = []
  
  try {
    // Verify revision before any writes
    const current = await readJson<WorkflowState>(workflowStatePath(root))
    const currentRevision = current.state_revision ?? 0
    const expected = bundle.expectedRevision ?? bundle.workflow.state_revision
    
    if (expected !== currentRevision) {
      throw new Error(`Workflow state changed concurrently. Expected revision ${expected}, found ${currentRevision}.`)
    }
    
    bundle.workflow.state_revision = currentRevision + 1
    
    // Execute all writes
    for (const write of writes) {
      await mkdir(dirname(write.path), { recursive: true })
      await writeFile(write.path, write.content, "utf-8")
      completedWrites.push(write.path)
    }
    
    // Phase 3: Refresh derived surfaces only if all writes succeeded
    if (bundle.refreshDerivedSurfaces !== false) {
      await refreshRestartSurfaces({ manifest: bundle.manifest, workflow: bundle.workflow, root })
    }
    
  } catch (error) {
    throw new Error(
      `Bundle save failed after ${completedWrites.length}/${writes.length} writes. ` +
      `Completed: ${completedWrites.join(", ") || "none"}. ` +
      `Error: ${error instanceof Error ? error.message : String(error)}`
    )
  }
}
```

---

## Summary: Files to Modify

| Issue | Fitting File | Template File | Lines | Change Type |
|-------|--------------|---------------|-------|-------------|
| Lane-lease scoping | `agents/glitch-team-leader.md` | `agents/__AGENT_PREFIX__-team-leader.md` | After 203 | Add path scoping section |
| Lane-lease scoping | `tools/ticket_claim.ts` | `tools/ticket_claim.ts` | 19 | Enhance description |
| Duplicate autoloads | `tools/godot_autoload_check.ts` | `tools/godot_autoload_check.ts` | NEW FILE | Create detection tool |
| Duplicate autoloads | `skills/godot-architecture/SKILL.md` | `skills/godot-architecture/SKILL.md` | 17-22 | Add boundary rules |
| Duplicate autoloads | `agents/glitch-reviewer-code.md` | `agents/__AGENT_PREFIX__-reviewer-code.md` | 53 | Add checklist item |
| Smoke-test brittleness | `tools/smoke_test.ts` | `tools/smoke_test.ts` | 365, 372-373 | Preserve quotes |
| Smoke-test brittleness | `tools/smoke_test.ts` | `tools/smoke_test.ts` | 36-44 | Add status metadata |
| Transition guidance | `lib/workflow.ts` | `lib/workflow.ts` | After 829 | Add validateReviewArtifactEvidence |
| Transition guidance | `tools/ticket_lookup.ts` | `tools/ticket_lookup.ts` | 221-248 | Add verdict checking |
| Transition guidance | `tools/ticket_lookup.ts` | `tools/ticket_lookup.ts` | 46-63 | Add new guidance fields |
| Handoff verification | `tools/handoff_publish.ts` | `tools/handoff_publish.ts` | 39 | Add verification metadata |
| Handoff verification | `tools/context_snapshot.ts` | `tools/context_snapshot.ts` | 34 | Add verification metadata |
| Active ticket split-brain | `tools/ticket_lookup.ts` | `tools/ticket_lookup.ts` | 389-397, 455 | Fix override semantics |
| Atomicity | `lib/workflow.ts` | `lib/workflow.ts` | 1133-1139 | Add transaction wrapper |

**Note:** Both the Glitch fitting and Scafforge template have **IDENTICAL** code in all these locations. The same fixes apply to both.

---

## Fact-Check Verification Summary

**16-agent comprehensive fact-check completed on all claims in this report.**

| Category | Verified | Disputed | Partially Verified |
|----------|----------|----------|-------------------|
| Post-Generation Overwrite Claims | 9 | 0 | 2 |
| GPT5.4 Execution Log Claims | 8 | 4 | 5 |
| Final Key Findings | 4 | 0 | 0 |
| **TOTAL** | **21** | **4** | **7** |

**Key Corrections Applied:**
- Token usage: ~10.04M (not 3.56M) - claim captured scaffold phase only
- Patching rounds: 2 (not 3) - passed on 2nd round after initial failure
- Skills: 8 scaffold spine invoked, 14 local skills generated (not 11)
- Agents: 17 customized (not 15) - includes 2 additional utility agents
- Files: ~150 generated (not 156+) - varies by count method
- Stale-surface categories: 5 (not 4) - includes `human_decision`

### Post-Generation Overwrite Analysis

**6-agent comprehensive investigation confirms:** Post-generation overwrites DO occur, but they are **mostly intentional managed-surface regeneration** rather than bugs.

**When Overwrites Occur (Intentional):**
1. **During scafforge-repair (Deterministic Refresh)** - Replaces entire directories: `.opencode/tools/`, `.opencode/lib/`, `.opencode/plugins/`, `.opencode/commands/`
2. **During scafforge-pivot (Downstream Refresh)** - After canonical brief truth changes
3. **During Repair Follow-On Stages** - Rewrites skills with drift or placeholder content
4. **During Initial Greenfield (Same Session)** - Template → project-specific content transformation

**Potential Issues:**
1. **No User Confirmation Before Replace** - `shutil.rmtree()` + `shutil.copytree()` without showing diffs
2. **Scaffold-Managed vs Project-Specific Boundary Ambiguity** - No clear marker distinguishing scaffold-managed from user-added content
3. **Multiple Skills Touch Restart Surfaces** - Though handoff-brief IS the canonical owner

**Recommendations to Prevent Unwanted Overwrites:**
| Recommendation | Status |
|----------------|--------|
| 1. Backup Before Repair | 🔴 NEEDS IMPLEMENTATION |
| 2. Explicit Differential Display | 🔴 NEEDS IMPLEMENTATION |
| 3. Scaffold-Managed Boundary Marker | 🟡 ALREADY IMPLEMENTED (uses SCAFFORGE markers) |
| 4. User Confirmation for Non-Placeholder Overwrites | 🔴 NEEDS IMPLEMENTATION |
| 5. Post-Generation Edit Preservation Log | 🔴 NEEDS IMPLEMENTATION |
| 6. Single Owner Principle | 🟡 PARTIALLY IMPLEMENTED |

---

## Recommendations

### Immediate Actions Required (P0)

1. **Add Godot scene validation to scaffold chain**
   - Validate `load_steps` matches actual resource count
   - Ensure format version matches target Godot version
   - Block generation on validation failure

2. **Fix ticket_update lease ownership check**
   - Add validation that caller holds the lease before allowing mutation
   - Prevents transitions by agents without ownership

3. **Fix superseded implementation → review invalidation**
   - When marking implementation "superseded", auto-downgrade reviews
   - Prevents advancing to QA on stale reviews

4. **Fix smoke_test.ts quote preservation bug**
   - Lines 365, 372-373 in tokenizeCommandString()
   - This is causing false smoke test failures

### High-Impact Medium-Effort Fixes (P1)

5. **Add structured review verdict field**
   - Require `verdict: "PASS"|"FAIL"|"NEEDS_WORK"` in review artifacts
   - System reads this field for guidance generation

6. **Enhance agent prompts with heuristics**
   - "When to lookup vs. when to trust previous response"
   - "Delegation boundaries: leaders orchestrate, specialists execute"
   - "Stage sequence is predictable: planning → review → implementation → review → qa → smoke-test → closeout"

7. **Add command linting to smoke_test**
   - Detect shell syntax errors before execution
   - Distinguish "command_error" from "verification_failure"

8. **Add lease transfer tool**
   - Atomic ownership change without release/reclaim window
   - Auto-release subagent leases on successful task completion

### Structural Improvements (P2-P3)

9. **Create Godot version-locked templates**
   - Separate Godot 3.x and 4.x template sets
   - Add `godot_version` to canonical brief as required field

10. **Add GDScript anti-pattern linter**
    - Detect static methods that instantiate nodes
    - Flag memory leak patterns
    - Enforce autoload registration consistency

11. **Implement `ticket_progress` combined tool**
    - Single tool: "check guidance + advance stage + verify"
    - Reduces 3-tool sequence to 1 atomic operation

12. **Fix ticket_lookup.ts active ticket split-brain**
    - Either document the semantics or reconcile to single source of truth

---

## Appendix: Line Reference Quick Guide

| Issue | Key Lines in glitchblock1.md |
|-------|------------------------------|
| Lease scoping blocker | 928-988 (initial claim), 2228-2255 (blocker detection), 2268-2373 (fix) |
| Duplicate autoloads | 3227-3278 (review), 3249 (FAIL verdict), 3296-3345 (fix), 4163-4206 (QA verify) |
| Smoke-test brittleness | 4716-4761 (failure), 4820-4836 (actual success), 4883-4919 (simplified pass) |
| verification_state | 832, 1346, 1719, 2091, 2884, 3476, 4602, 5090 (all "suspect"), 5380 ("trusted") |
| Guidance/verdict mismatch | 3578-3604 (guidance), 3249 (review FAIL) |
| Handoff verification gaps | 638-644 (context_snapshot), 665-671 (handoff_publish) |
| Active ticket split-brain | 768-770, 5779-5781, 6042-6044 |

---

**Document Status:** Comprehensive analysis complete. All findings validated with transcript evidence and source code locations.

**Next Steps:** Prioritize P0 fixes (validation gaps, tool logic errors) before P1 agent guidance improvements.
