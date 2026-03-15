# Scafforge — Critical Issues Report

A thorough line-by-line review of every skill, tool, plugin, script, and template in the repository. Issues are grouped by severity and then by subsystem.

---

## Severity Levels Used

- **BUG** — demonstrably wrong behaviour that will cause failures at runtime or validation time
- **RISK** — correct today but fragile; will silently break under specific conditions
- **CONTRADICTION** — two parts of the codebase say different things about the same thing
- **GAP** — something the project claims to do or guarantee that is not yet actually enforced

---

## 1. Bugs

### BUG-01 — Legacy branding marker is still in the TypeScript runtime and template

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts`
**File:** `skills/repo-scaffold-factory/assets/project-template/START-HERE.md`

The constant `START_HERE_MANAGED_START` is still `"<!-- CODEXSETUP:START_HERE_BLOCK START -->"` and `START_HERE_MANAGED_END` is `"<!-- CODEXSETUP:START_HERE_BLOCK END -->"`. These markers are written into every generated `START-HERE.md` through `renderStartHere()` and `mergeStartHere()`. The template `START-HERE.md` already contains those strings. Every generated repo will permanently carry the `CODEXSETUP` brand in its restart surface.

`TASKS.md` item T-017 explicitly calls this out as something to remove. The `validate_scafforge_contract.py` script checks for several legacy strings but **does not check for `CODEXSETUP`**, so the automated validator will not catch it.

**Impact:** Every generated repo leaks internal Scafforge package-era naming into a user-facing file. If users search for documentation on `CODEXSETUP`, they find nothing relevant.

**Fix:** Rename the markers to `<!-- SCAFFORGE:START_HERE_BLOCK START -->` and update all references in `_workflow.ts`, the template, and the validator's disallowed list.

---

### BUG-02 — `package.json` is marked private but the adapter manifest declares it as a publishable package

**File:** `package.json`
**File:** `adapters/manifest.json`

`package.json` has `"private": true`. The adapter manifest names the primary distribution package as `@scafforge/core` and gives npm/pnpm/bun install examples. The CLI wrapper `bin/scafforge.mjs` exists and is referenced via `"bin"` in `package.json`. The package cannot be published as-is.

**Impact:** The install examples in `adapters/manifest.json` and `adapters/README.md` do not work. Any adapter documentation pointing users to `npm install --global @scafforge/core` will fail.

**Fix:** Remove `"private": true` from `package.json` once the project is ready to publish, or add a comment making clear this is a development-only guard that must be removed before the first release.

---

### BUG-03 — `context_snapshot.ts` modifies workflow state in memory without persisting it

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/context_snapshot.ts`

When an optional `ticket_id` argument is provided, the tool loads the workflow state, overwrites three fields (`active_ticket`, `stage`, `status`) to match the requested ticket, then uses that mutated object to render the snapshot. It **never calls `saveWorkflowState(workflow)`**. The mutation is in-memory only.

```typescript
if (args.ticket_id) {
  workflow.active_ticket = ticket.id
  workflow.stage = ticket.stage
  workflow.status = ticket.status
}
const content = renderContextSnapshot(manifest, workflow, args.note)
// saveWorkflowState is never called
```

The snapshot file on disk will describe a ticket that does not match `.opencode/state/workflow-state.json`. Any agent that reads both surfaces in the same session will see contradictory state.

**Impact:** Context snapshot becomes an unreliable surface whenever a non-active ticket is requested. The `docs-and-handoff` skill instructs agents to keep the snapshot fresh — a snapshot for the wrong ticket silently satisfies that instruction.

**Fix:** Either (a) remove the in-memory mutation entirely and always snapshot the true active ticket, or (b) call `saveWorkflowState(workflow)` after the mutation so both files agree. Document which behaviour is intended.

---

### BUG-04 — Smoke test does not verify that template placeholders were actually replaced

**File:** `scripts/smoke_test_scafforge.py`

`verify_render()` checks that required files and directories exist and that `tickets/manifest.json` has a `tickets` key. It does not check that placeholder strings like `__PROJECT_NAME__`, `__PLANNER_MODEL__`, `__AGENT_PREFIX__`, etc. were replaced in any generated file.

The bootstrap script does perform replacement, but if a new placeholder is introduced in the template without a matching entry in the `replacements` dict in `bootstrap_repo_scaffold.py`, the smoke test passes while the generated file still contains the raw placeholder string.

