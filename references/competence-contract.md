# Scafforge Competence Contract

Scafforge is not competent unless the generated workflow exposes one clear legal next move at every step.

## Core invariants

- every workflow state exposes one legal next action, one named owner, and one blocker return path
- operator confusion is package evidence when the next legal move is ambiguous, contradictory, or too expensive to infer
- no workflow step may depend on hidden operator memory of extra flags, follow-up commands, or omitted transcript inputs
- deterministic tools must fail truthfully and must not require impossible preconditions
- ticket acceptance criteria must be scope-isolated; if closeout depends on later-ticket work, the backlog split is wrong
- prompts, tools, workflow docs, restart surfaces, and ticketing must all describe the same state machine
- post-repair verification must prove both current-state cleanliness and causal-regression coverage when the repair basis was transcript-backed

## Audit expectations

- audit must identify the underlying contradiction, not only the visible symptom
- when one finding appears, audit should inspect adjacent surfaces that can create the same trap
- repeated weekly recurrence of the same trap family is package non-convergence, not just another repo-local finding list

## Repair expectations

- repair must carry forward the audit evidence basis automatically
- repair is not converged if it can only prove the repo looks clean now; it must also prove the original trap no longer routes the operator into confusion

## Pivot expectations

- pivot must update canonical truth before regenerating derived surfaces
- pivot must leave ticket lineage and restart surfaces truthful to the new design
- post-pivot verification must prove the repo still exposes one legal next move

## Greenfield expectations

- generated tickets must have executable acceptance that belongs entirely to the ticket's own scope
- generated prompts must stop on contradictions instead of encouraging exploratory stage probing or workaround search
