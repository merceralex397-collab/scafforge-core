# Scafforge — Improvements & Additions

This document covers enhancements beyond bug fixes: new capabilities, UX improvements, structural changes, and hardening that would meaningfully advance the project. Each item includes rationale, suggested implementation approach, and how it maps to the existing roadmap.

---

## Section 1 — Developer Experience

### IMP-01 — Add a `CONTRIBUTING.md`

**Priority: High**

Currently there is no onboarding path for a new developer, agent, or future maintainer. The maintenance checklist in `AGENTS.md` assumes the reader already knows how to run validations.

**What to include:**
- Prerequisites: Python 3.10+, Node 18+
- How to run `npm run validate:contract` and `npm run validate:smoke`
- How to add a new skill (update `skills/skill-flow-manifest.json`, create `skills/<name>/SKILL.md`, add to validator)
- How to run the doctor against a generated scaffold: `python skills/repo-process-doctor/scripts/audit_repo_process.py <path>`
- Definition of done for package changes (already in `AGENTS.md` but should be mirrored here)
- How to update the template and verify the conformance checklist still passes

**Roadmap alignment:** Closes Phase 9 (unify documentation).

---

### IMP-02 — Add subcommand `scafforge audit-repo <path>` to the CLI wrapper

**Priority: High**

The process doctor is the most operationally useful standalone tool, yet it requires knowing the Python script path. Surfacing it through the CLI wrapper makes the developer loop: scaffold → audit → repair much more discoverable.

**Suggested implementation in `bin/scafforge.mjs`:**
```javascript
if (command === "audit-repo") {
  if (!args[0]) {
    console.error("Usage: scafforge audit-repo <repo-path> [--format markdown|json|both]")
    process.exit(1)
  }
  runPython(path.join(root, "skills", "repo-process-doctor", "scripts", "audit_repo_process.py"), args)
}
```

**Roadmap alignment:** Closes Phase 8 (validation harness); directly supports the post-scaffold repair loop described in Phase 0.

---

### IMP-03 — Add a `--dry-run` flag to the bootstrap scripts

**Priority: Medium**

Currently `bootstrap_repo_scaffold.py` either succeeds (writing files) or fails (refusing to overwrite without `--force`). There is no way to preview what would be written without committing to it. This is particularly useful before overwriting an existing OpenCode layer in a retrofit run.

**Suggested change:** When `--dry-run` is set, `write_file()` prints `[DRY-RUN] would write: <path>` instead of writing. The provenance and state directories are not created either.

**Roadmap alignment:** Improves installer UX (Phase 7).

---

### IMP-04 — Surface the doctor findings as machine-readable JSON in the CLI return code

**Priority: Medium**

The doctor script already supports `--format json` but it prints to stdout. For integration into CI pipelines, it would be useful for `scafforge audit-repo` to set a non-zero exit code based on severity (it already has `--fail-on error|warning|never`) and optionally write JSON output to a file. The CLI wrapper currently passes all args through, so this is already mostly possible — it just needs documentation and an example CI workflow.

**Suggested addition:** A `docs/ci-integration.md` example showing how to use `scafforge audit-repo . --fail-on error --json-output audit-results.json` in a GitHub Actions workflow.

---

## Section 2 — Template & Generated Repo Quality

### IMP-05 — Rename `CODEXSETUP` markers to `SCAFFORGE`

**Priority: High**

See BUG-01 in the critical issues report. Beyond being a bug, this is an improvement opportunity: the new marker name can be more descriptive, e.g.:

```
<!-- SCAFFORGE:MANAGED_START — do not remove or rename these markers -->
```

Adding a visible instruction inside the comment reduces the likelihood of a user accidentally removing the marker and silently breaking handoff updates.

**Files to change:** `_workflow.ts` (two constants), `START-HERE.md` template, and add `CODEXSETUP` to `validate_scafforge_contract.py`'s disallowed list.

---

### IMP-06 — Add a `scaffold-manifest.json` to generated repos

**Priority: Medium**