**Impact:** Regressions in placeholder handling are invisible to automated testing.

**Fix:** Add a check in `verify_render()` that scans generated text files for any string matching `__[A-Z_]+__` and fails if any remain.

---

### BUG-05 — `template_commit()` has no timeout and no fallback in the provenance writer

**File:** `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`

```python
result = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    cwd=managed_repo_root(),
    check=False,
    capture_output=True,
    ...
)
```

There is no `timeout=` argument. In a slow CI environment, a git operation can hang indefinitely, blocking scaffold generation with no error message. The fallback returns `"unknown"` only if the return code is non-zero, not on timeout.

**Impact:** Scaffold generation can hang silently in CI pipelines or environments where git is slow or unavailable.

**Fix:** Add `timeout=10` to the `subprocess.run` call and wrap in a `try/except subprocess.TimeoutExpired` that returns `"unknown"`.

---

## 2. Risks

### RISK-01 — `stage-gate-enforcer.ts` allows all `.opencode/` paths before plan approval

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`

The `isDocPath()` function allows write/edit operations on any path that starts with `.opencode/`. This means an agent could write to `.opencode/state/implementations/` before `approved_plan` is true, provided it does so through the `write` or `edit` tool rather than through `artifact_write`.

The audit script's `audit_missing_artifact_gates` check only looks at agent prompts for the word `artifact` or `approved_plan`, so it would not catch a bypass routed through a raw write.

**Impact:** The stage gate has a bypass path for implementation-stage artifacts.

**Fix:** Narrow `isDocPath()` to only allow writing to `docs/`, `tickets/`, `.opencode/state/plans/`, `.opencode/skills/`, and similar planning-only paths before approval. Block `.opencode/state/implementations/` until `approved_plan` is true.

---

### RISK-02 — `handoff_publish.ts` silently does nothing if `START-HERE.md` lacks the managed markers

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`

`mergeStartHere()` only injects the managed block if the existing file contains both `START_HERE_MANAGED_START` and `START_HERE_MANAGED_END`. If a user removes or renames those markers, subsequent calls to `handoff_publish` return success but write nothing new to `START-HERE.md`.

The tool's return value (`{ start_here, latest_handoff }`) does not indicate whether the merge was a no-op or an actual update. The calling agent has no way to detect that the handoff was silently discarded.

**Impact:** A repository that has had its `START-HERE.md` manually cleaned up will silently stop receiving handoff updates.

**Fix:** Return a `merged: boolean` flag in the result, and have the agent log a warning if `merged` is false.

---

### RISK-03 — `audit_invalid_tool_schemas` regex can match TypeScript syntax unrelated to tool arg schemas

**File:** `skills/repo-process-doctor/scripts/audit_repo_process.py`

```python
def tool_uses_plain_object_args(text: str) -> bool:
    return bool(re.search(r"\btype:\s*\"[A-Za-z]+\"", text) or
                re.search(r"\brequired:\s*(true|false)\b", text))
```

The pattern `type:\s*"[A-Za-z]+"` matches any TypeScript object literal with a `type` string field, including legitimate usage in plugin event handlers, MCP config objects, or JSON serialisation code. A false positive would flag a valid tool as having an invalid schema.

**Impact:** Repos with valid custom tools that happen to use `type:` string fields will receive spurious `invalid-opencode-tool-schema` errors.

**Fix:** Scope the check more narrowly — for example, only trigger when the file also contains `export default tool(` and the `type:` match appears inside the `args:` block specifically.

---

### RISK-04 — `opencode.jsonc` bash permission allows `sed *`, which the doctor flags as a mutation risk

**File:** `skills/repo-scaffold-factory/assets/project-template/opencode.jsonc`

The global bash permissions in the generated `opencode.jsonc` include `"sed *": "allow"`. The doctor's `MUTATING_SHELL_TOKENS` tuple includes `'"sed *": allow'` as a dangerous pattern. The audit script only checks agent `.md` files, not `opencode.jsonc`, so this is not currently caught — but it represents a latent inconsistency. If a future version of the doctor is expanded to scan config files, every generated repo will immediately fail the audit.

**Impact:** Future-proofing risk; potential to allow unintended file mutations through the global bash allowlist.

**Fix:** Remove `"sed *": "allow"` from the global `opencode.jsonc` bash permissions. Add it only in the specific agent definitions (e.g. the implementer) that genuinely need it.

