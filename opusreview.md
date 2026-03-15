# Scafforge — Comprehensive Review

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-15
**Scope:** Full review of the entire initial commit (b4a0cc2) — 117 files, ~8,500 lines
**Review type:** Design review + implementation review + correctness audit

---

## Executive Summary

Scafforge is an ambitious, well-conceived scaffold generator for autonomous AI coding agents. The conceptual design — a host-agnostic generator that produces an OpenCode-oriented project operating layer — is sound and fills a genuine gap. The overall architecture is thoughtful: a clean two-layer separation (generator vs. generated), a machine-readable flow manifest, a structured truth hierarchy, tool-backed state management, and a comprehensive audit system.

However, the initial commit contains several bugs, missing infrastructure pieces, and legacy artifacts that undermine the polish and reliability of what is otherwise a strong foundation. The most significant issues are: committed `.pyc` bytecode files, a missing `.gitignore`, legacy `CODEXSETUP` branding in the runtime code, invisible Unicode citation artifacts in user-facing docs, and a smoke test that doesn't verify its most critical contract (placeholder replacement).

This review is structured as: Bugs & Errors → Structural/Design Issues → Documentation Issues → Code Quality → Validation & Testing → Generated Output Quality → Per-Skill Analysis.

---

## 1. Bugs & Errors

### BUG-01: `.pyc` bytecode files committed to git

**Severity: High**
**Files:**
- `skills/opencode-team-bootstrap/scripts/__pycache__/bootstrap_opencode_team.cpython-314.pyc`
- `skills/repo-process-doctor/scripts/__pycache__/audit_repo_process.cpython-314.pyc`
- `skills/repo-scaffold-factory/scripts/__pycache__/bootstrap_repo_scaffold.cpython-314.pyc`

Three compiled Python bytecode files are tracked in the initial commit. These are platform-specific binary artifacts that:
- Expose the Python version used during development (CPython 3.14)
- Bloat the repository with unreproducible binary content
- Will cause merge conflicts if different developers use different Python versions
- Signal a missing `.gitignore` (see BUG-02)

**Fix:** Remove from tracking with `git rm --cached`, add `__pycache__/` and `*.pyc` to `.gitignore`.

---

### BUG-02: No `.gitignore` file exists

**Severity: High**

The repository has no `.gitignore` at all. For a project that involves Python scripts, Node.js packaging, and TypeScript tooling, this is a critical omission. Without it:
- Python bytecache (`__pycache__/`, `*.pyc`) gets committed (as already happened)
- `node_modules/` would be committed if `npm install` were ever run
- Temporary test artifacts from the smoke test could be committed
- Editor-specific files (`.vscode/`, `.idea/`) could leak in
- OS-specific files (`.DS_Store`, `Thumbs.db`) could accumulate

**Fix:** Add a comprehensive `.gitignore` covering at minimum: `__pycache__/`, `*.pyc`, `node_modules/`, `.env`, `.DS_Store`, `Thumbs.db`, and any build/temp directories.

---

### BUG-03: `CODEXSETUP` legacy branding markers in runtime code and template

