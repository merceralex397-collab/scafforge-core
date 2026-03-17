# Scafforge Recommendations — Validated Changes

**Date:** 2026-03-17
**Source material:**
- `research/gpttalker-agent-failure-analysis.md` — GPTTalker post-implementation audit
- `devdocs/research-minimax-m2-5-full.md` — MiniMax M2.5 integration guidance
- MiniMax official API docs, Hugging Face model card, Unsloth deployment guide
- Current Scafforge agent templates in `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/`

---

## 1. Sampling Parameter Corrections

### 1.1 Current Values vs MiniMax M2.5 Recommended Defaults

MiniMax's official documentation and the Hugging Face model card recommend **temperature=1.0, top_p=0.95, top_k=40** as the baseline for coding and agentic workflows. The current Scafforge templates use dramatically lower values that push the model into deterministic template-filling behavior.

| Agent Template | Current temp | Current top_p | Recommended temp | Recommended top_p |
|---|---|---|---|---|
| `__AGENT_PREFIX__-team-leader` | 0.2 | 0.7 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-planner` | 0.18 | 0.65 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-implementer` | 0.22 | 0.7 | 0.8 | 0.95 |
| `__AGENT_PREFIX__-reviewer-code` | 0.12 | 0.55 | 0.8 | 0.95 |
| `__AGENT_PREFIX__-reviewer-security` | 0.1 | 0.55 | 0.8 | 0.95 |
| `__AGENT_PREFIX__-tester-qa` | 0.12 | 0.6 | 0.8 | 0.95 |
| `__AGENT_PREFIX__-plan-review` | 0.14 | 0.6 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-backlog-verifier` | 0.1 | 0.55 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-ticket-creator` | 0.12 | 0.55 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-docs-handoff` | 0.14 | 0.6 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-utility-summarize` | 0.08 | 0.5 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-utility-explore` | 0.1 | 0.55 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-utility-web-research` | 0.1 | 0.55 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-utility-github-research` | 0.1 | 0.55 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-utility-shell-inspect` | 0.1 | 0.55 | 0.7 | 0.9 |
| `__AGENT_PREFIX__-utility-ticket-audit` | 0.08 | 0.5 | 0.7 | 0.9 |

**Rationale:** MiniMax M2.5 was designed and tuned to operate at temperature=1.0 / top_p=0.95. Lowering these values below ~0.7 pushes the model into a narrow, repetitive token-selection mode that removes the reasoning diversity needed for validation, edge-case detection, and adversarial thinking. The GPTTalker audit confirmed this: reviewers and QA agents at temperature 0.12 produced identical rubber-stamp approval templates instead of catching syntax errors, import failures, and missing tool registrations.

**Key principles for the updated values:**
- **Implementers and reviewers** (0.8 / 0.95): These roles need the most reasoning diversity — implementers to produce creative solutions, reviewers and QA to explore "what-if" failure scenarios.
- **Planners, team leaders, and coordination agents** (0.7 / 0.9): Slightly lower to favor structured output, but still well within MiniMax's functional range.
- **Utility agents** (0.7 / 0.9): Even utility agents should not be pushed to extreme determinism; 0.7 is conservative enough for summarization while avoiding template-filling.

### 1.2 top_k Parameter — Add to Templates

**Status: Confirmed — add to all agent templates**

The current templates do not specify `top_k` at all. MiniMax recommends `top_k: 40` as a standard companion to their temperature/top_p settings. Adding top_k provides an additional guard against low-probability token noise without over-constraining output diversity.

**Change:** Add `top_k: 40` to all agent template frontmatter in `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/`.

### 1.3 Do Not Hardcode in Core

**Status: Confirmed — already compliant**

The `devdocs/research-minimax-m2-5-full.md` and `scripts/validate_scafforge_contract.py` already enforce that MiniMax-specific model strings are not hardcoded in core logic. The sampling parameter changes are in template files (which are designed for customization), not in core package logic.

---

## 2. Stage Gate Execution Evidence

### 2.1 Require Execution Evidence in Artifacts

**Status: Confirmed — change needed**

**Finding:** The GPTTalker audit (§3.2) revealed that stage gates check artifact existence, not artifact content quality. A 50-byte QA artifact passed the gate.

**Change:** Update the team leader template (`__AGENT_PREFIX__-team-leader.md`) to add artifact quality validation rules under "Required stage proofs":

```markdown
Artifact quality requirements:

- implementation artifacts must contain evidence of at least one compile/import check (command output, not just file references)
- review artifacts must reference specific code findings, not just style observations
- QA artifacts must contain test execution output (command output with pass/fail counts)
- reject any QA artifact under 200 bytes as insufficient
- reject artifacts that claim validation "via code inspection" without execution evidence
```