---

### RISK-05 — `bootstrap_repo_scaffold.py` silently overwrites without `--force` if `dest` is a non-empty directory

**File:** `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`

`write_file()` raises `FileExistsError` if a target file exists and `--force` is not set. However, `copy_template()` iterates only the template's own top-level entries. If `dest` already contains files that are not in the template (e.g. source code), those files are simply ignored. A user could believe a full scaffold reset happened when only some files were written.

**Impact:** Partial overwrites are silently treated as success.

**Fix:** In non-force mode, add a pre-flight check that warns if the destination directory is non-empty. In force mode, log each file being overwritten.

---

### RISK-06 — No `engines` field in `package.json`; ESM `import.meta.url` in `bin/scafforge.mjs` requires Node ≥ 14

**File:** `package.json`, `bin/scafforge.mjs`

`bin/scafforge.mjs` uses `import.meta.url` and top-level `await`-compatible ESM. There is no `engines` field declaring the minimum Node.js version. Users on older Node versions will receive cryptic syntax errors rather than a clear message.

**Fix:** Add `"engines": { "node": ">=18.0.0" }` to `package.json`.

---

### RISK-07 — `devdocs/` contains Windows absolute paths that contradict the Linux-targeted output requirement

**Files:** `devdocs/history/research report.md`, `devdocs/scafforge-implementation-plan.md`

These files contain hardcoded Windows paths such as `C:\Users\rowan\.copilot\session-state\...` and `C:\Users\rowan\AppData\Local\Temp\...`. The plan document (section 4.6) explicitly states generated output must default to Linux-safe conventions. Having Windows paths in the dev docs embedded in the same repository creates contradictory signals for any agent reading the full context.

**Impact:** Agents scanning the repo may inherit Windows path assumptions, especially for commands in the planning stages.

**Fix:** Move `devdocs/` to `.gitignore` or sanitise the Windows paths. They serve historical documentation purposes but should not be part of the active operating context.

---

## 3. Contradictions

### CONTRA-01 — `docs/process/agent-catalog.md` is in the required read order but not in the conformance checklist

**Files:** `skills/repo-scaffold-factory/assets/project-template/AGENTS.md` (required read order step 5)
**File:** `skills/repo-scaffold-factory/references/opencode-conformance-checklist.json`

`AGENTS.md` lists `docs/process/agent-catalog.md` as step 5 in the required read order. The conformance checklist does not include this file in `required_files`. The smoke test and validator therefore cannot detect if this file goes missing.

**Fix:** Add `docs/process/agent-catalog.md` to `required_files` in the conformance checklist.

---

### CONTRA-02 — `docs/process/tooling.md` is referenced in template docs but not in `opencode.jsonc` instructions

**File:** `skills/repo-scaffold-factory/assets/project-template/opencode.jsonc`
**File:** `skills/repo-scaffold-factory/assets/project-template/docs/process/tooling.md`

The `opencode.jsonc` `instructions` array loads `docs/process/*.md`, which would pick up `tooling.md` via glob. However, if OpenCode resolves that glob literally (some versions do, some do not), and if it does not, `tooling.md` — which explains every important workflow tool — may not be loaded into context. The file is also not listed individually as a safety net.

**Fix:** Add `docs/process/tooling.md` as an explicit entry in the `instructions` array alongside the glob, as a defensive measure.

---

### CONTRA-03 — `TASKS.md` T-019 and T-020 are still listed as incomplete but the worklog says they are done

**File:** `TASKS.md` (items T-019, T-020)
**File:** `devdocs/worklog.md`

`TASKS.md` says in its status note that "the foundational baseline is now implemented" but still lists T-019 (improve `START-HERE.md`) and T-020 (improve `AGENTS.md`) in the body without a completion marker. The worklog describes improvements to both. An agent reading only `TASKS.md` will believe these are still open work items.

**Fix:** Mark T-019 and T-020 as complete with a note, or remove them from the open list.

---

### CONTRA-04 — `adapter manifest` promises adapters for `opencode` host but the OpenCode adapter section describes operating the generated repo, not installing Scafforge

**File:** `adapters/manifest.json`

The `opencode` adapter entry in the manifest says:
> "invoke generated repo after scaffold completion", "read START-HERE.md", "run the autonomous lifecycle inside the generated repo"

