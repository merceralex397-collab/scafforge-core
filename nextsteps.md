# Scafforge — Next Steps

Instructions for finalizing the project after acting on the review findings and selected suggestions.

---

## Phase 1: Critical Fixes (Must Do Before Any Release)

### 1.1 Add `.gitignore` and remove committed bytecode

```bash
# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
node_modules/
.env
.env.*
!.env.example
.DS_Store
Thumbs.db
*.swp
*.swo
*~
.idea/
.vscode/
EOF

# Remove tracked .pyc files
git rm --cached -r skills/opencode-team-bootstrap/scripts/__pycache__/
git rm --cached -r skills/repo-process-doctor/scripts/__pycache__/
git rm --cached -r skills/repo-scaffold-factory/scripts/__pycache__/

git add .gitignore
git commit -m "Add .gitignore and remove committed .pyc files"
```

### 1.2 Replace `CODEXSETUP` markers with `SCAFFORGE`

Files to update:
1. `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts` — lines 74-75: change both constants
2. `skills/repo-scaffold-factory/assets/project-template/START-HERE.md` — lines 3 and 32: change both comments
3. `scripts/validate_scafforge_contract.py` — add `"CODEXSETUP"` to the `disallowed` list

New marker format:
```
<!-- SCAFFORGE:MANAGED_START — do not remove or rename these markers -->
<!-- SCAFFORGE:MANAGED_END -->
```

### 1.3 Remove invisible Unicode citation artifacts

Files to clean:
1. `README.md` — lines 105 and 247
2. `REVIEW-NOTES.md` — lines 68 and 84

The citation text (e.g. `citeturn375117search2turn375117search0...`) is wrapped in invisible private-use Unicode characters (U+E200, U+E201, U+E202). These must be removed by:
- Opening each file in a hex-aware editor and deleting the byte sequences `EE 88 80`, `EE 88 81`, `EE 88 82` plus the adjacent `citeturn...` text
- Or using a script to strip everything matching the pattern from the trailing text of the affected lines

### 1.4 Fix `context_snapshot.ts` in-memory mutation

In `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/context_snapshot.ts`, either:
- **Option A (recommended):** Remove the in-memory mutation entirely — always snapshot the true active ticket:
  ```typescript
  // Remove the if (args.ticket_id) block entirely
  const content = renderContextSnapshot(manifest, workflow, args.note)
  ```
- **Option B:** Persist the mutation by calling `saveWorkflowState(workflow)` after modifying it

### 1.5 Fix `workflow-state.json` / `manifest.json` initial state inconsistency

In `skills/repo-scaffold-factory/assets/project-template/.opencode/state/workflow-state.json`, align with the manifest:
```json
{
  "active_ticket": "SETUP-001",
  "stage": "scaffold",
  "status": "todo",
  "approved_plan": false
}
```

Or update the manifest ticket to `"stage": "planning"` and `"status": "ready"` if that's the intended initial state.

---

## Phase 2: Infrastructure (Should Do Before Publication)

### 2.1 Add `engines` field to `package.json`

```json
{
  "engines": { "node": ">=18.0.0" }
}
```

### 2.2 Fix `bin/scafforge.mjs` command dispatch

Replace the independent `if` blocks with an `else if` chain or command map:

```javascript
const commands = {
  "render-full": path.join(root, "skills", "repo-scaffold-factory", "scripts", "bootstrap_repo_scaffold.py"),
  "render-opencode": path.join(root, "skills", "opencode-team-bootstrap", "scripts", "bootstrap_opencode_team.py"),
  "validate-contract": path.join(root, "scripts", "validate_scafforge_contract.py"),
  "audit-repo": path.join(root, "skills", "repo-process-doctor", "scripts", "audit_repo_process.py"),
}

const script = commands[command]
if (!script) {
  console.error(`Unknown command: ${command}`)
  process.exit(1)
}
runPython(script, args)
```

### 2.3 Add `audit-repo` command to the CLI wrapper

Add to the command map (above) or as a new `if` block:
```javascript
if (command === "audit-repo") {
  if (!args[0]) {
    console.error("Usage: scafforge audit-repo <repo-path> [--format markdown|json|both]")
    process.exit(1)
  }
  runPython(path.join(root, "skills", "repo-process-doctor", "scripts", "audit_repo_process.py"), args)
}
```

