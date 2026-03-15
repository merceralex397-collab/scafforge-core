# Scafforge — Suggestions for Improvement

These are non-critical enhancement ideas. None of these are bugs, schema errors, or contract violations. They are suggestions for how the project could become stronger, more usable, and more robust as it matures toward a publishable v1.

---

## Developer Experience

### SUG-01: Add a `scafforge init` interactive wizard

Currently a user must know all required flags (`--project-name`, `--model-provider`, `--planner-model`, `--implementer-model`) upfront. A guided wizard that prompts for each value would lower the barrier to first use. This aligns with the "batched decision interview packet" concept in the implementation plan.

---

### SUG-02: Add a `--dry-run` flag to the bootstrap scripts

There is no way to preview what would be written without committing to it. When `--dry-run` is set, `write_file()` could print `[DRY-RUN] would write: <path>` instead of writing. This is especially useful before overwriting an existing OpenCode layer in a retrofit run.

---

### SUG-03: Add `--help` forwarding for individual CLI subcommands

Top-level `--help` is handled, but individual subcommands pass all arguments through to Python scripts. A user passing wrong arguments to `render-full` gets a Python argparse error with no CLI-level context. The wrapper could validate argument count and forward `--help` to the underlying script.

---

### SUG-04: Add a `CHANGELOG.md`

The worklog is comprehensive but is a prose narrative. As Scafforge moves toward npm publication, a structured `CHANGELOG.md` following Keep A Changelog conventions would help users track what changed between versions. An initial `v0.1.0` entry could summarize the worklog's implementation steps.

---

### SUG-05: Add a CI integration example

Create a `docs/ci-integration.md` showing how to use `scafforge audit-repo . --fail-on error --json-output audit-results.json` in a GitHub Actions workflow. The doctor script already supports `--format json` and `--fail-on`, so this is mostly a documentation exercise.

---

## Template & Generated Output

### SUG-06: Make `START-HERE.md` template more self-contained

Add sections for:
- **State Disagreement Resolution** — what to do if `workflow-state.json` and `manifest.json` show different active tickets (manifest wins)
- **If The Context Is Stale** — the exact command to refresh (`/resume` or `context_snapshot`)
- **Blockers** — initially empty, meant to be filled by the docs-handoff agent

This aligns with the implementation plan's call for self-contained restart surfaces.

---

### SUG-07: Add a scaffold inventory manifest (`scaffold-manifest.json`)

Extend `write_bootstrap_provenance()` or add a separate function to write a `.opencode/meta/scaffold-manifest.json` listing every generated agent, tool, plugin, command, and skill with its purpose. This gives agents a compact map of the operating layer without needing to discover files individually.

Suggested shape:
```json
{
  "version": 1,
  "generated_at": "...",
  "agents": [
    { "id": "myproject-team-leader", "role": "visible-primary", "file": ".opencode/agents/myproject-team-leader.md" }
  ],
  "tools": [...],
  "plugins": [...],
  "commands": [...],
  "skills": [...]
}
```

---

### SUG-08: Extract `isDocPath` logic into configuration

The hardcoded list of safe-before-approval paths in `stage-gate-enforcer.ts` means any change to the artifact directory structure requires editing a plugin file. This could instead be driven by a `.opencode/config/stage-gate.json` file, making it customizable per-project without touching plugin source.

---

### SUG-09: Add a `compaction-preservation` plugin

The current `session-compactor.ts` adds a generic note but doesn't protect any specific tool outputs from context compaction. A more useful plugin would, on `experimental.session.compacting`, read `workflow-state.json` and append a compact summary of: active ticket ID, stage, approved_plan status, and the three most recent artifacts.

---

### SUG-10: Introduce scaffold complexity profiles

Add a `profiles/` directory with `minimum.json` and `full.json` manifests. The bootstrap script could accept a `--profile` flag to generate different surface areas accordingly, without duplicating template logic.

```
profiles/
  minimum.json   — core agents + tools only
  full.json      — current default (all agents, skills, utility pack)
  custom.json    — user-provided override
```

---

## Skill-Level Improvements

### SUG-11: Add a run-type classification decision tree to `scaffold-kickoff`

The skill describes the greenfield flow in detail but gives no guidance on how to classify an incoming repo. A simple decision tree:
- No `CANONICAL-BRIEF.md` and no `opencode.jsonc` → greenfield
- `CANONICAL-BRIEF.md` exists but no `.opencode/` → retrofit
- Both exist → targeted refinement