This describes what a user does *inside* a generated repo, not how to install or invoke the Scafforge generator from an OpenCode host. The other adapters (github-copilot, codex, gemini-cli) correctly describe installation and invocation. The opencode adapter is semantically different and will confuse readers.

**Fix:** Either describe how to invoke Scafforge *as a generator* from within an OpenCode session, or create a separate section for "post-scaffold usage" versus "adapter invocation".

---

## 4. Gaps

### GAP-01 — The CLI wrapper exposes no `audit` command

**File:** `bin/scafforge.mjs`

The `repo-process-doctor` audit script (`skills/repo-process-doctor/scripts/audit_repo_process.py`) is a powerful, standalone tool. The CLI wrapper has `render-full`, `render-opencode`, and `validate-contract` but no `audit-repo <path>` command. Users must know to invoke the Python script directly.

**Fix:** Add `scafforge audit-repo <path> [--format markdown|json|both]` as a fourth command in `bin/scafforge.mjs`.

---

### GAP-02 — No test that runs the doctor against the template itself to verify zero false positives

The doctor can produce false positives (see RISK-03). There is no test that runs `audit_repo_process.py` against a freshly generated scaffold and asserts the result has zero findings. This means a change to the template could accidentally introduce a pattern the doctor flags, and no automated check would catch it.

**Fix:** Add a step to `scripts/smoke_test_scafforge.py` that runs the doctor against the freshly generated `full_dest` fixture and asserts `finding_count == 0`.

---

### GAP-03 — `validate_scafforge_contract.py` does not check for unreplaced placeholders in the template

**File:** `scripts/validate_scafforge_contract.py`

The validator verifies that certain strings exist in certain files but never checks whether the template source files themselves contain placeholder strings that should not be in the final package. For example, if `__PLANNER_MODEL__` were accidentally left in a non-template file, the validator would not notice.

**Fix:** Add a check that scans all non-template source files (i.e. everything outside `assets/project-template/`) for `__[A-Z_]+__` patterns and fails if any are found.

---

### GAP-04 — No scaffold complexity budget is enforced

**File:** `devdocs/scafforge-implementation-plan.md` (interview question 2)

The implementation plan's interview section explicitly calls for a "scaffold complexity budget" defining maximum default agent count, skill count, command count, and custom tool count. This is described as necessary to keep generated repos navigable for weaker models. Nothing in the current codebase enforces or even documents such limits.

**Fix:** Add a complexity constants section to `skills/repo-scaffold-factory/SKILL.md` and a corresponding check in `validate_scafforge_contract.py` or the smoke test that counts generated agents/skills/tools and warns if counts exceed the defined budget.

---

### GAP-05 — No scaffold inventory manifest is generated

**File:** `devdocs/scafforge-implementation-plan.md` (interview question 3)

The plan calls for a machine-readable scaffold inventory manifest at something like `.opencode/meta/scaffold-manifest.json` listing every generated agent, tool, plugin, command, and skill with its purpose and authority level. This would give agents a compact map of the operating layer. `bootstrap-provenance.json` records generation metadata but not the surface inventory.

**Fix:** Extend `write_bootstrap_provenance()` in `bootstrap_repo_scaffold.py` to also write a `scaffold-manifest.json` that enumerates the generated `.opencode/` surfaces with purpose annotations drawn from their YAML frontmatter descriptions.

---

### GAP-06 — The `bin/scafforge.mjs` CLI wrapper has no `--help` for individual subcommands

**File:** `bin/scafforge.mjs`

Top-level `--help` is handled. Individual subcommands pass all arguments through to the Python scripts, which have their own `--help`. But the CLI wrapper does not surface those help texts or validate argument count before calling Python. A user passing wrong arguments to `render-full` gets a Python argparse error with no CLI-level context.

**Fix:** Add minimal argument validation and `--help` forwarding for each subcommand within the JS wrapper.

---

### GAP-07 — No `CONTRIBUTING.md` or development setup guide exists

The repository has `package.json`, Python scripts, TypeScript tools, and a `bin/` entry point. There is no document explaining how to set up a development environment, run the validators, run the smoke tests, or add a new skill. This matters because the `AGENTS.md` refers to external contributors running the maintenance checklist.

**Fix:** Add `CONTRIBUTING.md` covering: prerequisites (Node, Python), how to run `validate:contract` and `validate:smoke`, how to add a new skill to the flow manifest, and the definition of done for package changes.
