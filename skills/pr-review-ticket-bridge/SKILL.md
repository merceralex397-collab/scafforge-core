---
name: pr-review-ticket-bridge
description: Review a pull request, validate review comments against the actual implementation, and generate follow-up tickets only for findings that survive evidence-based triage. Use this as a host-side Scafforge skill after scaffolded repos are already operating.
---

# PR Review Ticket Bridge

Use this skill when you need Scafforge itself to inspect a pull request and turn valid findings into new tickets.

This is a host-side skill for the CLI agent using Scafforge. It is not part of the generated output repo's default ticket lifecycle.

## Procedure

### 1. Gather the full PR surface

Review all of these before judging comments:

- PR title and summary
- full diff
- commit history
- check runs or review status if available
- review comments and discussion comments
- any referenced issue or design context that materially changes comment validity

Do not treat a single comment in isolation as sufficient evidence.

### 2. Perform a professional review first

Evaluate:

- correctness
- regressions
- security boundaries
- missing validation or tests
- architectural drift
- whether requested changes are actually valid for the repo's contract

### 3. Triage review comments

For each material review comment:

- confirm whether the comment is valid, partially valid, outdated, or invalid
- tie the judgment to the actual diff and current repo contract
- reject comments that ask for invalid changes, duplicate existing follow-up work, or conflict with accepted project decisions

### 4. Generate follow-up tickets only for accepted findings

When a comment or review finding is valid and still actionable:

- create a ticket in the repo's canonical ticket format
- keep the ticket narrow and implementation-ready
- include the PR number, commit or file reference, and the reason the finding was accepted
- do not generate tickets for already-fixed or duplicate work

### 5. Leave an explicit audit trail

Return:

1. PR review summary
2. Valid findings
3. Rejected findings with rationale
4. Tickets created or proposed
5. Any blockers that need a human decision

## Rules

- review the implementation first, then judge the comments
- do not create tickets from invalid, stale, or purely stylistic comments
- preserve the repo's existing ticket contract; do not invent a second backlog format
- if the repo already has a ticket covering the same issue, update or reference that instead of duplicating it
- keep this skill out of the default greenfield scaffold chain

## References

- `references/review-contract.md`