**Severity: High**
**Files:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts` (lines 74-75)
- `skills/repo-scaffold-factory/assets/project-template/START-HERE.md` (lines 3, 32)

The managed-block markers used by `renderStartHere()` and `mergeStartHere()` are:
```typescript
export const START_HERE_MANAGED_START = "<!-- CODEXSETUP:START_HERE_BLOCK START -->"
export const START_HERE_MANAGED_END = "<!-- CODEXSETUP:START_HERE_BLOCK END -->"
```

Every generated repository permanently carries the `CODEXSETUP` brand in its `START-HERE.md`. This is:
- Directly contradicted by `TASKS.md` item T-017 which says "Purge `CODEXSETUP` and similar legacy placeholders or markers"
- Not caught by `validate_scafforge_contract.py`, which checks for several legacy strings but **does not include `CODEXSETUP`** in its disallowed list
- Confusing to end users who will see a meaningless `CODEXSETUP` comment in their project files

The `devdocs/scafforge-critical-issues.md` document (which is part of this same commit!) correctly identifies this as BUG-01 but the fix was not applied before committing.

**Fix:** Rename to `<!-- SCAFFORGE:MANAGED_START -->` and `<!-- SCAFFORGE:MANAGED_END -->`. Add `CODEXSETUP` to the validator's disallowed list.

---

### BUG-04: Invisible Unicode citation artifacts in README.md and REVIEW-NOTES.md

**Severity: High**
**Files:**
- `README.md` (2 locations: lines 105, 247)
- `REVIEW-NOTES.md` (2 locations: lines 68, 84)

Both files contain AI-generated citation markers from OpenAI's system. These use **private-use Unicode characters** (U+E200, U+E201, U+E202) that are invisible to most text editors, renderers, and search tools. Byte-level inspection reveals:

```
plugins. [U+E200]cite[U+E202]turn375117search2[U+E202]turn375117search0...
```

The invisible characters have several consequences:
1. **Invisible to users** — they don't appear in rendered Markdown but exist in the raw bytes
2. **Break text search tools** — `grep`, `Select-String`, `IndexOf` all fail to find "citeturn" because the invisible characters break up the pattern
3. **May cause encoding issues** — some tools and CI systems may handle these private-use characters unpredictably
4. **Indicate unreviewed AI-generated content** — citation markers should be cleaned before publication

The affected lines in README.md are:
- Line 105: `"...makes it a good target for a generated project operating layer. [invisible citations]"`
- Line 247: `"...including OpenCode and Codex. [invisible citations]"`

And in REVIEW-NOTES.md:
- Line 68: `"...supports repo-local rules, skills, commands, tools, and plugins. [invisible citations]"`
- Line 84: `"...works across many agent hosts. [invisible citations]"`

**Fix:** Strip all bytes matching `\xEE\x88[\x80-\x82]` from both files. Optionally add the OpenAI citation string patterns to the validator's disallowed list.

---

### BUG-05: `context_snapshot.ts` modifies workflow state in memory without persisting

**Severity: Medium**
**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/context_snapshot.ts`

When an optional `ticket_id` argument is provided, the tool loads the workflow state, overwrites three fields to match the requested ticket, then uses the mutated object to render the snapshot — but **never calls `saveWorkflowState()`**:

```typescript
if (args.ticket_id) {
  workflow.active_ticket = ticket.id
  workflow.stage = ticket.stage
  workflow.status = ticket.status
}
const content = renderContextSnapshot(manifest, workflow, args.note)
// saveWorkflowState is never called
```

The resulting snapshot file describes a ticket state that doesn't match `workflow-state.json`. Any agent reading both surfaces in the same session sees contradictory state.

**Fix:** Either remove the in-memory mutation entirely (always snapshot the true active ticket), or call `saveWorkflowState(workflow)` after the mutation. Document which behavior is intended.

---

### BUG-06: Smoke test doesn't verify placeholder replacement

**Severity: Medium**
**File:** `scripts/smoke_test_scafforge.py`

`verify_render()` checks that required files exist and that `tickets/manifest.json` has a `tickets` key. It does **not** check whether placeholder strings like `__PROJECT_NAME__`, `__PLANNER_MODEL__`, `__AGENT_PREFIX__`, etc. were actually replaced in any generated file.

If a new placeholder is introduced in the template without a matching entry in the `replacements` dictionary in `bootstrap_repo_scaffold.py`, the smoke test passes while generated files still contain raw placeholder strings.

**Fix:** Add a scan for any string matching `__[A-Z][A-Z_]+__` across all generated text files and fail if any remain.

---

### BUG-07: `template_commit()` has no subprocess timeout

**Severity: Low-Medium**
**File:** `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py` (lines 109-120)

```python
result = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    cwd=managed_repo_root(),
    check=False,
    capture_output=True,
    ...
)
```

There is no `timeout=` argument. In CI environments where git is slow, misconfigured, or unavailable, this call can hang indefinitely. The fallback returns `"unknown"` only on non-zero return code, not on timeout.

**Fix:** Add `timeout=10` and wrap in `try/except subprocess.TimeoutExpired` returning `"unknown"`.

---

### BUG-08: `package.json` marked private contradicts adapter install examples

**Severity: Low-Medium**
**Files:** `package.json` (line 4), `adapters/manifest.json` (lines 5-10)