**Files affected:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`

### 2.2 Add Mandatory Pre-Commit Validation to Implementer Prompt

**Status: Confirmed — change needed**

**Finding:** The GPTTalker audit (§4.1) found implementers generated high-quality code but never validated it would compile or import. Every hard blocker (syntax errors, type errors, circular imports) would have been caught by a simple compile check.

**Change:** Add to the implementer template (`__AGENT_PREFIX__-implementer.md`) rules section:

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

**Finding:** The GPTTalker audit (§4.3) showed the QA agent's own prompt instruction ("if no meaningful validation can be run, say so explicitly and return the missing requirement as a blocker") was actively violated. The agent never said it couldn't validate — it always claimed success via code inspection.

**Change:** Strengthen the QA template (`__AGENT_PREFIX__-tester-qa.md`) rules:

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

**Finding:** The GPTTalker audit (§3.5) showed reviewers had tools but didn't use them. The current Scafforge code reviewer template only permits read-only commands (`cat`, `rg`, `head`, `tail`, `git diff`). While it allows `bash: true`, the bash allowlist is restricted to file-reading tools.

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

This gives reviewers the ability to verify that code compiles and imports, without granting full write/execute access.

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

**Finding:** The GPTTalker audit (§3.6) identified a cascading trust chain where no agent independently verified another's claims. The team leader trusted QA, QA trusted the reviewer, the reviewer trusted the implementer, but nobody ran the tests.

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

**Finding:** The GPTTalker audit (§5.6) found that acceptance criteria written as properties ("Node registry schema is defined") allowed QA agents to match text against code structure without testing anything. Executable criteria ("running `python -c 'from module import X'` succeeds") give agents concrete commands to run.

**Change:** Update `skills/ticket-pack-builder/SKILL.md` to add guidance that acceptance criteria should be executable where possible. This is a documentation/guidance change, not a template change.

**Files affected:**
- `skills/ticket-pack-builder/SKILL.md`

---

## 6. Automated Smoke-Test Gate

### 6.1 Add Deterministic Smoke-Test Stage

**Status: Confirmed — recommended but deferred**

**Finding:** The GPTTalker audit (§5.5) recommended adding a non-agent-driven deterministic smoke test between QA and closeout. A shell script running compile checks and the test suite is more reliable than three agents that only read files.

**Recommendation:** This is a significant workflow contract change. The recommendation is validated and confirmed, but implementation should be a separate ticket because it requires:
- Adding a new stage to the workflow contract
- Updating `ticket_update` tool stage transitions
- Adding a smoke-test script generation step to `repo-scaffold-factory`
- Updating the stage-gate-enforcer plugin

This recommendation should be tracked as a follow-up item, not implemented in this batch.

---

## 7. Model Notes Documentation

### 7.1 Create MiniMax M2.5 Model Notes

**Status: Confirmed — change needed**

**Finding:** The `skills/agent-prompt-engineering/references/model-notes/` directory has a README explaining that model-specific notes should be written here, but no MiniMax M2.5 notes file exists. Given that MiniMax is a primary model for Scafforge-generated projects, this is a gap.

**Change:** Create `skills/agent-prompt-engineering/references/model-notes/minimax-m2.5.md` with:
- Recommended sampling parameters (temperature=1.0, top_p=0.95, top_k=40)
- Role-specific tuning guidance (lower end ~0.7 for coordination, ~0.8 for creative/validation work)
- Known quirks (tool-call hallucinations in long loops, template-filling at low temperature)
- Context window management notes (~200K advertised, lower operational)
- Prompting best practices for this model family

**Files affected:**
- `skills/agent-prompt-engineering/references/model-notes/minimax-m2.5.md` (new file)

---

## Summary of All Confirmed Changes

| # | Change | Files | Status |
|---|--------|-------|--------|
| 1 | Raise temperature/top_p across all agent templates | 16 template files in `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/` | Confirmed |
| 2 | Add `top_k: 40` to all agent templates | Same 16 template files | Confirmed |
| 3 | Add artifact quality rules to team leader | `__AGENT_PREFIX__-team-leader.md` | Confirmed |
| 4 | Add pre-commit validation to implementer | `__AGENT_PREFIX__-implementer.md` | Confirmed |
| 5 | Strengthen QA execution requirements | `__AGENT_PREFIX__-tester-qa.md` | Confirmed |
| 6 | Add compile/import bash permissions to reviewer | `__AGENT_PREFIX__-reviewer-code.md` | Confirmed |
| 7 | Add compile check instructions to reviewer | `__AGENT_PREFIX__-reviewer-code.md` | Confirmed |
| 8 | Add cross-agent trust policy to team leader | `__AGENT_PREFIX__-team-leader.md` | Confirmed |
| 9 | Guidance for executable acceptance criteria | `skills/ticket-pack-builder/SKILL.md` | Confirmed |
| 10 | Automated smoke-test gate | Workflow contract + multiple files | Confirmed — deferred to separate ticket |
| 11 | Create MiniMax M2.5 model notes | `skills/agent-prompt-engineering/references/model-notes/minimax-m2.5.md` | Confirmed |

---

## References

- [MiniMax-M2.5 Hugging Face Model Card](https://huggingface.co/MiniMaxAI/MiniMax-M2.5)
- [MiniMax API Best Practices](https://platform.minimax.io/docs/coding-plan/best-practices)
- [Unsloth MiniMax-M2.5 How to Run Guide](https://unsloth.ai/docs/models/minimax-m25)
- [MiniMax-M2 vLLM Recipes](https://docs.vllm.ai/projects/recipes/en/latest/MiniMax/MiniMax-M2.html)
- [LLM Sampling Parameter Guide](https://alouani.org/en/blog/temperature-top-p-top-k-llm-guide/)
- `research/gpttalker-agent-failure-analysis.md` — GPTTalker post-implementation audit
- `devdocs/research-minimax-m2-5-full.md` — MiniMax M2.5 integration guidance
