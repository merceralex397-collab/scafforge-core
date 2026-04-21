# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the matrix covers web, game, CLI/script, service, desktop, and Android families
- check that proof artifacts and stack-specific ladders are concrete
- confirm the plan is not Android-biased and still respects Linux/headless reality

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the validation matrix, tool bundles, proof artifact conventions, and audit/handoff integration
- preserve the cheapest-truthful-proof principle
- keep unsupported stacks explicit rather than silently skipped

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- look for missing stack families, vague proof requirements, or a return to smoke-test-only validation
- check that artifact handling is structured and not uncontrolled log dumping
- verify the implementation does not assume GUI access where headless validation should be primary

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: systemic validation blind spots, unhandled stack families, and failure to block incomplete proofs.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: ladder coherence, state transitions around proof artifacts, and lifecycle fit with audit/repair/handoff.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: script correctness, fixture coverage, and implementation gaps in adapter or validator wiring.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: architecture/documentation consistency and whether the resulting matrix is sustainable.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: practical operator value, clarity of required proofs, and whether teams could actually use the matrix day to day.