`package.json` has `"private": true`. The adapter manifest declares the primary distribution package as `@scafforge/core` and provides install commands:
```json
"npm": "npm install --global @scafforge/core",
"pnpm": "pnpm add --global @scafforge/core",
"bun": "bun add --global @scafforge/core"
```

These commands will fail. Either `private` should be removed (when ready to publish), or the install examples should be documented as future-state.

---

### BUG-09: `bin/scafforge.mjs` uses non-chained `if` statements

**Severity: Low**
**File:** `bin/scafforge.mjs` (lines 35-48)

The command dispatch uses three independent `if` blocks:
```javascript
if (command === "render-full") {
  runPython(...)  // calls process.exit()
}
if (command === "render-opencode") {
  runPython(...)  // calls process.exit()
}
if (command === "validate-contract") {
  runPython(...)  // calls process.exit()
}
console.error(`Unknown command: ${command}`)
process.exit(1)
```

This works because `runPython()` calls `process.exit()`, so valid commands never reach the error. But this is fragile — if `runPython` is ever refactored to not exit (e.g. to return a status code), every valid command would also print "Unknown command" and exit 1.

**Fix:** Use `else if` chains, a switch statement, or a command map with early return.

---

### BUG-10: `docs/process/agent-catalog.md` missing from conformance checklist

**Severity: Low**
**Files:**
- `skills/repo-scaffold-factory/assets/project-template/AGENTS.md` (required read order step 5)
- `skills/repo-scaffold-factory/references/opencode-conformance-checklist.json`

The generated `AGENTS.md` lists `docs/process/agent-catalog.md` as step 5 in the required read order. The conformance checklist's `required_files` array does not include this file. The smoke test and validator therefore cannot detect if this file goes missing from the template.

**Fix:** Add `"docs/process/agent-catalog.md"` and `"docs/process/tooling.md"` to `required_files` in the conformance checklist.

---

## 2. Structural & Design Issues

### DESIGN-01: No `.gitignore` means the package is not distribution-ready

Beyond the `.pyc` issue, the absence of `.gitignore` means the repo cannot safely have `npm install` run (no `node_modules/` exclusion), and the smoke test's temporary directories are only cleaned up programmatically — a failed test could leave artifacts in the working directory.

---

### DESIGN-02: `devdocs/` ships with the package but is historical reference, not operating context

The `devdocs/` directory contains:
- `research report.md` — has a **space in the filename** (should be `research-report.md`)
- `scafforge-implementation-plan.md` — 1,656 lines of planning prose
- `worklog.md` — 570 lines of implementation narrative
- `scafforge-architecture-analysis.md` — architecture deep-dive
- `scafforge-critical-issues.md` — identifies bugs **that are still present in this commit**
- `scafforge-improvements.md` — improvement suggestions

Issues:
1. **Windows absolute paths** in `research report.md` and the implementation plan (e.g. `C:\Users\rowan\.copilot\session-state\...`) contradict the Linux-safe output requirement
2. **`scafforge-critical-issues.md` identifies bugs that weren't fixed** before committing — BUG-01 (CODEXSETUP), BUG-03 (context_snapshot), BUG-04 (placeholder check), and all RISKs are documented but not resolved
3. No document in the repo marks `devdocs/` as historical/internal — agents with read access may treat it as operating guidance
4. The space in `research report.md` violates naming conventions and can cause shell-quoting issues

---

### DESIGN-03: Adapter manifest's `opencode` entry is semantically different from others

**File:** `adapters/manifest.json`

The `opencode` adapter entry says:
```json
"opencode": [
  "invoke generated repo after scaffold completion",
  "read START-HERE.md",
  "run the autonomous lifecycle inside the generated repo"
]
```

This describes **post-scaffold usage**, not **how to install/invoke Scafforge from OpenCode**. The other adapters (github-copilot, codex, gemini-cli) correctly describe installation and invocation. This semantic inconsistency will confuse readers.

---

### DESIGN-04: No CLI `audit-repo` command

**File:** `bin/scafforge.mjs`

