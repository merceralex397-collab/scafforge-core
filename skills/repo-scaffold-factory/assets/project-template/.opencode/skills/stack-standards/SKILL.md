---
name: stack-standards
description: Hold the project-local standards for languages, frameworks, validation, and runtime assumptions. Use when planning or implementing work that should follow repo-specific engineering conventions.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

Current scaffold mode: `__STACK_LABEL__`

## Universal Engineering Standards

These rules apply to all work in this repository regardless of stack.

### Code Quality
- Write code for readability first; optimise only when profiled evidence justifies it.
- Keep functions and methods focused on a single responsibility; extract helpers when a unit exceeds a single screen of logic.
- Every public or exported symbol must have a documentation comment that describes intent, not implementation.
- Delete dead code instead of commenting it out; use version control to recover removed code.

### Quality Gate Commands

Use the smallest stack-appropriate command set that proves the code still builds, references resolve, and the test surface is callable.

- Python: `ruff check .`, `mypy .` when configured, `pytest --collect-only`
- Node.js: `npm run lint`, `tsc --noEmit`, `npm test`
- Rust: `cargo clippy`, `cargo test`
- Go: `go vet ./...`, `golangci-lint run`, `go test ./...`
- Godot: `godot --headless --check-only` when available, scene reference checks, autoload validation, project load/import verification
- C/C++: `cmake --build .`, compiler warning review, and the configured test target when present
- .NET: `dotnet build`, `dotnet test`
- Generic make-based repos: `make check` or `make test`

When the repo stack is finalized, rewrite this catalog so review and QA agents get the exact build, lint, reference-integrity, and test commands that belong to this project.

### Validation
- All external inputs (API payloads, file reads, environment variables) must be validated at the boundary before use.
- Assertions and precondition checks belong at the call site, not buried in utility helpers.
- Write tests for correctness-critical paths; treat flaky tests as bugs to fix before merge.

### Visual Quality For Reviewable Repos
- Treat visual review as a contract, not as optional taste commentary.
- Style choice is not a blocker by itself. Block only when layout, readability, hierarchy, finish, or feedback is broken.
- Use named failure categories such as `screen-fit failure`, `menu hierarchy failure`, `readability failure`, `silhouette failure`, `material readability failure`, and `motion-feedback failure`.
- Menus, title screens, HUDs, and modal overlays must fit common viewport shapes and keep the primary interaction surface readable.
- Prefer one clear focal surface plus compact supporting UI. Do not frame the whole screen with equal-weight chrome.
- For interactive work, put long notes, controls lists, or lore behind drawers, toggles, or pause states instead of leaving them permanently open.
- Prefer free/open tools by default when authoring or revising art direction inputs: Inkscape, Krita, GIMP, Blender, and similar FOSS tooling.

### Visual Proof In QA
- When `.opencode/meta/bootstrap-provenance.json` says `requires_visual_proof: true`, QA must include a structured visual-proof block before the ticket can enter smoke-test.
- The QA artifact should record:
  - `visual_proof_status: PASS|FAIL|BLOCKED|APPROVED|REJECT`
  - `visual_proof_evidence: <comma-separated screenshot/render paths>`
  - `visual_proof_surfaces: <comma-separated reviewed surfaces>`
  - `visual_rubric_blockers: none|<comma-separated blocker categories>`
  - `visual_style_note: <why the style is intentional or why a deviation is acceptable>`
- A repo can be stylized and still pass. It cannot pass while the first screen is clipped, unreadable, corner-pinned, or obviously placeholder-grade.

### Dependencies
- Add a dependency only when it solves a problem the project cannot reasonably solve itself.
- Pin dependency versions in lock files; never rely on floating ranges in production builds.
- Audit new dependencies for license compatibility before adding them.

### Process
- Use ticket tools to track work; do not silently advance stages without updating ticket state.
- Artifacts produced by each stage must be registered via `artifact_write` / `artifact_register`.
- Smoke tests run on the real binary or export target, not on a mocked surrogate.
- When the project stack is confirmed, replace this file's Universal Standards section with stack-specific rules using the `project-skill-bootstrap` skill.