The implementation plan's interview section calls for a machine-readable inventory of every generated surface. `bootstrap-provenance.json` records *how* the scaffold was generated; a `scaffold-manifest.json` should record *what* was generated.

**Suggested shape:**
```json
{
  "version": 1,
  "generated_at": "2025-01-01T00:00:00Z",
  "agents": [
    { "id": "myproject-team-leader", "role": "visible-primary", "file": ".opencode/agents/myproject-team-leader.md" }
  ],
  "tools": [...],
  "plugins": [...],
  "commands": [...],
  "skills": [...]
}
```

**Implementation:** Extend `write_bootstrap_provenance()` or add a separate `write_scaffold_manifest()` function in `bootstrap_repo_scaffold.py`. Extract agent/tool/plugin descriptions from YAML frontmatter during template copy.

**Roadmap alignment:** Directly addresses interview question 3 in the implementation plan. Also enables a future `scafforge list-surfaces <path>` command.

---

### IMP-07 — Strengthen `START-HERE.md` template to be self-contained

**Priority: Medium**

The current template's "Next Action" section contains placeholder prose. The plan (interview question 4) calls for critical restart files to be self-contained: they should not depend on another file to understand what is happening.

**Suggested additions to the template:**
- A `## State Disagreement Resolution` section explaining what to do if `workflow-state.json` and `manifest.json` show different active tickets (manifest wins)
- A `## If The Context Is Stale` section with the exact command to refresh: `/resume` or the `context_snapshot` tool
- A `## Blockers` section (initially empty, meant to be filled by the docs-handoff agent)

**Roadmap alignment:** Closes T-019 properly.

---

### IMP-08 — Add a `CHANGELOG.md`

**Priority: Low-Medium**

The worklog (`devdocs/worklog.md`) is comprehensive but is a prose narrative, not a structured changelog. As Scafforge moves toward a publishable npm package, a structured `CHANGELOG.md` following Keep A Changelog conventions will be important for users tracking what changed between versions.

**Initial content:** A `v0.1.0` entry summarising the items from the worklog's implementation steps.

---

### IMP-09 — Add `engines` and `repository` fields to `package.json`

**Priority: Medium**

```json
{
  "engines": { "node": ">=18.0.0" },
  "repository": {
    "type": "git",
    "url": "https://github.com/<owner>/scafforge"
  }
}
```

Without `engines`, users on Node 14/16 will encounter cryptic ESM errors. The `repository` field is required for npm to display the correct source link.

---

## Section 3 — Testing & Validation

### IMP-10 — Doctor zero-findings test against the generated scaffold

**Priority: High**

After the smoke test generates a scaffold, immediately run the doctor against it and assert `finding_count == 0`. This creates a tight feedback loop: any change to the template that introduces a workflow smell is caught automatically.

**Implementation in `scripts/smoke_test_scafforge.py`:**
```python
import subprocess

def run_doctor(dest: Path) -> None:
    result = subprocess.run(
        ["python",
         str(ROOT / "skills" / "repo-process-doctor" / "scripts" / "audit_repo_process.py"),
         str(dest), "--format", "json"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout.split('\n')[-1])  # last line is JSON
    if data["finding_count"] > 0:
        raise RuntimeError(f"Doctor found {data['finding_count']} findings in generated scaffold")
```

---

### IMP-11 — Add placeholder replacement check to smoke test

**Priority: High** (see BUG-04)

```python
def check_no_unreplaced_placeholders(dest: Path) -> None:
    import re
    pattern = re.compile(r'__[A-Z][A-Z_]+__')
    for path in dest.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".json", ".jsonc", ".ts", ".yaml"}:
            text = path.read_text(encoding="utf-8")
            matches = pattern.findall(text)
            if matches:
                raise RuntimeError(f"Unreplaced placeholders in {path}: {matches}")
```

---

### IMP-12 — Add weak-model prompt regression scenarios

**Priority: Medium**