The process doctor audit script is the most operationally useful standalone tool in the package, yet the CLI wrapper only exposes `render-full`, `render-opencode`, and `validate-contract`. Users must know the Python script path (`skills/repo-process-doctor/scripts/audit_repo_process.py`) to run an audit.

---

### DESIGN-05: No scaffold inventory manifest generated

**File:** `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`

`bootstrap-provenance.json` records *how* the scaffold was generated (which commit, which arguments) but not *what* was generated. There is no machine-readable inventory of the agents, tools, plugins, commands, and skills that were created. This was explicitly called for in the implementation plan's interview question 3.

---

### DESIGN-06: Stage gate enforcer allows pre-approval writes to implementation paths

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`

The `isDocPath()` function allows write/edit operations on any path starting with `.opencode/`:
```typescript
function isDocPath(pathValue: string): boolean {
  return (
    pathValue.startsWith("docs/") ||
    pathValue.startsWith("tickets/") ||
    pathValue.startsWith(".opencode/") ||  // Too broad!
    ...
  )
}
```

This means an agent could write to `.opencode/state/implementations/` before `approved_plan` is true, bypassing the stage gate through the raw `write`/`edit` tools rather than through `artifact_write`.

**Fix:** Narrow to only allow `docs/`, `tickets/`, `.opencode/state/plans/`, `.opencode/skills/`, and similar planning-safe paths before approval. Block `.opencode/state/implementations/`, `.opencode/state/reviews/`, `.opencode/state/qa/`, and `.opencode/state/handoffs/` until `approved_plan` is true.

---

### DESIGN-07: `handoff_publish.ts` silently no-ops when markers are removed

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`

`mergeStartHere()` preserves the existing file unchanged if it lacks the managed markers. The tool returns `{ start_here, latest_handoff }` with no indication that the merge was a no-op. The calling agent cannot detect that the handoff was silently discarded.

**Fix:** Return a `merged: boolean` field and have the team leader log a warning if `merged` is false.

---

### DESIGN-08: `opencode.jsonc` global bash permissions include `sed *`

**File:** `skills/repo-scaffold-factory/assets/project-template/opencode.jsonc` (line 46)

The generated `opencode.jsonc` allows `"sed *": "allow"` in the global bash permissions. The project's own doctor script flags `sed` as a mutating shell token. This creates an inconsistency: the project's audit tool would flag a pattern that the project's own template generates.

**Fix:** Remove `"sed *": "allow"` from the global config and add it only to the implementer agent's bash allowlist.

---

### DESIGN-09: `opencode-team-bootstrap` delegates via `subprocess.run`

**File:** `skills/opencode-team-bootstrap/scripts/bootstrap_opencode_team.py`

The bootstrap script for OpenCode-only scope simply constructs a command-line invocation of `bootstrap_repo_scaffold.py` and runs it via `subprocess.run`. This adds an unnecessary process layer and requires the Scafforge repo's Python scripts to be accessible at runtime. A direct function import would be more robust.

---

### DESIGN-10: `TASKS.md` items T-019 and T-020 listed as incomplete but worklog says done

**Files:** `TASKS.md`, `devdocs/worklog.md`

`TASKS.md` has a status note saying the foundational baseline is implemented, but the body still lists T-019 (improve `START-HERE.md`) and T-020 (improve `AGENTS.md`) without completion markers. The worklog describes improvements to both. An agent reading only `TASKS.md` would believe these are still open.

---

## 3. Documentation Issues

### DOC-01: No `CONTRIBUTING.md` or development setup guide

The repository has `package.json` with npm scripts, Python scripts, TypeScript tools, and a `bin/` entry point. There is no document explaining:
- Prerequisites (Node version, Python version)
- How to run `npm run validate:contract` and `npm run validate:smoke`
- How to add a new skill to the flow manifest
- The definition of done for package changes

---

### DOC-02: Missing inline comments in TypeScript tools

Most `.ts` tool files have minimal or no inline comments explaining key logic:
- `ticket_update.ts` enforces several critical invariants (plan approval before in_progress, implementation artifact before review, etc.) but doesn't comment why each check exists
- `_workflow.ts` is the most important shared module and has no module-level documentation header
- `stage-gate-enforcer.ts` has no comments explaining its security model

---

