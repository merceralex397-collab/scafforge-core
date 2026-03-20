# Scafforge Recommendations — Validated Changes

**Date:** 2026-03-20
**Source material:**
- `research/gpttalker-agent-failure-analysis.md` — GPTTalker post-implementation audit
- Existing MiniMax integration guidance research notes
- MiniMax API best-practices guidance and deployment notes
- Current Scafforge agent templates in `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/`

---

## 1. Sampling Parameter Corrections

### 1.1 Current Values vs MiniMax 2.7 Operating Defaults

For this implementation batch, Scafforge will standardize all generated agents on **temperature=1.0, top_p=0.95, top_k=40** for MiniMax 2.7. The current templates use dramatically lower values that push the model into deterministic template-filling behavior and reduce validation quality.

| Agent Template | Current temp | Current top_p | Recommended temp | Recommended top_p |
|---|---|---|---|---|
| `__AGENT_PREFIX__-team-leader` | 0.2 | 0.7 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-planner` | 0.18 | 0.65 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-implementer` | 0.22 | 0.7 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-reviewer-code` | 0.12 | 0.55 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-reviewer-security` | 0.1 | 0.55 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-tester-qa` | 0.12 | 0.6 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-plan-review` | 0.14 | 0.6 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-backlog-verifier` | 0.1 | 0.55 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-ticket-creator` | 0.12 | 0.55 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-docs-handoff` | 0.14 | 0.6 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-utility-summarize` | 0.08 | 0.5 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-utility-explore` | 0.1 | 0.55 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-utility-web-research` | 0.1 | 0.55 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-utility-github-research` | 0.1 | 0.55 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-utility-shell-inspect` | 0.1 | 0.55 | 1.0 | 0.95 |
| `__AGENT_PREFIX__-utility-ticket-audit` | 0.08 | 0.5 | 1.0 | 0.95 |

**Rationale:** MiniMax 2.7 should not be forced into ultra-low-temperature reviewer and QA roles. The GPTTalker audit showed that heavily deterministic settings produced rubber-stamp validation instead of independent error detection. Scafforge will therefore use one uniform MiniMax 2.7 operating profile for all generated agents in this pack.

**Implementation note:** The earlier role-specific temperature split is intentionally superseded here. Coordination, implementation, review, QA, and utility agents will all use the same MiniMax 2.7 sampling defaults in generated templates.

### 1.2 top_k Parameter — Add to Templates

**Status: Confirmed — add to all agent templates**

The current templates do not specify `top_k` at all. Add `top_k: 40` to all agent template frontmatter in `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/`.

### 1.3 Do Not Hardcode in Core

**Status: Confirmed — already compliant**

The sampling parameter changes belong in template files and model-notes references, not in core package logic.

---

## 2. Stage Gate Execution Evidence

### 2.1 Require Execution Evidence in Artifacts

**Status: Confirmed — change needed**

**Finding:** The GPTTalker audit (§3.2) revealed that stage gates checked artifact existence, not artifact content quality. A tiny QA artifact passed the gate without executable evidence.

**Change:** Update the team leader template and workflow gating surfaces to require artifact quality checks, including:

```markdown
Artifact quality requirements:

- implementation artifacts must contain evidence of at least one compile/import check (command output, not just file references)
- review artifacts must reference specific code findings, not just style observations
- QA artifacts must contain test execution output or compile/import output with pass/fail or exit-code evidence
- reject any QA artifact under 200 bytes as insufficient
- reject artifacts that claim validation "via code inspection" without execution evidence
- smoke-test artifacts must contain raw command output and an explicit PASS/FAIL result
```

**Files affected:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`

### 2.2 Add Mandatory Pre-Commit Validation to Implementer Prompt

**Status: Confirmed — change needed**

**Finding:** The GPTTalker audit (§4.1) found implementers generated high-quality code but never validated it would compile or import.

**Change:** Add to the implementer template rules section:

```markdown
- before creating the implementation artifact, run at minimum:
  - a compile or syntax check on all new/modified source files
  - an import check for the primary module
  - the project test suite if it exists
- include the command output in the implementation artifact
- do not create an implementation artifact for code that fails these checks
```

**Files affected:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-implementer.md`

### 2.3 QA Must Execute, Not Inspect

**Status: Confirmed — change needed**

**Finding:** The GPTTalker audit (§4.3) showed the QA agent claimed success via code inspection instead of running checks.

**Change:** Strengthen the QA template rules:

```markdown
- "code inspection" alone is not validation — you must execute tests or compile checks
- run the project test suite and report pass/fail counts with command output
- if no test suite exists, run compile/syntax checks and import verification on all source files
- include raw command output in the QA artifact
- if the QA artifact does not contain command output, it will be rejected by the team leader
- a QA artifact under 200 bytes is almost certainly insufficient — add more evidence or return a blocker
```

**Files affected:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-tester-qa.md`

---

## 3. Reviewer Execution Permissions

### 3.1 Add Execution Bash Permissions to Code Reviewer

**Status: Confirmed — change needed**

**Finding:** The GPTTalker audit (§3.5) showed reviewers had tools but did not use them because the allowlist was too narrow.

**Change:** Add compile/import check permissions to the code reviewer bash allowlist:

```yaml
bash:
  "python -m py_compile*": allow
  "python -c *": allow
  "python3 -m py_compile*": allow
  "python3 -c *": allow
  "node -e *": allow
  "cargo check*": allow
  "go vet*": allow
  "tsc --noEmit*": allow