---

### SUG-12: Add a worked example to `spec-pack-normalizer`

The normalizer has a schema but no before/after example. A concrete "messy spec → canonical brief" transformation would reduce hallucination risk and improve output consistency for agents using the skill.

---

### SUG-13: Document "safe repair" directly in `repo-process-doctor/SKILL.md`

The skill says "default to `apply-repair` unless explicitly blocked" but the details are buried in `references/repair-playbook.md`. Agents read the SKILL.md first and may not follow references. A 5-line summary of what safe repair means would help.

---

### SUG-14: Add a `## Failure Modes` section to `ticket-execution` skill

The skill describes the required order but says nothing about what to do when a stage fails. Add guidance like:
- Missing artifact at stage transition → return blocker, don't advance
- Plan review returns REVISE → route back to planner
- QA produces blocking findings → return to implementer before marking done

---

### SUG-15: Consider reducing the default local skill count

The default pack ships 9 local skills. For a system designed for weaker models, this may be more than necessary. The implementation plan calls for a complexity budget but doesn't specify concrete limits. Consider whether skills like `workflow-observability` and `isolation-guidance` should be lazy-activated by default rather than always present.

---

## Code Quality

### SUG-16: Replace long single-line template literals with multi-line builders

`renderContextSnapshot()`, `renderStartHere()`, and `renderBoard()` in `_workflow.ts` produce strings using single-line template literals that are 200+ characters long. These are hard to read, edit, and debug. Using multi-line template literals or array `.join("\n")` would improve maintainability.

---

### SUG-17: Add JSDoc comments to `_workflow.ts` exports

This is the most critical shared module in the generated repo. Adding JSDoc comments to exported functions, types, and constants would help both human developers and AI agents understand the API surface.

---

### SUG-18: Add runtime schema validation for `manifest.json` reads

Currently `readJson<T>()` casts with `as T` and no validation. For a system where weaker models might corrupt state files, adding lightweight Zod validation on manifest reads would catch malformed state early rather than at the point of use.

---

### SUG-19: Use `import` instead of `subprocess.run` in `bootstrap_opencode_team.py`

The OpenCode bootstrap script could directly import `main()` from `bootstrap_repo_scaffold.py` instead of constructing and running a subprocess. This eliminates the process overhead and the dependency on the Scafforge repo being available as a file path at runtime.

---

## Testing & Validation

### SUG-20: Run the doctor against the generated scaffold in the smoke test

After the smoke test generates a scaffold, immediately run `audit_repo_process.py` against it and assert zero findings. This creates a tight feedback loop: any change to the template that introduces a workflow smell is caught automatically.

---

### SUG-21: Add weak-model prompt regression checks

Add static assertions to `validate_scafforge_contract.py` that verify critical prompt rails are present:
- Planner prompt contains "return a blocker"
- Plan review prompt contains "Decision: APPROVED or REVISE"
- Team leader prompt contains all required stage proof checks
- Implementer prompt contains "confirmed `approved_plan` is already true"
- No agent prompt contains "summarize and stop" without a completion condition

---

### SUG-22: Add a reference path validator

Parse every `SKILL.md`'s `## References` section, extract file paths, and verify each exists relative to the skill's directory. This catches renamed or deleted reference files before they cause runtime failures.

---

### SUG-23: Test the retrofit flow as a first-class scenario

Add a third fixture to the smoke test that pre-populates a destination with a mock `docs/` and `tickets/` structure, runs `--scope opencode`, and verifies the existing docs were not overwritten.

---

## Documentation

### SUG-24: Add `repository` field to `package.json`

```json
{
  "repository": {
    "type": "git",
    "url": "https://github.com/<owner>/scafforge"
  }
}
```

This is required for npm to display the correct source link on the package page.

---

### SUG-25: Consider separating `devdocs/` from the active repo surface

Options:
1. Add `devdocs/` to `.gitignore` so it's not part of the published package
2. Move to `docs/history/` with a note in `AGENTS.md` marking it as historical reference
3. At minimum, sanitize Windows paths and add a comment at the top of each file marking it as historical

---

### SUG-26: Add a one-paragraph summary of the doctor's capabilities to the main README

The process doctor is the most impressive component in the package but is barely mentioned in the README. A short section under "## Tools" explaining what the doctor does and how to run it would improve discoverability.
