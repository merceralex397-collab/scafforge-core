# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the WinUI app is defined as an observer/controller, not a second workflow engine
- check that packaging, WSL/SSH connectivity, secret handling, and operator override flows are explicit
- confirm the plan distinguishes Windows-local UI concerns from backend orchestration truth

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the WinUI boundary, backend API/event contract, secure settings model, and operator workflow map
- optimize early work for internal-tool local build/run loops before packaged distribution
- ensure the app can represent downstream repo state, package investigations, and provider/router state without ambiguity

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- check that the app does not invent or own workflow truth locally
- verify Windows-specific decisions do not leak into headless backend contracts unnecessarily
- look for security gaps around provider keys, SSH credentials, operator approvals, and logging

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: architecture and authority-boundary flaws, especially accidental backend duplication inside the UI app.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: cross-surface state coherence between orchestration services, event streams, and operator actions.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: connectivity, API client, event subscription, secure settings, and verification gaps in the changed files.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: contract and documentation alignment across WinUI, orchestration backend, and operator guidance.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: real operator usability, intervention flows, and whether the control plane would actually help during failures.