```

**Files affected:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md`

### 3.2 Add Compile Check Instructions to Reviewer Prompt

**Status: Confirmed — change needed**

**Change:** Add to the reviewer template rules:

```markdown
- verify that new/modified source files compile by running the appropriate compile check (e.g., `python -m py_compile`, `cargo check`, `tsc --noEmit`)
- verify that primary module imports succeed
- include compile/import check output in the review artifact
- do not approve code that fails to compile
```

**Files affected:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md`

---

## 4. Cross-Agent Trust Policy

### 4.1 Add Cross-Agent Trust Rules

**Status: Confirmed — change needed**

**Finding:** The GPTTalker audit (§3.6) identified a cascading trust chain where no agent independently verified another's claims.

**Change:** Add to the team leader template:

```markdown
Cross-agent trust policy:

- never accept a downstream claim without evidence
- "tests pass" must be accompanied by test output in the artifact
- "code compiles" must be accompanied by compiler/interpreter output
- if evidence is missing from an artifact, request it before advancing the ticket
```

**Files affected:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`

---

## 5. Acceptance Criteria Style

### 5.1 Prefer Executable Acceptance Criteria

**Status: Confirmed — guidance change needed**

**Finding:** The GPTTalker audit (§5.6) found that property-style acceptance criteria allowed QA agents to match text against code structure without testing anything.

**Change:** Update `skills/ticket-pack-builder/SKILL.md` to state that acceptance criteria should be executable where possible, for example `python -c 'from module import X'` succeeds or `npm test` exits successfully.

**Files affected:**
- `skills/ticket-pack-builder/SKILL.md`

---

## 6. Automated Smoke-Test Gate

### 6.1 Add Deterministic Smoke-Test Stage

**Status: Confirmed — implement in this batch**

**Finding:** The GPTTalker audit (§5.5) recommended adding a non-agent-driven deterministic smoke test between QA and closeout.

**Change:** Implement a deterministic `smoke_test` tool and add a smoke-test stage between QA and closeout. The generated workflow must:
- require a QA artifact before the smoke-test stage begins
- run a deterministic smoke-test tool instead of delegating this stage to another agent
- register a canonical smoke-test artifact under `.opencode/state/smoke-tests/`
- require a passing smoke-test artifact before `done`
- update workflow docs, stage gating, and process-version metadata accordingly

**Files affected:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts` (new)
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-docs-handoff.md`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/workflow.md`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/tooling.md`
- `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`

---

## 7. Model Notes Documentation

### 7.1 Create MiniMax 2.7 Model Notes

**Status: Confirmed — change needed**

**Finding:** The `skills/agent-prompt-engineering/references/model-notes/` directory has a README explaining that model-specific notes should be written there, but no MiniMax 2.7 notes file exists.

**Change:** Create `skills/agent-prompt-engineering/references/model-notes/minimax-m2.7.md` with:
- Scafforge operating defaults (`temperature=1.0`, `top_p=0.95`, `top_k=40`)
- Known low-temperature failure mode from the GPTTalker audit
- Guidance to include executable evidence when MiniMax is used in reviewer and QA roles
- Prompting and context-management notes for MiniMax 2.7 in this scaffold

**Files affected:**
- `skills/agent-prompt-engineering/references/model-notes/minimax-m2.7.md` (new)

---

## Summary of All Confirmed Changes

| # | Change | Files | Status |
|---|--------|-------|--------|
| 1 | Raise temperature/top_p across all agent templates to uniform MiniMax 2.7 defaults | 16 template files in `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/` | Confirmed |
| 2 | Add `top_k: 40` to all agent templates | Same 16 template files | Confirmed |
| 3 | Add artifact quality rules to team leader and workflow gates | Team leader template + workflow tool/plugin files | Confirmed |
| 4 | Add pre-commit validation to implementer | `__AGENT_PREFIX__-implementer.md` | Confirmed |
| 5 | Strengthen QA execution requirements | `__AGENT_PREFIX__-tester-qa.md` | Confirmed |
| 6 | Add compile/import bash permissions to reviewer | `__AGENT_PREFIX__-reviewer-code.md` | Confirmed |
| 7 | Add compile check instructions to reviewer | `__AGENT_PREFIX__-reviewer-code.md` | Confirmed |
| 8 | Add cross-agent trust policy to team leader | `__AGENT_PREFIX__-team-leader.md` | Confirmed |
| 9 | Guidance for executable acceptance criteria | `skills/ticket-pack-builder/SKILL.md` | Confirmed |
| 10 | Deterministic smoke-test gate | Workflow contract + new `smoke_test` tool | Confirmed |
| 11 | Create MiniMax 2.7 model notes | `skills/agent-prompt-engineering/references/model-notes/minimax-m2.7.md` | Confirmed |

---

## References

- [MiniMax API Best Practices](https://platform.minimax.io/docs/coding-plan/best-practices)
- [MiniMax-M2 vLLM Recipes](https://docs.vllm.ai/projects/recipes/en/latest/MiniMax/MiniMax-M2.html)
- [LLM Sampling Parameter Guide](https://alouani.org/en/blog/temperature-top-p-top-k-llm-guide/)
- `research/gpttalker-agent-failure-analysis.md` — GPTTalker post-implementation audit
