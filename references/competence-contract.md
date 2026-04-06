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
- greenfield bootstrap must persist blocker state so missing host prerequisites stop the flow truthfully instead of being inferred from tool failures later
- model-tier configuration may change prompt density, but it must not change workflow fidelity, ownership boundaries, or proof requirements

## Authority And Publication

- diagnosis owns finding disposition and follow-up classification
- the generated runtime workflow layer owns canonical repo mutation
- `scafforge-pivot` owns pivot-state persistence and stale-surface routing
- `handoff-brief` owns restart publication, which may only happen from the verified final snapshot
- `agent-prompt-engineering` and the contract surfaces it hardens must keep the same owner map visible across prompts, workflow docs, and generated behavior
- repair-side restart rendering is the first duplicate-authority seam to collapse, not a secondary cleanup item

## Release Proof

- Tier 1 release proof uses stack-specific commands from [stack-adapter-contract.md](stack-adapter-contract.md)
- package-level smoke and contract validation remain useful, but they do not replace stack proof on a host that can run the declared toolchain
- unsupported or partially supported hosts must degrade truthfully instead of pretending release proof passed

## Stack coverage expectations

- Scafforge must detect and bootstrap Tier 1 stacks across Python, Node, Rust, Go, Godot, Java or Android, C or C++, and .NET
- Tier 1 greenfield handoff is not competent unless the stack-specific execution audit and reference-integrity audit both pass
- Tier 2 stacks must still get first-class detection and bootstrap guidance for Flutter or Dart, Swift, Zig, and Ruby
- Tier 3 stacks must still get first-class detection and explicit blocker reporting for Elixir, PHP, and Haskell
- Tier 4 generic fallback surfaces such as Makefile or shell-script repos must still expose truthful bootstrap blockers and one legal next move
- unsupported or partially supported stacks must degrade explicitly instead of being treated as Python-shaped by default

## Audit expectations

- audit must identify the underlying contradiction, not only the visible symptom
- when one finding appears, audit should inspect adjacent surfaces that can create the same trap
- repeated weekly recurrence of the same trap family is package non-convergence, not just another repo-local finding list
- audit must cover code-quality findings as well as workflow-surface findings
- audit must classify stack-specific execution failures under EXEC findings and broken canonical references under REF findings when those surfaces are already invalid

## Repair expectations

- repair must carry forward the audit evidence basis automatically
- repair is not converged if it can only prove the repo looks clean now; it must also prove the original trap no longer routes the operator into confusion
- managed-surface replacement must be non-destructive, with per-surface backup, restore-on-failure behavior, and recorded diff summaries in provenance
- repair must route source-layer EXEC and REF follow-up into canonical remediation tickets instead of mutating product code under the repair label

## Pivot expectations

- pivot must update canonical truth before regenerating derived surfaces
- pivot must leave ticket lineage and restart surfaces truthful to the new design
- post-pivot verification must prove the repo still exposes one legal next move

## Greenfield expectations

- generated tickets must have executable acceptance that belongs entirely to the ticket's own scope
- generated prompts must stop on contradictions instead of encouraging exploratory stage probing or workaround search
- greenfield generation must run environment bootstrap before specialization continues and halt when unresolved blockers still exist
- greenfield continuation proof must require zero critical execution-surface failures and zero broken canonical references before handoff