Update the help text accordingly.

### 2.4 Add `CODEXSETUP` to the validator's disallowed list

In `scripts/validate_scafforge_contract.py`, add to the `disallowed` list:
```python
disallowed = [
    "CODEXSETUP",  # Add this
    "minimax-coding-plan/MiniMax-M2.5",
    # ... existing entries ...
]
```

### 2.5 Add placeholder replacement check to smoke test

In `scripts/smoke_test_scafforge.py`, add after `verify_render()`:
```python
import re

def check_no_unreplaced_placeholders(dest: Path) -> None:
    pattern = re.compile(r'__[A-Z][A-Z_]+__')
    for path in dest.rglob("*"):
        if path.is_dir():
            continue
        if path.suffix not in {".md", ".json", ".jsonc", ".ts", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8")
        matches = pattern.findall(text)
        if matches:
            raise RuntimeError(f"Unreplaced placeholders in {path}: {matches}")
```

Call it after each `verify_render()`.

### 2.6 Add doctor zero-findings check to smoke test

In `scripts/smoke_test_scafforge.py`, add after `verify_render()`:
```python
def run_doctor(dest: Path) -> None:
    doctor = ROOT / "skills" / "repo-process-doctor" / "scripts" / "audit_repo_process.py"
    result = subprocess.run(
        ["python", str(doctor), str(dest), "--format", "json"],
        capture_output=True, text=True
    )
    output_lines = [line for line in result.stdout.strip().split('\n') if line.strip()]
    for line in output_lines:
        try:
            data = json.loads(line)
            if "finding_count" in data and data["finding_count"] > 0:
                raise RuntimeError(f"Doctor found {data['finding_count']} findings in generated scaffold:\n{json.dumps(data['findings'], indent=2)}")
        except json.JSONDecodeError:
            continue
```

### 2.7 Add missing files to conformance checklist

In `skills/repo-scaffold-factory/references/opencode-conformance-checklist.json`, add to `required_files`:
```json
"docs/process/agent-catalog.md",
"docs/process/tooling.md"
```

### 2.8 Add `CONTRIBUTING.md`

Create a `CONTRIBUTING.md` covering:
- Prerequisites: Python 3.10+, Node 18+
- How to run `npm run validate:contract` and `npm run validate:smoke`
- How to add a new skill (update `skill-flow-manifest.json`, create `skills/<name>/SKILL.md`)
- How to run the doctor: `python skills/repo-process-doctor/scripts/audit_repo_process.py <path>`
- Definition of done for package changes (already in AGENTS.md, mirror here)

### 2.9 Fix `devdocs/research report.md` filename

Rename to `devdocs/research-report.md` (hyphenated, no space). Update any references.

### 2.10 Remove `sed *` from global `opencode.jsonc` bash permissions

In `skills/repo-scaffold-factory/assets/project-template/opencode.jsonc`, remove the `"sed *": "allow"` line from the global bash permissions. If `sed` is needed, add it only to the implementer agent's bash allowlist.

---

## Phase 3: Validation Pass

After applying all Phase 1 and Phase 2 fixes:

```bash
# Run the contract validator
python scripts/validate_scafforge_contract.py

# Run the smoke test (now with placeholder and doctor checks)
python scripts/smoke_test_scafforge.py

# Run the CLI wrapper
node bin/scafforge.mjs --help
node bin/scafforge.mjs validate-contract

# Run the doctor against a generated scaffold
python scripts/smoke_test_scafforge.py  # Implicitly tests this if Phase 2.6 is done
```

All must pass with zero errors.

---

## Phase 4: Packaging for Distribution

### 4.1 Decide on publication readiness

When ready to publish:
1. Remove `"private": true` from `package.json`
2. Add `"repository"` field with the GitHub URL
3. Add `"license"` field
4. Add a `"files"` array to whitelist what gets published:
   ```json
   {
     "files": [
       "bin/",
       "skills/",
       "scripts/",
       "adapters/",
       "README.md",
       "AGENTS.md",
       "TASKS.md",
       "REVIEW-NOTES.md"
     ]
   }
   ```
   This keeps `devdocs/`, `__pycache__/`, and review artifacts out of the published package.