The implementation plan (interview question 5) explicitly calls for a test pack that validates prompt behaviour under adversarial conditions. While full LLM testing is expensive, the scenarios can be encoded as static assertions on the prompt text itself — verifying that key rails are present.

**Suggested static checks (`scripts/validate_scafforge_contract.py`):**
- Planner prompt contains "return a blocker" (not just "ask")
- Plan review prompt contains "Decision: APPROVED or REVISE"
- Team leader prompt contains all required stage proof checks
- Implementer prompt contains "confirmed `approved_plan` is already true"
- No agent prompt contains "summarize and stop" without a completion condition

---

### IMP-13 — Add a `validate_no_stale_references.py` script

**Priority: Medium**

The doctor checks for some path drift, but there is no validator that confirms every file path referenced in skill `SKILL.md` files actually exists. For example, if a reference file is renamed, the skill silently points at a ghost.

**Suggested check:** Parse every `SKILL.md`'s `## References` section, extract file paths, and verify each exists relative to the skill's directory.

---

## Section 4 — Architectural Improvements

### IMP-14 — Extract `isDocPath` logic in `stage-gate-enforcer.ts` into configuration

**Priority: Medium**

The current hardcoded list of safe-before-approval paths in `stage-gate-enforcer.ts` means any change to the artifact directory structure requires editing a plugin file. This could instead be driven by a small config block in `opencode.jsonc` or a dedicated `gate-config.json`, making it easier to customise per-project without touching the plugin source.

**Suggested approach:** Read allowed pre-approval paths from a `.opencode/config/stage-gate.json` file if present, falling back to the current hardcoded defaults.

---

### IMP-15 — Add `merged` return field to `handoff_publish.ts`

**Priority: Medium** (see RISK-02)

```typescript
return JSON.stringify({
  start_here: startHere,
  latest_handoff: handoffCopy,
  merged: existingStartHere.includes(START_HERE_MANAGED_START)
}, null, 2)
```

This allows calling agents to detect a silent no-op and log a warning.

---

### IMP-16 — Introduce an optional `compaction-preservation` plugin

**Priority: Medium**

The research report (`devdocs/history/research report.md`) identifies protecting ticket state, artifact references, and handoff outputs from context compaction as one of the most important improvements from the OpenCode ecosystem. The current `session-compactor.ts` plugin adds a generic note but does not actually protect any specific tool outputs.

**Suggested implementation:** A new plugin `compaction-guard.ts` that, on `experimental.session.compacting`, reads the current `workflow-state.json` and latest handoff and appends a compact summary of: active ticket ID, stage, approved_plan status, and the canonical paths of the three most recent artifacts. This ensures the agent always has the minimum context needed to continue after compaction.

**Roadmap alignment:** Directly addresses interview question 3 (compaction preservation) and the research report's amendment 5.3.

---

### IMP-17 — Add a complexity budget validator

**Priority: Medium** (see GAP-04)

Based on the implementation plan's interview question 2, add a check to `validate_scafforge_contract.py` (or the smoke test) that counts generated surfaces and warns if they exceed sane defaults:

```python
MAX_AGENTS = 15
MAX_SKILLS = 12
MAX_TOOLS = 12
MAX_PLUGINS = 6
MAX_COMMANDS = 6
```

These are not hard limits but should produce a warning with guidance to check if the generated surface area is justified.

---

### IMP-18 — Separate `devdocs/` from the active operating context

**Priority: Medium**

`devdocs/worklog.md` and `devdocs/history/research report.md` are valuable historical documents but contain Windows paths, internal session IDs, and footnote-heavy content that can pollute an agent's reading of the repo. They are not linked from `opencode.jsonc`'s `instructions` array, which helps, but they are still present in the repository and discoverable by any agent with `read` permissions.

**Options:**
1. Add `devdocs/` to `.gitignore` so they are not committed to the public package
2. Move them to `docs/history/` and add a comment in `AGENTS.md` noting they are historical reference, not active operating guidance
3. Sanitise the Windows paths before retaining

---

## Section 5 — Skill-Level Improvements

### IMP-19 — `scaffold-kickoff` SKILL.md should include a run-type classification decision tree

