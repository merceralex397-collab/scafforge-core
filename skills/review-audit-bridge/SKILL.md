---
name: review-audit-bridge
description: Structure repo review, implementation audit, security review, and QA passes so they produce short, actionable findings rather than vague commentary. Use during implementation cycles after the initial scaffold exists, not during scaffolding itself.
---

# Review Audit Bridge

Use this skill to keep reviews evidence-based and stage-aware. This is for implementation cycles, NOT for the initial scaffold.

## When to use

- After a ticket has been implemented and needs code review
- After implementation review passes and needs security review
- After security review passes and needs QA
- When auditing an existing codebase for quality

Do NOT use during the initial scaffold flow — that's handled by `scaffold-kickoff`.

## Procedure

1. Restate the target change or ticket being reviewed
2. Read the approved plan and implementation artifacts
3. Check in this priority order:
   - Correctness bugs
   - Behavior regressions
   - Security or trust issues
   - Missing tests or validation gaps
   - Maintainability concerns
4. Produce prioritized findings with exact file references
5. End with residual risks and missing validation only after findings

## Rules

- Do not start with praise or summaries — findings come first
- Reference specific files and line ranges
- Each finding should be actionable (what to fix, not just what's wrong)
- Keep findings prioritized by severity

## References

- `references/review-sequence.md` for the review contract
