# Scafforge Comprehensive Hardening Plan

**Created:** April 2, 2026
**Status:** Active — ready for phased implementation
**Scope:** Full package hardening for universal project-class support

---

## Mission

Make Scafforge robust enough that a weaker AI can operate safely inside a generated repo for **any supported project class** — compilers, operating systems, websites, AI agents, TUIs, Unity/Unreal/Godot games, Windows programs, Linux programs, packages, and anything else — without getting trapped between contradictory workflow surfaces, missing stack guidance, shallow validation, or non-functional generated code.

This plan addresses two verified root failures:

1. **Agents in generated repos hit workflow blockers** — contradictory transition guidance, verdict-blind gating, smoke-test tool bugs, lease confusion, and stack-ignorant bootstrap surfaces leave weaker models stuck.
2. **Generated products are non-functional** — agents claim completion while code doesn't compile, tests don't pass, and required SDKs are missing, because audit doesn't check code quality, execution depth is Python-only, and review/QA gates check artifact existence rather than verdict content.

## Evidence Sources

All claims in this plan are backed by verified evidence from the codebase. Each phase file cites specific files, functions, and line ranges.

### Primary sources

| Source | What it proves |
|--------|---------------|
| `skills/scafforge-audit/scripts/audit_execution_surfaces.py` | The only deep execution check is `audit_python_execution()` — no equivalent for any other language |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts` | Stack detection exists for Python, Node, Rust, Go only — no Godot, Java, Android, C/C++, .NET, Flutter, Swift, Zig, or custom toolchain support |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts` | Smoke patterns recognize only pytest, cargo test, go test, npm/pnpm/yarn/bun test — no patterns for `godot --headless`, `gradle test`, `dotnet test`, `flutter test`, `make test`, `zig test`, or any other stack |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts` | Transition guidance checks artifact existence, not artifact verdict — a FAIL review still recommends advancing |
| `skills/scafforge-audit/scripts/shared_verifier.py` | Greenfield proof gates check workflow-surface alignment only — no stack-viability or build-readiness checks |
| `skills/scafforge-audit/scripts/audit_reporting.py` | `build_ticket_recommendations()` routes all non-EXEC/ENV findings to `scafforge-repair` — insufficient escalation for package-level defects |
| `skills/scafforge-repair/scripts/apply_repo_process_repair.py` | Uses `shutil.rmtree` plus `shutil.copytree` for managed-surface replacement — no backup, diff, or preservation strategy |
| `glitchresearch.md` | 27 documented agent confusion events, 7 code quality failures, 7 core workflow issues from a single Godot test run |
| `livetesting/glitch/diagnosis/20260401-215051/` | Audit found only 4 findings (WFLOW006, WFLOW012, WFLOW013, read-only-shell-mutation) — missed environment gaps, code quality, verdict-blind gating, smoke-test bugs, and SDK absence |
| `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py` | Model profile detection uses fragile substring matching; no idempotency check on target directory |

### Secondary sources

| Source | What it shows |
|--------|-------------|
| `livetesting/glitch/glitchblock1.md` | Actual agent session showing successful-but-shallow ticket progression |
| `references/competence-contract.md` | Package promise: one legal next move, no hidden state, truthful tools |
| `references/one-shot-generation-contract.md` | Greenfield completion requires immediate continuation proof |
| `skills/scaffold-kickoff/SKILL.md` | The generation chain and its proof gates |
| `skills/project-skill-bootstrap/SKILL.md` | Stack-specific skill synthesis is agent-driven, not deterministic |
| `skills/opencode-team-bootstrap/SKILL.md` | Agent team customization is agent-driven, not deterministic |

## Plan Structure

| Phase | Title | Priority | Impact |
|-------|-------|----------|--------|
| [01](01-workflow-tool-contract-fixes.md) | Workflow Tool Contract Fixes | P0 | Stops agents hitting workflow blockers |
| [02](02-environment-bootstrap-universality.md) | Environment Bootstrap Universality | P0 | Makes bootstrap work for any stack |
| [03](03-audit-execution-depth.md) | Audit Execution Depth Beyond Python | P0 | Makes audit find real issues in any repo |
| [04](04-greenfield-proof-expansion.md) | Greenfield Proof Gate Expansion | P1 | Catches viability failures at generation time |
| [05](05-agent-prompt-hardening.md) | Agent Prompt and Delegation Hardening | P1 | Prevents weak-model confusion and overreach |
| [06](06-code-quality-feedback-loop.md) | Code Quality Feedback Loop | P1 | Prevents non-functional products |
| [07](07-repair-safety-and-coverage.md) | Repair Safety and Coverage | P1 | Makes repair trustworthy and complete |
| [08](08-scaffold-template-fixes.md) | Scaffold Template Mechanical Fixes | P2 | Fixes known template-level bugs |
| [09](09-contract-and-doc-updates.md) | Contract and Documentation Updates | P2 | Aligns docs with new capabilities |
| [10](10-multi-stack-proof-program.md) | Multi-Stack Proof Program | P2 | Proves hardening across project types |

## Dependency Graph

```
Phase 01 (workflow fixes)  ───┐
Phase 02 (env bootstrap)  ───┤
Phase 08 (template fixes)  ──┼──> Phase 04 (greenfield proof)
Phase 05 (prompt hardening) ──┤
Phase 03 (audit depth)  ─────┼──> Phase 06 (code quality loop) ──> Phase 07 (repair) ──> Phase 09 (docs) ──> Phase 10 (proof)
```

Phases 01, 02, 03, 05, and 08 can proceed in parallel.
Phase 04 depends on 01, 02, and 08.
Phase 06 depends on 03.
Phase 07 depends on 06.
Phase 09 depends on all P0/P1 phases.
Phase 10 is the final validation pass.

## Definition of Done

This plan is complete when ALL of the following are true:

1. `environment_bootstrap.ts` successfully detects and bootstraps at least: Python, Node, Rust, Go, Godot, Java/Android, C/C++, .NET, and Flutter projects
2. `audit_execution_surfaces.py` can run deep execution checks for at least Python, Node, Rust, Go, and Godot projects
3. `smoke_test.ts` recognizes smoke patterns for all stacks that `environment_bootstrap.ts` detects
4. Transition guidance in `ticket_lookup.ts` is verdict-aware — a FAIL review blocks forward motion
5. Greenfield proof gates check stack-specific viability, not just workflow-surface alignment
6. Audit generates code-quality findings that repair converts to remediation tickets
7. Repair uses backup/diff before destructive replacement and generates follow-up tickets for code issues
8. Agent prompts prevent weak-model confusion, overreach, and evidence-free PASS claims
9. Generated repos expose one legal next move at every step for any supported stack
10. All changes are validated by at least two proof-target project types (Python + one non-Python)

## What This Plan Does NOT Do

- It does not repair Glitch's Godot source code (that is subject-repo development work)
- It does not add multi-host output support (generated output remains OpenCode-oriented)
- It does not create version-locked templates for every stack (it creates extensible adapters)
- It does not auto-install arbitrary external skills or tools
- It does not redesign the core workflow state machine (it fixes contradictions within the existing one)
