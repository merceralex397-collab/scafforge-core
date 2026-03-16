# Research: workflow and multi-agent operating patterns relevant to Scafforge

## Scope

This note compares Scafforge with two internal reference repos, `GPS` and `GPTTalker`, then cross-checks those patterns against broader public multi-agent workflow guidance.

Internal evidence reviewed:

- `Scafforge`
- `GPS`
- `GPTTalker`

External references:

- MetaGPT SOP / assembly-line model: <https://arxiv.org/abs/2308.00352>
- Microsoft multi-agent reference architecture: <https://microsoft.github.io/multi-agent-reference-architecture/index.html>
- AWS workflow-vs-collaboration guidance: <https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/multi-agent-collaboration.html>
- LLM multi-agent systems for software engineering review: <https://arxiv.org/abs/2404.04834>

## Executive summary

The strongest shared pattern across Scafforge, GPS, GPTTalker, and the external references is:

1. one visible orchestrator
2. sequential stage gates per ticket
3. specialized ownership lanes or domains
4. tool-backed workflow state instead of prose-only coordination
5. artifact proof before stage transitions
6. blockers instead of silent assumption-making

Scafforge should continue positioning itself as a structured workflow-agent scaffold, not a free-form peer collaboration system. The best default remains one visible team leader with bounded parallel lanes, strong artifact gates, and explicit guarded follow-up ticket creation.

## Comparative snapshot

| System | Lane ownership | Sequential vs parallel | Hierarchy | Migration / revalidation | Guarded ticket creation | PR review to ticket generation |
| --- | --- | --- | --- | --- | --- | --- |
| `Scafforge` | explicit `wave`, `lane`, `parallel_safe`, `overlap_risk` | sequential per ticket; bounded parallel lanes | single visible team leader by default | explicit `pending_process_verification`, backlog verifier, guarded `ticket_create` | strong and proof-backed | formalized as an optional host-side skill |
| `GPS` | strong domain-lane taxonomy | very strict; one specialist at a time | single visible team leader | strong artifact truth recomputation | strong execution gating, less formal ticket-creation guard | concrete review-to-follow-up pattern |
| `GPTTalker` | clear hub / node-agent / context split | sequential per ticket | single visible team leader | strong stage validation, weaker migration-specific lane | strong execution gating | follow-up risks exist, but no dedicated bridge |

## Key findings

### Lane ownership

`GPS` shows the value of true ownership lanes. `GPTTalker` shows a lighter-weight version through specialized implementers. Scafforge should keep `lane` and `wave` distinct, and use `parallel_safe` plus `overlap_risk` to make concurrency explicit instead of implied.

### Parallelism

All three systems keep the lifecycle sequential per ticket. The safest improvement is bounded cross-ticket parallelism only when:

- dependencies are satisfied
- overlap risk is low
- write-capable work does not collide in the same ownership lane

This is more robust for weaker models than introducing broad peer collaboration.

### Manager hierarchy

Neither GPS nor GPTTalker shows that an extra manager layer should be the default. Scafforge should keep a single visible team leader by default and reserve manager or section-leader hierarchies for unusually large repos with clear non-overlapping domains.

### Post-migration verification

This is where Scafforge should lean in. GPS is useful because it aggressively recomputes truth from artifacts. GPTTalker is good at stage validation. Scafforge's stronger contract is to record process changes, set `pending_process_verification`, and re-check old completed work before it is trusted again.

### Guarded ticket creation

The best pattern is:

- verifier produces proof
- team leader judges the result
- a guarded tool creates the ticket

This prevents ad hoc ticket inflation and keeps a clear evidence trail.

### PR review to ticket generation

GPS shows the practical pattern: review findings become prioritized later work. Scafforge should formalize that as a host-side bridge that validates comments first and emits canonical ticket proposals unless the target repo exposes a safe direct intake path.

## Recommendations for Scafforge

1. Keep one visible team leader as the default.
2. Keep per-ticket flow strictly sequential.
3. Make lane ownership concrete in generated repos.
4. Preserve and strengthen process-migration verification.
5. Keep review-driven follow-up ticket creation guarded and evidence-backed.
6. Continue preferring blockers over assumption-making.
7. Keep workflow truth hierarchical and tool-backed.

## Bottom line

Scafforge should continue to be a structured workflow-agent scaffold optimized for reliable execution under tighter constraints. The internal reference repos reinforce strong ownership and sequential flow. Scafforge's differentiator should remain explicit process migration awareness plus verifier-backed follow-up ticket handling.
