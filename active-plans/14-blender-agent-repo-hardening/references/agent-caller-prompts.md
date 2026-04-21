# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the plan preserves honest tool-maturity labeling across certified, partial, preview, and experimental surfaces
- check that Linux/headless viability, QA/export proof, and packaging/client contracts are concrete
- confirm Scafforge is not being asked to rely on wider behavior than `blender-agent` can really prove

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the hardening work in the adjacent `blender-agent` repo around truthful public contracts, runtime safety, certified tool families, QA/export, and packaging
- keep v1/v2 maturity boundaries explicit and machine-readable
- ensure headless Blender support and client packaging claims are only as broad as the tests and docs actually prove

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- check for any mismatch between README claims, tool maturity tables, test coverage, and real server behavior
- verify headless/Linux and engine-export claims are supported with concrete validation evidence
- look for skill surfaces that promise more than the certified tool contracts can deliver

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: systemic honesty of the public contract, especially around maturity labels and unsupported paths.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: end-to-end coherence across server runtime, QA/export evidence, skills, and Scafforge integration expectations.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: concrete implementation holes in runtime safety, payload validation, tests, fixtures, export profiles, and CI coverage.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: documentation and contract consistency across the repo’s plans, status docs, and packaged-skill claims.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: practical asset-pipeline reliability, operator trust, and whether the repo can be used honestly by Scafforge without surprise failure modes.