**Priority: Medium**

`scaffold-kickoff` is described as the default entrypoint that decides whether a run is greenfield, retrofit, or targeted refinement. The skill's `SKILL.md` currently describes the greenfield flow in detail but gives almost no guidance on how to *classify* the incoming repo. An agent using this skill for the first time has to infer the classification logic.

**Suggested addition:** A `## Classification` section with a simple decision tree:
- If no `docs/spec/CANONICAL-BRIEF.md` and no `opencode.jsonc` → greenfield
- If `CANONICAL-BRIEF.md` exists but no `.opencode/` → retrofit
- If both exist → targeted refinement

---

### IMP-20 — `repo-process-doctor` SKILL.md should document what "safe repair" means concretely

**Priority: Medium**

The skill says "default to `apply-repair` unless explicitly blocked" but the `references/repair-playbook.md` already has a useful `Safe-repair boundary` section that lists the difference. This content should be surfaced directly in the main `SKILL.md` rather than only in a reference file, because agents will read the skill first and may not follow the reference link.

**Suggested addition:** Add a `## What Safe Repair Means` section to `repo-process-doctor/SKILL.md` with a 5-line summary from the playbook.

---

### IMP-21 — Add a `## Failure Modes` section to `ticket-execution/SKILL.md`

**Priority: Low-Medium**

The ticket execution skill describes the required order but says nothing about what to do when a stage fails or produces a blocker. An agent following the skill to the letter and encountering a missing artifact has no guidance within the skill itself.

**Suggested addition:**
```markdown
## Failure Modes

- If a required artifact is missing at stage transition: return a blocker to the team leader, do not advance
- If plan review returns REVISE: route back to planner with the specific revision request
- If QA produces blocking findings: return to the implementer with the finding list before marking done
```

---

### IMP-22 — Add `references/brief-examples.md` to `spec-pack-normalizer`

**Priority: Low**

The normalizer has a schema (`references/brief-schema.md`) but no worked example. For agents using this skill against a complex or ambiguous input, a concrete before/after example of "messy spec → canonical brief" would reduce hallucination risk and improve output consistency.

---

## Section 6 — Long-Term Structural Additions

### IMP-23 — Introduce a `profiles/` directory for scaffold complexity profiles

**Priority: Low-Medium**

The implementation plan calls for at minimum two scaffold profiles: minimum deterministic and full orchestration. Currently there is effectively only one profile. A `profiles/` directory containing `minimum.json` and `full.json` manifests would allow the bootstrap script to accept a `--profile` flag and generate different surface areas accordingly, without duplicating template logic.

**Suggested structure:**
```
profiles/
  minimum.json   — core agents + tools only, no utility specialists, no research delegation
  full.json      — current default (all agents, skills, utility pack)
  custom.json    — (user-provided override)
```

---

### IMP-24 — Add a `scafforge init` interactive wizard

**Priority: Low**

Currently a user must know all the required flags (`--project-name`, `--model-provider`, `--planner-model`, `--implementer-model`) to generate a scaffold. A guided interactive wizard (`scafforge init`) that prompts for each value and then calls the bootstrap script would significantly lower the barrier to first use and reduce the chance of missing required arguments.

This aligns directly with the "batched decision interview packet" concept in the implementation plan (interview question 8).

---

### IMP-25 — Document and test the retrofit flow as a first-class scenario

**Priority: Medium**

The retrofit flow (spec-pack-normalizer → opencode-team-bootstrap → ticket-pack-builder → ...) is described in `AGENTS.md` and `scaffold-kickoff/SKILL.md` but is not tested by the smoke test, which only tests `--scope full` and `--scope opencode`. There is no fixture that verifies a repo with existing docs gets the OpenCode layer added without overwriting the existing content.

**Suggested addition:** A third fixture in `scripts/smoke_test_scafforge.py` that pre-populates a destination with a mock `docs/` and `tickets/` structure, runs `--scope opencode`, and verifies the existing docs were not overwritten.