### DOC-03: `skill_ping.ts` accesses undocumented context properties

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/skill_ping.ts` (lines 11-14)

```typescript
async execute(args, context) {
  const event = {
    session_id: context.sessionID,
    message_id: context.messageID,
    agent: context.agent,
    // ...
  }
  const path = invocationLogPath(context.directory)
```

The `context` parameter's available properties (`sessionID`, `messageID`, `agent`, `directory`) are not documented anywhere in the Scafforge package. If OpenCode's tool context API changes, this breaks silently.

---

### DOC-04: No explicit documentation marking `devdocs/` as historical reference

Agents reading the full repo could treat `devdocs/` as active operating guidance. The `devdocs/scafforge-implementation-plan.md` is 1,656 lines of planning that could overwhelm agent context windows and create confusing cross-references.

---

### DOC-05: Missing `No engines` field documentation in package.json

**File:** `package.json`

The `bin/scafforge.mjs` CLI uses `import.meta.url` and ESM modules. Without an `engines` field (`"engines": { "node": ">=18.0.0" }`), users on old Node versions get cryptic ESM syntax errors rather than a clear version requirement message.

---

### DOC-06: README's "Current gaps to close" section is partially stale

**File:** `README.md` (lines 299-305)

The "Current gaps to close" section lists:
- "some skill descriptions still use Codex-specific wording"
- "the package needs a skill-flow manifest or machine-checkable dependency map"

The worklog says the skill-flow manifest was added and Codex wording was cleaned. These items should be updated to reflect current status.

---

## 4. Code Quality

### CODE-01: `audit_repo_process.py` has duplicate path-normalization functions

**File:** `skills/repo-process-doctor/scripts/audit_repo_process.py`

The file defines both `normalize_path()` (line 70) and `normalized_path()` (line 150) — two functions with nearly identical names that do the same thing:
```python
def normalize_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")

def normalized_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")
```

The only difference is that `normalize_path` has a `try/except` fallback. Some functions use one, some use the other. This is confusing and error-prone.

**Fix:** Remove the duplicate and standardize on one function.

---

### CODE-02: `audit_invalid_tool_schemas` regex can produce false positives

**File:** `skills/repo-process-doctor/scripts/audit_repo_process.py` (lines 491-533)

```python
def tool_uses_plain_object_args(text: str) -> bool:
    return bool(re.search(r"\btype:\s*\"[A-Za-z]+\"", text) or
                re.search(r"\brequired:\s*(true|false)\b", text))
```

The pattern `type:\s*"[A-Za-z]+"` matches any TypeScript object literal with a `type` string field, including legitimate usage in plugin event handlers, MCP config objects, or JSON serialization code. Although the function is only called on files containing `export default tool(`, the regex within the file is too broad.

---

### CODE-03: `bootstrap_repo_scaffold.py` allows partial overwrites without warning

**File:** `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`

In non-force mode, `write_file()` raises `FileExistsError` for individual files, but `copy_template()` doesn't pre-flight check whether the destination directory is non-empty. A user could get a partial scaffold where some files were written and others were rejected, with no clear indication of what happened.

---

### CODE-04: `_workflow.ts` `renderContextSnapshot` produces a very long single-line string

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts` (line 262)

The `renderContextSnapshot()` function returns a template literal that is 263+ characters of concatenated Markdown on a single line. This is unmaintainable and hard to debug:

```typescript
return `# Context Snapshot\n\n## Project\n\n${manifest.project}\n\n## Active Ticket\n\n- ID: ${ticket.id}\n- Title: ${ticket.title}\n- Stage: ${ticket.stage}\n- Status: ${ticket.status}\n- Approved plan: ${workflow.approved_plan ? "yes" : "no"}\n\n## Ticket Summary\n\n${ticket.summary}\n\n## Recent Artifacts\n\n${artifactLines}${noteBlock}\n## Next Useful Step\n\nUse the team leader or the next required specialist for the current stage.\n`
```

The same applies to `renderStartHere()` (line 266-267) and `renderBoard()` (line 247).

**Fix:** Use multi-line template literals or build arrays of lines with `.join("\n")`.

---

### CODE-05: No type validation on manifest JSON structure

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts`

`readJson<T>()` performs a cast (`as T`) with no runtime validation:
```typescript
export async function readJson<T>(path: string, fallback?: T): Promise<T> {
  const raw = await readFile(path, "utf-8")
  return JSON.parse(raw) as T
}
```

If `manifest.json` is malformed or has a different shape than `Manifest`, the error surfaces far from the read site. For a system designed for weaker models that might accidentally corrupt state files, this is risky.

---

## 5. Validation & Testing

### TEST-01: Smoke test doesn't run the doctor against generated output

**File:** `scripts/smoke_test_scafforge.py`

After generating a scaffold, the smoke test does not run `audit_repo_process.py` against the result. This means a change to the template that introduces a workflow smell (e.g. contradictory status semantics) is not caught automatically. A generated scaffold should have zero doctor findings by default.

---

### TEST-02: Validator doesn't check for `CODEXSETUP`

**File:** `scripts/validate_scafforge_contract.py` (lines 111-129)

The `validate_no_hidden_defaults()` function checks for several disallowed strings:
```python
disallowed = [
    "minimax-coding-plan/MiniMax-M2.5",
    "--default-model",
    "__DEFAULT_MODEL__",
    "GitHub-native",
    "Use when Codex",
    "Codex or OpenCode",
]
```

`CODEXSETUP` is conspicuously absent. The `devdocs/scafforge-critical-issues.md` file (part of this commit) explicitly notes this oversight.

---

### TEST-03: Validator doesn't check for unreplaced placeholders outside the template

**File:** `scripts/validate_scafforge_contract.py`

The validator never scans non-template source files for `__[A-Z_]+__` patterns. If a placeholder were accidentally left in a non-template file (e.g. a skill SKILL.md or a reference document), it would go undetected.

---

### TEST-04: No test for the retrofit flow

**File:** `scripts/smoke_test_scafforge.py`

The smoke test only tests `--scope full` and `--scope opencode`. There is no fixture that verifies the retrofit flow — i.e., adding the OpenCode layer to a repo that already has existing docs and tickets without overwriting them.

---

## 6. Generated Output Quality

### OUTPUT-01: Generated `opencode.jsonc` allows overly broad bash permissions

The global `bash` permissions in the generated config include `"sed *": "allow"`, which is a mutation-capable command that contradicts the project's own audit philosophy. The `git log*` allowlist may also be more permissive than intended (allows `git log --all --decorate`, etc.).

---

### OUTPUT-02: Generated `START-HERE.md` contains legacy `CODEXSETUP` markers

Every generated repository will carry `<!-- CODEXSETUP:START_HERE_BLOCK START -->` and `<!-- CODEXSETUP:START_HERE_BLOCK END -->` markers. These are meaningless to end users and leak internal package-era branding.

---

### OUTPUT-03: Generated agents have consistent and well-designed permission models

**Positive finding.** The agent permission models are thoughtfully designed:
- Team leader has no write/edit/bash but has ticket tools and delegation capability
- Planner has artifact_write/register but no bash
- Implementer has write/edit/bash with a well-curated allowlist
- Reviewers have read-only shell access with no mutation commands
- Utility agents are properly bounded

This is a strong design that prevents the common failure mode of agents with too-broad permissions.

---

### OUTPUT-04: Generated `workflow-state.json` initial state has minor inconsistency

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/state/workflow-state.json`

```json
{
  "active_ticket": "SETUP-001",
  "stage": "planning",
  "status": "ready",
  "approved_plan": false
}
```

The initial ticket `SETUP-001` in `manifest.json` has `"stage": "scaffold"` and `"status": "todo"`, but `workflow-state.json` says `"stage": "planning"` and `"status": "ready"`. These don't match.

**Fix:** Either align the initial workflow state with the manifest ticket, or document that workflow state is intentionally set to the *intended next* state rather than mirroring the current ticket state.

---

### OUTPUT-05: Generated ticket template has stage-specific fields but the default ticket doesn't use them

**File:** `skills/repo-scaffold-factory/assets/project-template/tickets/templates/TICKET.template.md`

The template includes sections like `## Implementation Brief` and `## Acceptance Criteria` that are appropriate for implementation tickets but not for setup/scaffold tickets. The default SETUP-001 ticket has no corresponding markdown file — it exists only in the manifest. This is fine architecturally, but it means the ticket template is never demonstrated in use.

---

## 7. Per-Skill Analysis

### `scaffold-kickoff`

**Quality: Good.** The SKILL.md is well-structured, clearly describes the full-cycle flow, distinguishes between greenfield and retrofit paths, and explicitly states what the skill does not own. The "intentionally thin" framing is correct.

**Issue:** No classification decision tree for determining run type (greenfield vs. retrofit vs. refinement). An agent using this skill for the first time must infer the classification logic.

---

### `spec-pack-normalizer`

**Quality: Good.** Clear workflow, well-defined output shape, good rules about separating facts from assumptions. The `references/brief-schema.md` is a useful structured schema.

**Issue:** No worked example (`references/brief-examples.md`) showing a before/after transformation. This would significantly help agents using the skill.

---

### `repo-scaffold-factory`

**Quality: Very Good.** This is the most complete skill. The Python script is well-structured, the template system is sound, the placeholder replacement is clean, and the provenance writer is a good design decision.

**Issues:**
- The quick-start code block shows PowerShell syntax (backtick continuation) which is Windows-specific despite the project claiming Linux-safe defaults
- The `references/opencode-conformance-checklist.json` is missing `docs/process/agent-catalog.md` and `docs/process/tooling.md` from `required_files`
- The `agents/openai.yaml` file for all skills is minimal (4 lines each) and identical across skills — it's unclear if this adds value

---

### `opencode-team-bootstrap`

**Quality: Adequate.** Correctly positions itself as a thin wrapper. The script correctly delegates to `bootstrap_repo_scaffold.py` with `--scope opencode`.

**Issue:** The subprocess delegation adds an unnecessary process layer. A Python import would be more robust and eliminate the need for the Scafforge repo to be accessible at runtime.

---

### `ticket-pack-builder`

**Quality: Good.** Clear dual-mode contract (bootstrap/refine). Good rules about not fabricating detail for unresolved decisions.

**Issue:** The `references/ticket-system.md` is useful but could be more specific about the machine-readable format of `manifest.json` — i.e., what fields are required on each ticket entry.

---

### `project-skill-bootstrap`

**Quality: Good.** Clear dual-mode contract (foundation/synthesis). Good guardrails about not blindly copying skills.

**Issue:** The default local skill pack lists 9 skills. The implementation plan's interview section calls for a complexity budget. Whether 9 is the right number is not discussed.

---

### `agent-prompt-engineering`

**Quality: Good.** The references directory is the strongest part — `anti-patterns.md`, `prompt-contracts.md`, `examples.md`, and `weak-model-profile.md` form a coherent prompt-hardening toolkit.

**Issue:** No issue found. This skill is solid.

---

### `repo-process-doctor`

**Quality: Excellent.** This is the most impressive component. The audit script (`audit_repo_process.py`, 858 lines) is thorough, well-structured, and covers 20 distinct audit checks. The finding dataclass with `code`, `severity`, `problem`, `root_cause`, `files`, `safer_pattern`, and `evidence` fields is a good design. The markdown and JSON output modes are well-implemented.

**Issues:**
- Duplicate path-normalization functions (`normalize_path` vs `normalized_path`)
- `audit_invalid_tool_schemas` regex is slightly too broad (see CODE-02)
- The SKILL.md says "default to `apply-repair` unless explicitly blocked" but the script only supports `audit` mode — there is no actual repair implementation

---

### `review-audit-bridge`

**Quality: Minimal.** This is the thinnest skill — 18 lines in SKILL.md, 11 lines in the review-sequence reference. It's explicitly positioned as a later-lifecycle skill, but it lacks enough substance to be useful without significant agent interpretation.

---

### `handoff-brief`

**Quality: Adequate.** Clear required outputs, references the template and checklist.

**Issue:** The `assets/templates/START-HERE.template.md` is 21 lines and is essentially a simpler version of the generated START-HERE. It's unclear when an agent would use this template vs. the `renderStartHere()` function in `_workflow.ts`.

---

## 8. Flow Manifest & Contract Coherence

### The `skill-flow-manifest.json` is well-designed

The manifest correctly describes both greenfield and retrofit flows, includes input/output declarations for each skill, and properly chains upstreams/downstreams. The validator checks that the greenfield sequence contains required steps.

### The AGENTS.md spine includes `opencode-team-bootstrap` between `repo-scaffold-factory` and `ticket-pack-builder`

This is correct for the overall skill catalog but could be confusing since `opencode-team-bootstrap` is only used in the retrofit flow. The greenfield flow goes directly from `repo-scaffold-factory` to `ticket-pack-builder`. The spine listing doesn't make this distinction clear.

---

## 9. Cross-Cutting Concerns

### Windows vs. Linux path handling

The bootstrap script correctly uses `pathlib.Path` which handles cross-platform paths. The `_workflow.ts` runtime uses `path.join()` from Node.js which also handles this. The `normalizeRepoPath()` function correctly converts backslashes. The generated `AGENTS.md` includes the note "Use Ubuntu-safe commands and paths" which is appropriate.

However, the `repo-scaffold-factory/SKILL.md` quick-start shows PowerShell backtick continuation syntax, which is Windows-only.

### OpenCode API assumptions

The generated tools and plugins import from `@opencode-ai/plugin` and assume specific API surfaces:
- `tool()` function with `description`, `args`, and `execute`
- `tool.schema.string()`, `tool.schema.boolean()`, `tool.schema.enum()` — Zod-style schemas
- Plugin hooks: `chat.message`, `tool.execute.before`, `tool.execute.after`, `command.execute.before`, `experimental.session.compacting`
- Plugin input/output shapes with `sessionID`, `agent`, `messageID`, etc.
- Tool context with `sessionID`, `messageID`, `agent`, `directory`

None of these API surfaces are documented within the Scafforge package. If OpenCode changes its plugin API, the generated repos break silently.

### Agent YAML files

Every skill has an `agents/openai.yaml` file with 4 lines:
```yaml
interface:
  display_name: "..."
  short_description: "..."
  default_prompt: "..."
```

These appear to be OpenAI Agents SDK metadata for each skill. They're minimal and consistent. The `default_prompt` values are reasonable.

---

## 10. Summary of Findings by Severity

| Severity | Count | Key Items |
|----------|-------|-----------|
| **High** | 4 | Committed .pyc files, no .gitignore, CODEXSETUP markers, invisible citation artifacts |
| **Medium** | 6 | context_snapshot mutation, placeholder verification, stage gate bypass, no audit CLI, manifest inconsistency, smoke test gaps |
| **Low** | 10 | Template string formatting, subprocess timeout, package.json private flag, stale TASKS.md, missing CONTRIBUTING.md, etc. |

---

## 11. Overall Assessment

### Strengths
1. **Strong conceptual architecture** — the two-layer model is clean and well-reasoned
2. **Excellent audit system** — the process doctor is genuinely impressive and operationally useful
3. **Good agent permission design** — the generated team has well-thought-out capability boundaries
4. **Sound truth hierarchy** — the canonical ownership model is a strong design that solves real problems
5. **Comprehensive flow manifest** — machine-readable skill chain with proper upstream/downstream declarations
6. **Good prompt engineering reference library** — the anti-patterns and contracts references are valuable

### Weaknesses
1. **Known bugs shipped knowingly** — `devdocs/scafforge-critical-issues.md` documents bugs that weren't fixed before commit
2. **Missing basic infrastructure** — no `.gitignore`, no `engines` field, no `CONTRIBUTING.md`
3. **Legacy branding contamination** — `CODEXSETUP` markers in runtime code
4. **Invisible encoding issues** — private-use Unicode characters in user-facing docs
5. **Incomplete validation harness** — the existing validators miss several important checks
6. **TypeScript code clarity** — long single-line template literals, minimal comments, no JSDoc

### Verdict

The project is conceptually strong but operationally unfinished. The initial commit reads like a solid v0.1 alpha that should have had one more cleanup pass before being published. The most critical fix is adding a `.gitignore` and removing the committed `.pyc` files; the most impactful improvement would be fixing the `CODEXSETUP` markers and the invisible citation artifacts before any user ever sees the generated output.