### 4.2 Test installation

```bash
# Local install test
npm pack
npm install -g ./scafforge-core-0.1.0.tgz

# Verify CLI works from anywhere
scafforge --help
scafforge validate-contract
scafforge render-full --help  # Should forward to Python --help

# Clean up
npm uninstall -g @scafforge/core
```

### 4.3 Test cross-platform

The bootstrap scripts use `pathlib.Path` (cross-platform) and the TypeScript tools use `path.join()` (cross-platform). Verify on:
- **Linux/macOS**: The primary target. Run `smoke_test_scafforge.py` and verify generated paths.
- **Windows**: The development platform. Already tested implicitly.

### 4.4 Publish

```bash
npm publish --access public
```

---

## Phase 5: Making Scafforge Easy to Install for Any CLI Agent

### 5.1 npm global install (primary method)

Once published, the primary install path is:
```bash
npm install -g @scafforge/core
```

This gives the user the `scafforge` command globally. Usage:
```bash
scafforge render-full \
  --dest /path/to/new-project \
  --project-name "My Project" \
  --model-provider "openrouter" \
  --planner-model "openrouter/anthropic/claude-sonnet-4.5" \
  --implementer-model "openrouter/openai/gpt-5-codex"
```

### 5.2 npx (no-install method)

For one-off use:
```bash
npx @scafforge/core render-full --dest ./my-project --project-name "My Project" ...
```

### 5.3 Per-host adapter documentation

Create per-host adapter docs (in `adapters/`) explaining how each CLI host should invoke Scafforge:

**For GitHub Copilot CLI:**
```
Install: npm install -g @scafforge/core
Invoke:  scafforge render-full --dest . --project-name "My Project" ...
```

**For Codex:**
```
Install: npm install -g @scafforge/core
Invoke:  scafforge render-full --dest . --project-name "My Project" ...
```

**For OpenCode (post-scaffold):**
```
The generated repo is ready to use with OpenCode. Run:
  opencode
Then use /kickoff or /resume commands.
```

### 5.4 Consider a `scafforge init` wizard

For the best first-use experience, add an interactive wizard that prompts for each required value:

```bash
scafforge init
# > Project name: My Project
# > Destination: ./my-project
# > Model provider: openrouter
# > Planner model: openrouter/anthropic/claude-sonnet-4.5
# > Implementer model: openrouter/openai/gpt-5-codex
# > Utility model (optional, defaults to planner): 
# > Stack label: framework-agnostic
# > Generating scaffold...
```

This can be implemented with the `readline` module in Node.js or a library like `inquirer`.

---

## Phase 6: Post-Release Maintenance

### 6.1 Run the maintenance checklist from AGENTS.md after every change

- Verify the skill chain still makes sense end to end
- Verify `scaffold-kickoff` still describes the real default workflow
- Verify bootstrap-mode ticket generation happens in the full-cycle path
- Verify project-skill synthesis rules are still conservative
- Verify generated template paths match current OpenCode conventions
- Remove stale host-specific wording from core skills and docs

### 6.2 Keep the smoke test and doctor in the CI pipeline

Every PR should run:
```bash
npm run validate:contract
npm run validate:smoke
```

### 6.3 Track OpenCode API changes

The generated tools and plugins depend on `@opencode-ai/plugin`. Monitor for API changes in:
- Tool schema definition syntax (`tool.schema.*`)
- Plugin hook names and signatures
- Tool context properties (`sessionID`, `messageID`, `agent`, `directory`)
- Configuration format (`opencode.jsonc`)

---

## Summary Checklist

- [ ] Phase 1: Critical fixes (`.gitignore`, CODEXSETUP, citations, context_snapshot, workflow-state)
- [ ] Phase 2: Infrastructure (engines, CLI, validator, smoke test, CONTRIBUTING, conformance)
- [ ] Phase 3: Validation pass (all validators green, all tests pass)
- [ ] Phase 4: Packaging (`private: false`, `files` array, test install, publish)
- [ ] Phase 5: Distribution (adapter docs, optional wizard)
- [ ] Phase 6: Maintenance (CI pipeline, API tracking)
