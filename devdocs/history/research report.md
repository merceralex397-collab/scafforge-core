# Research Report: OpenCode Ecosystem Patterns Adaptable to Scafforge

## Executive Summary

Scafforge's current direction is strongly aligned with OpenCode's native architecture: project-local agents, commands, skills, plugins, custom tools, granular permissions, and MCP integration are all first-class capabilities, not hacks.[^1][^2][^3][^4][^5][^6][^7] The most important new finding is that the current upstream `anomalyco/opencode` repository appears to dogfood singular internal directories like `.opencode/agent`, `.opencode/command`, and `.opencode/tool`, while the public docs emphasize plural directories such as `.opencode/agents`, `.opencode/commands`, and `.opencode/tools`; Scafforge should therefore add a schema-watch and compatibility strategy instead of trusting one snapshot blindly.[^8][^9][^10][^11][^12] The ecosystem also contains several high-value patterns that map directly to the existing Scafforge roadmap: lazy skill loading, persistent background delegation, context pruning and compaction control, handoff/session continuity, worktree and sandbox isolation, packaged plugin bundles, cross-tool installer flows, and editor/event-driven clients.[^13][^14][^15][^16][^17][^18][^19][^20][^21] The strongest recommendation is to keep `OpenCode-only` output for v1, but enrich the plan with optional plugin packs and validation layers that make the output more resilient for weak-model autonomous execution.[^22]

## Scope and method

This research focused on ideas that can be specifically adapted into Scafforge rather than generic AI-agent trends. I combined: official OpenCode docs for agents, commands, permissions, MCP, config, plugins, skills, rules, and custom tools; upstream `opencode` repository contents; ecosystem catalogs; and representative community repos whose mechanisms could concretely inform Scafforge's roadmap.[^1][^2][^3][^4][^5][^6][^7][^8][^13][^19][^23] I treated Scafforge's current plan as the local baseline: host-agnostic generator, `OpenCode-only` output for v1, autonomous weak-model friendliness, deterministic state, explicit ambiguity handling, and stronger repair/audit behavior.[^22]

## 1. What OpenCode already provides natively, and why that matters for Scafforge

### 1.1 Agents are already designed as workflow roles, not just personalities

OpenCode natively distinguishes primary agents from subagents, ships built-in `build`, `plan`, `general`, and `explore` roles, supports custom markdown-defined agents, and lets each agent override model choice, tool access, permissions, and maximum reasoning steps.[^1] This is important for Scafforge because it means your generated repos do not need to simulate multi-role behavior purely with prose; they can encode planner, implementer, reviewer, QA, docs, and utility lanes as actual OpenCode agents with explicit capability boundaries.[^1][^22]

Two especially useful built-in features should be reflected more explicitly in the plan:

- `steps` can cap iterations before the agent is forced into a summary response, which means Scafforge should define when to leave steps unlimited versus when to set bounded lanes for cheap helper roles.[^1]
- Agent permissions can override global permissions, which supports your requirement to keep git/local repo operations safe but still enable lane-specific workflows.[^1][^4]

### 1.2 Commands are stronger than "slash command wrappers"

OpenCode commands can target a specific agent, force subtask mode, accept arguments, inject shell output via `!` command blocks, and inline file references with `@file` syntax.[^2] That makes commands suitable as deterministic workflow entrypoints for Scafforge-generated repos: `/kickoff`, `/plan-ticket`, `/qa-ticket`, `/resume`, and similar commands can package the exact state surfaces and context that weak models need, instead of depending on freeform prompting.[^2][^22]

This also supports a cleaner separation of concerns:

- commands initiate repeatable workflows,
- agents own reasoning and delegated work,
- plugins enforce guardrails,
- tools mutate or inspect structured state.[^2][^6][^7]

### 1.3 Permissions are fine-grained enough to encode process discipline

OpenCode permissions can be global or tool-specific, support wildcard matching, and include `external_directory` and `doom_loop` protections in addition to ordinary tools.[^4] The `doom_loop` permission is especially relevant to your weak-model concerns because it exists to catch the same tool call repeating with identical input, which is exactly the kind of autonomous failure pattern Scafforge is trying to guard against.[^4]

This maps directly into the plan:

- generated repos should explicitly configure `doom_loop`,
- generated repos should explicitly gate `external_directory`,
- local git permissions should be lane-specific,
- dangerous shell commands should be denied or escalated.[^4][^22]

### 1.4 MCP is powerful, but the docs explicitly warn about context blow-up

OpenCode's MCP docs warn that MCP servers add to context and that large servers such as GitHub MCP can easily exhaust the window, which is exactly why your v1 decision to keep generated repos at `local git read/write without GitHub` is sensible.[^5][^22] The docs also support enabling MCP globally but selectively turning MCP tools on only for certain agents, which suggests a strong Scafforge design rule: research-heavy or docs-heavy MCP should be enabled only for agents that truly need it.[^5]

That directly supports several roadmap refinements:

- keep GitHub automation out of the default v1 scaffold,
- create optional research or docs packs for heavyweight MCP,
- document context costs in generated runtime-model and tooling docs.[^5][^22]

### 1.5 Plugins and custom tools are the real workflow enforcement layer

OpenCode plugins can be loaded from local files or npm, auto-installed with Bun, and hooked into session, tool, shell, permission, message, TUI, and compaction-related events.[^6] Plugins can also register tools directly, and the docs expose both `tool.execute.before/after` hooks and `experimental.session.compacting` hooks.[^6] Custom tools support structured argument schemas, execution context, and arbitrary backing languages via TypeScript or JavaScript wrappers.[^7]

This is highly relevant to Scafforge because it validates your instinct that stronger rails should live in tools/plugins instead of prompt prose.[^22] Specifically, Scafforge should treat the following as first-class implementation targets:

- stage-gate enforcement plugins,
- structured artifact write/register tools,
- compaction-preserving plugins,
- secret/file safety plugins,
- provenance/logging plugins,
- packaged optional bundles distributed as npm plugins.[^6][^7][^22]

### 1.6 Rules, instructions, and config precedence support modularity

OpenCode supports project `AGENTS.md`, global rules, compatibility with Claude-style files, and additional instruction files listed from `opencode.json`, including remote URLs.[^8] Config merges remote organizational defaults, global config, custom config files, project config, `.opencode` directories, and inline env-based config.[^3] This reinforces a major Scafforge planning theme: keep the generator core, host adapters, and generated project output distinct.[^3][^8][^22]

It also creates a concrete packaging avenue for Scafforge host adapters:

- host-specific installation and invocation can live outside the generated repo,
- generated repos can remain OpenCode-shaped,
- shared guidance can live in reusable instruction files rather than monolithic `AGENTS.md` blocks.[^3][^8]

## 2. Upstream repository signals that should change Scafforge's conformance strategy

### 2.1 The upstream repo appears to dogfood singular `.opencode` subdirectories

The current `anomalyco/opencode` repository root exposes a project-local `.opencode` tree containing `.opencode/agent`, `.opencode/command`, `.opencode/tool`, `.opencode/glossary`, `.opencode/themes`, and `.opencode/opencode.jsonc`.[^9][^10][^11] That is notable because the public docs we reviewed consistently describe plural directories such as `.opencode/agents`, `.opencode/commands`, `.opencode/tools`, `.opencode/plugins`, and `.opencode/skills`.[^1][^2][^6][^12]

This does **not** mean the docs are wrong or that Scafforge should immediately switch to singular names. It means Scafforge needs an explicit **schema-watch and compatibility matrix**:

1. track official docs,
2. track upstream repo dogfooding,
3. validate generated output against the intended target version,
4. optionally support compatibility aliases or version-targeted output profiles later.[^3][^6][^22]

This is one of the strongest concrete new research findings.

### 2.2 Upstream uses task-specific agents, commands, and tools internally

The upstream repo includes a hidden primary `triage` agent that only enables a custom `github-triage` tool, plus command files such as a `commit` command that injects `git diff`, `git diff --cached`, and `git status --short` into the prompt template.[^10][^11][^24] The `github-triage` tool is defined as a typed custom tool implemented with `@opencode-ai/plugin`, with guardrails that validate labels, assignments, and issue text before mutating GitHub state.[^11]

This is directly adaptable to Scafforge:

- generated repos can include more domain-operational agents, not just generic roles,
- commands can preload the exact structured evidence needed for tasks,
- tools should validate workflow invariants instead of trusting prompts alone.[^2][^7][^11]

### 2.3 OpenCode's own architecture reinforces Scafforge's host/output separation

The current upstream README emphasizes provider agnosticism, client/server architecture, TUI focus, SDKs, desktop availability, and remote-control possibilities.[^23] The repo layout also contains packages for `plugin`, `sdk`, `extensions`, `desktop`, `web`, `console`, and `opencode` itself, and the `packages/extensions` tree includes at least a `zed` extension package.[^25][^26]

That matters for Scafforge because it suggests a long-term clean split:

- generated output should remain an OpenCode project operating layer,
- installation/distribution can become host-adapter and client-adapter work,
- the generated repo should stay decoupled from any one frontend or editor surface.[^23][^25][^26][^22]

## 3. High-signal ecosystem patterns that Scafforge can actually adapt

### 3.1 Lazy skill loading and skill registries

Two community approaches stand out:

- `opencode-agent-skills` discovers skills across project, user, and Claude-compatible directories, injects availability into context, survives compaction, and can auto-match likely skills semantically.[^13]
- `opencode-skillful` exposes explicit `skill_find`, `skill_use`, and `skill_resource` tools, supports on-demand loading, model-specific rendering formats, and resource/script access without loading every skill at once.[^14]

**Adaptation for Scafforge**

Scafforge should not default to huge skill libraries. But if a generated repo grows beyond a small foundation pack, Scafforge should consider:

- a compact skill inventory manifest,
- lazy-loading or resource-only access patterns,
- model-specific rendering guidance if weak models benefit from alternate skill prompt shapes,
- script/resource separation within local skills.[^13][^14][^22]

### 3.2 Persistent background delegation and long-session survivability

`opencode-background-agents` is especially relevant because it persists delegation results to disk explicitly to survive compaction and session churn.[^15] It also restricts background delegation to read-only agents because write-capable background work cannot be safely reconciled with OpenCode's undo/branching model.[^15]

That is a highly actionable design lesson for Scafforge:

- persistent background research is a good fit,
- persistent write-capable background implementation is dangerous,
- delegation results should be artifactized and retrievable,
- the plan should clearly separate read-only research delegation from code mutation lanes.[^15][^22]

### 3.3 Handoff that can recover detail, not just summary

`opencode-handoff` adds a `/handoff <goal>` command that creates a continuation prompt for a new session and pairs it with a `read_session` tool to recover transcript details if the summary leaves something out.[^16]

This supports two Scafforge amendments:

- generated handoff surfaces should capture more than a brief summary,
- restart flows should have a recoverable evidence path, not only a static markdown snapshot.[^16][^22]

### 3.4 Differential context pruning and custom compaction behavior

`opencode-dynamic-context-pruning` is one of the strongest ecosystem ideas for your weak-model and long-session concerns. It protects certain tools and file patterns, allows model-specific context thresholds, supports custom prompt overrides for compression behavior, and keeps summaries layered rather than simply dropping old content.[^17]

This maps very well to Scafforge:

- protect ticket state, artifact references, handoff outputs, and tool-backed approvals from pruning,
- make model-specific compaction thresholds part of the runtime-model profile,
- add explicit compaction prompts or plugin hooks for generated repos,
- treat compaction behavior as part of workflow design, not just OpenCode internals.[^6][^17][^22]

### 3.5 Bundle profiles and harness packaging

`opencode-workspace` packages orchestrators, specialist agents, plugins, MCP servers, skills, commands, and permissions into a single installable harness.[^18] The idea is not that Scafforge should copy this bundle wholesale. The important idea is **profile composition**.

**Adaptation for Scafforge**

Scafforge should formalize at least two levels of generated operating layer:

- **minimum deterministic profile** for smaller projects,
- **full orchestration profile** for larger or longer-running projects.[^18][^22]

This research strongly supports the interview-style amendment already added to your plan.

### 3.6 Worktree isolation and remote sandboxes

`opencode-worktree` creates isolated git worktrees that automatically launch OpenCode sessions, manage lifecycle hooks, and support tmux or native terminal spawning.[^19] The Daytona plugin goes further: it runs each session in a remote sandbox, syncs it to local git branches, and persists sandbox/session mapping in local state files.[^20]

**Adaptation for Scafforge**

These should be **optional isolation profiles**, not the default v1 behavior:

- local worktree isolation for high-risk or parallel development,
- remote sandbox isolation for teams or riskier autonomous execution,
- generated configuration files for worktree/sandbox sync rules,
- clear warnings around auto-commit or overwrite behavior.[^19][^20]

### 3.7 Packaged OpenCode bundles and plugin templates

`cursed-dropkit-template` shows a publishable npm-bundle approach for shipping agents, commands, and skills with a plugin factory and CI/build scripts.[^21] The OpenCode plugin docs also explicitly support npm plugins that are automatically installed and cached.[^6]

**Adaptation for Scafforge**

This is directly relevant to your packaging goal:

- package host adapters or optional workflow packs as installable plugins,
- keep the generated output OpenCode-only,
- avoid copying every optional feature into the generated repo by default,
- use bundle packaging for add-on packs like safety, observability, research, or isolation.[^6][^21][^22]

### 3.8 Cross-tool installer and sync patterns

`agent-config-sync` is not a direct template for Scafforge output because you have explicitly kept the output scope to OpenCode only.[^22] But it is still useful as a **distribution pattern**: it treats one tool's config as the source of truth and automates synchronization to OpenCode, Codex, Cursor, and Claude-compatible surfaces.[^27]

**Adaptation for Scafforge**

Use this idea only for Scafforge's **host adapter packaging**:

- packaged install UX for Copilot, Codex, and Gemini,
- external config dir strategies,
- clean separation between installer behavior and generated repo behavior.[^3][^27][^22]

### 3.9 External clients and event-driven integrations

`opencode.nvim` shows OpenCode being used as a server-backed service with prompt injection, editor context placeholders like `@diff` and `@diagnostics`, command execution, SSE event forwarding, edit review, and permission approval flows inside a client integration.[^28] This supports a subtle but important Scafforge principle:

Generated repos should not assume the only user experience is the built-in TUI. If the repo state model is clean enough, alternative clients, dashboards, or review shells can attach later without changing the repo's source-of-truth surfaces.[^23][^28]

### 3.10 Hooks, specialist packs, and "ask before implementing"

`opencode-froggy` is unusually close to several Scafforge concerns: it combines hooks, specialist agents, skills, tools, and a skill explicitly named `ask-questions-if-underspecified`.[^29] That is an ecosystem confirmation that your "never assume on meaningful ambiguity" rule is not just a niche preference; it is already emerging as a reusable workflow primitive.[^22][^29]

**Adaptation for Scafforge**

Make ambiguity handling a packaged, enforceable workflow surface:

- a normalization policy,
- a local skill,
- maybe a plugin reminder or guard,
- and batched decision interview packets rather than ad hoc questioning.[^22][^29]

## 4. Ecosystem catalog signals worth tracking, but not auto-importing

The official ecosystem page and `awesome-opencode` catalog show several recurring plugin categories:

- agent identity and attribution,
- persistent memory,
- background agents,
- devcontainer isolation,
- dynamic context pruning,
- `.env` / secret protection,
- notifications,
- safety nets for destructive commands,
- token/context analysis,
- handoff tooling,
- worktree tooling,
- web/code research augmentations,
- auth/provider plugins,
- multi-agent agent packs and workflow bundles.[^30][^31]

These should **not** become automatic imports into generated repos. But they are perfect inputs for Scafforge's curated pattern catalog:

1. evaluate pattern,
2. extract the reusable behavior,
3. adapt it into repo-specific instructions/tools/plugins,
4. validate it against Scafforge's own workflow contract.[^22][^30][^31]

## 5. Concrete amendments to the Scafforge plan

Below are the strongest plan changes suggested by this research.

### 5.1 Add a schema-watch and compatibility lane

Scafforge should continuously compare:

- official docs,
- upstream repo dogfooding,
- generated template shape,
- live fixture repos.[^1][^2][^6][^8][^9][^10][^11][^12]

This is the right response to the singular/plural directory drift signal.

### 5.2 Add optional plugin-packaged profiles

Instead of forcing every capability into the base scaffold, Scafforge should define optional packs such as:

- research/delegation pack,
- safety pack,
- observability pack,
- isolation pack,
- advanced context-management pack.[^6][^15][^17][^19][^21][^30]

### 5.3 Add compaction-preservation design explicitly

The current plan already calls for stronger artifacts and handoff surfaces. This research says the plan should go further and explicitly define:

- protected tool outputs,
- protected files,
- compaction hooks or prompts,
- model-specific context thresholds,
- research/result persistence across compaction.[^6][^15][^17]

### 5.4 Add a scaffold inventory manifest and provenance registry

This complements the plan's existing provenance direction. The ecosystem evidence suggests Scafforge should make it easy for agents to know:

- what exists,
- why it exists,
- where it came from,
- whether it is generated, synthesized, or repaired later.[^13][^18][^21][^29]

### 5.5 Keep output OpenCode-only, but make installers/adapters package-grade

Your decision to keep output scope fixed is validated by the ecosystem evidence. The main packaging opportunity is **not** multi-output repos; it is packaged installation and adapter UX for multiple host CLIs.[^3][^6][^21][^27][^22]

### 5.6 Add optional isolation strategies, not mandatory ones

Worktrees and sandboxes are clearly useful, but they should be opt-in profiles. For many Scafforge-generated repos, the default flow should remain simpler and lighter.[^19][^20][^22]

### 5.7 Treat ecosystem discoveries as pattern inputs, not dependencies

This is perhaps the most important policy conclusion: the ecosystem is rich enough to inspire Scafforge, but importing it wholesale would create exactly the kind of skill sprawl and drift your roadmap is trying to avoid.[^18][^29][^30][^31][^22]

## 6. Ideas to explicitly approach with caution

### 6.1 Do not enable heavyweight MCP by default

OpenCode itself warns that MCP can explode context, especially with servers like GitHub MCP.[^5] This validates your current v1 boundary.

### 6.2 Do not default to write-capable background delegation

The background-agents plugin explicitly limits persistent background work to read-only agents because writes performed outside the normal session tree are hard to reconcile safely.[^15]

### 6.3 Do not let lazy skill loading become an excuse for huge skill packs

Lazy-loading plugins solve token usage, but they do not solve conceptual sprawl. Scafforge should still keep local skill packs small and evidence-based.[^13][^14][^22]

### 6.4 Do not make worktree auto-commit the default lifecycle

The worktree plugin's automated cleanup is powerful, but it is risky as a baseline. Scafforge should treat this as an advanced isolation option, not the default behavior.[^19]

## Key repositories summary

| Repository | What it contributes | Best adaptation for Scafforge |
| --- | --- | --- |
| [anomalyco/opencode](https://github.com/anomalyco/opencode) | Upstream architecture, packaged plugin SDK, dogfooded local agents/commands/tools | Schema-watch, packaged optional packs, stronger custom tool contracts |
| [joshuadavidthomas/opencode-agent-skills](https://github.com/joshuadavidthomas/opencode-agent-skills) | Dynamic skill discovery/injection, compaction-resilient skill availability | Lazy skill inventory and compaction-safe skill registry |
| [zenobi-us/opencode-skillful](https://github.com/zenobi-us/opencode-skillful) | On-demand skill find/use/resource model | Resource-first local skill design for larger repos |
| [kdcokenny/opencode-background-agents](https://github.com/kdcokenny/opencode-background-agents) | Persistent async delegation | Read-only research delegation artifacts |
| [joshuadavidthomas/opencode-handoff](https://github.com/joshuadavidthomas/opencode-handoff) | Session handoff with transcript recovery | Richer restart surfaces and recoverable handoff evidence |
| [Tarquinen/opencode-dynamic-context-pruning](https://github.com/Tarquinen/opencode-dynamic-context-pruning) | Protected compaction, prompt overrides, pruning strategies | Compaction-preservation and context budget profiles |
| [kdcokenny/opencode-workspace](https://github.com/kdcokenny/opencode-workspace) | Profile/bundle harness concept | Minimum-vs-full generated repo profiles |
| [kdcokenny/opencode-worktree](https://github.com/kdcokenny/opencode-worktree) | Worktree isolation | Optional local isolation profile |
| [daytonaio/daytona](https://github.com/daytonaio/daytona/tree/main/libs/opencode-plugin) | Remote sandbox sessions synced to git | Optional sandbox profile for safer autonomy |
| [CursedFactory/cursed-dropkit-template](https://github.com/CursedFactory/cursed-dropkit-template) | Packaged distribution of OpenCode content | Npm-packaged host adapters and add-on packs |
| [liamdmcgarrigle/agent-config-sync](https://github.com/liamdmcgarrigle/agent-config-sync) | Cross-tool installer/sync pattern | Host adapter packaging only, not output expansion |
| [nickjvandyke/opencode.nvim](https://github.com/nickjvandyke/opencode.nvim) | Server/event/editor integration | Keep generated repo state model client-agnostic |
| [smartfrog/opencode-froggy](https://github.com/smartfrog/opencode-froggy) | Hooks, specialist agents, ask-before-implementing skill | Packaged ambiguity-handling and hook-driven policy |

## Confidence Assessment

**High confidence**

- OpenCode's native feature surface is directly compatible with the current Scafforge direction around local agents, commands, tools, plugins, skills, and deterministic workflow enforcement.[^1][^2][^4][^6][^7][^8]
- The ecosystem clearly supports the plugin-pack, background delegation, handoff, pruning, worktree, and bundle concepts described above.[^15][^16][^17][^18][^19][^20][^21][^28][^29][^30][^31]
- Keeping the output scope OpenCode-only for v1 remains the right boundary.[^22]

**Medium confidence**

- The singular-vs-plural directory divergence is real enough to justify a schema-watch lane, but I cannot conclusively say from this research alone whether upstream is transitioning formats, supporting both, or dogfooding a special internal layout.[^1][^2][^6][^9][^10][^11][^12]
- Optional isolation profiles (worktrees/sandboxes) look highly promising, but their ergonomics and safety depend on the generated repo stack and the team's risk tolerance.[^19][^20]

**Inferred / design judgment**

- The strongest adaptations are architectural and packaging-oriented, not direct ecosystem imports. That conclusion is based on both the richness of the ecosystem and Scafforge's own requirement to remain disciplined, deterministic, and weak-model-friendly.[^22][^30][^31]

## Footnotes

[^1]: [OpenCode docs: Agents](https://opencode.ai/docs/agents/) — built-in agent types, custom agent config, `steps`, per-agent permissions, and agent roles.
[^2]: [OpenCode docs: Commands](https://opencode.ai/docs/commands/) — command templates, `$ARGUMENTS`, `!` shell-output injection, `@file` inclusion, `agent`, `subtask`, and `model` options.
[^3]: [OpenCode docs: Config](https://opencode.ai/docs/config) — config precedence, `OPENCODE_CONFIG_DIR`, project/global config, and merged configuration model.
[^4]: [OpenCode docs: Permissions](https://opencode.ai/docs/permissions/) — wildcard matching, per-agent overrides, `external_directory`, and `doom_loop`.
[^5]: [OpenCode docs: MCP servers](https://opencode.ai/docs/mcp-servers/) — MCP context caveat, local/remote MCP configuration, and per-agent MCP enable/disable patterns.
[^6]: [OpenCode docs: Plugins](https://opencode.ai/docs/plugins/) — npm/local plugin loading, hook/event surfaces, `experimental.session.compacting`, and plugin-added custom tools.
[^7]: [OpenCode docs: Custom tools](https://opencode.ai/docs/custom-tools/) — tool definition model, `tool()` helper, Zod schemas, and execution context.
[^8]: [OpenCode docs: Rules](https://opencode.ai/docs/rules/) — `AGENTS.md`, Claude compatibility, instruction files, and file-loading guidance.
[^9]: [anomalyco/opencode](https://github.com/anomalyco/opencode) `.opencode` directory listing (dev branch `0befa1e57e2b5ec2cd7b0fcfce7e572866393154`) — contains `.opencode/agent`, `.opencode/command`, `.opencode/tool`, `.opencode/glossary`, `.opencode/themes`, and `.opencode/opencode.jsonc`.
[^10]: [anomalyco/opencode](https://github.com/anomalyco/opencode) `.opencode/opencode.jsonc` (SHA `8380f7f719ef676b3480762274e4f57de21beece`), `.opencode/agent/triage.md` (SHA `a77b92737bc9e3a8dbbf9ffd6dd4fb0e822b72f8`), and `.opencode/command/commit.md` (SHA `e88932a24485ea8e4ef5b22dbb3306039e48cefb`).
[^11]: [anomalyco/opencode](https://github.com/anomalyco/opencode) `.opencode/tool/github-triage.ts` (SHA `ed80f49d541372a2d4dfbfdb49955641bb261120`) and `.opencode/agent/triage.md` (SHA `a77b92737bc9e3a8dbbf9ffd6dd4fb0e822b72f8`) — typed operational tool plus constrained issue-triage agent.
[^12]: Official docs use plural project directories for skills and plugins — see [OpenCode docs: Skills](https://opencode.ai/docs/skills/) and [OpenCode docs: Plugins](https://opencode.ai/docs/plugins/).
[^13]: [joshuadavidthomas/opencode-agent-skills](https://github.com/joshuadavidthomas/opencode-agent-skills) `README.md` (SHA `107d53b12cde50236cbf68c3e1f9d2049be7f160`) — dynamic discovery, compaction resilience, semantic matching, and skill availability injection.
[^14]: [zenobi-us/opencode-skillful](https://github.com/zenobi-us/opencode-skillful) `README.md` (SHA `682bbb85e34dc4a49977e99555fe82e6fe49a844`) — `skill_find`, `skill_use`, `skill_resource`, lazy loading, model-specific rendering, and resource/script access.
[^15]: [kdcokenny/opencode-background-agents](https://github.com/kdcokenny/opencode-background-agents) `README.md` (SHA `bc65ccb14a9d7501c8be339b514737fc679e0655`) — persistent background delegation, markdown results, and read-only-only delegation constraint.
[^16]: [joshuadavidthomas/opencode-handoff](https://github.com/joshuadavidthomas/opencode-handoff) `README.md` (SHA `9dae65d2ba2e6682e489b80670b4ed6ebe87f27e`) — `/handoff`, continuation prompts, and `read_session` transcript recovery.
[^17]: [Tarquinen/opencode-dynamic-context-pruning](https://github.com/Tarquinen/opencode-dynamic-context-pruning) `README.md` (SHA `0d2f0f7abb225f88a6f7221d724bbc95a3a1f388`) — compression tool, protected tools/file patterns, model-specific thresholds, and custom prompt overrides.
[^18]: [kdcokenny/opencode-workspace](https://github.com/kdcokenny/opencode-workspace) `README.md` (SHA `b854c5924ab8316fdf45c5f1cd16bba54d133bdb`) — bundle profile with orchestrators, specialists, plugins, MCP, commands, and skills.
[^19]: [kdcokenny/opencode-worktree](https://github.com/kdcokenny/opencode-worktree) `README.md` (SHA `8b52f74ccc193c8c536df72863f37644ad4d6953`) — worktree creation/deletion tools, terminal spawning, lifecycle hooks, and isolation behavior.
[^20]: [daytonaio/daytona](https://github.com/daytonaio/daytona/tree/main/libs/opencode-plugin) `libs/opencode-plugin/README.md` (SHA `ae5b483de3af70048a02b984c482dea6efd5a5d0`) — remote session sandboxing, git synchronization, and session-to-sandbox mapping.
[^21]: [CursedFactory/cursed-dropkit-template](https://github.com/CursedFactory/cursed-dropkit-template) `README.md` (SHA `9dd5df374af519f78edbe8759490f6f461431874`) — npm-publishable dropkit packaging for agents, commands, and skills.
[^22]: `C:\Users\rowan\.copilot\session-state\14195f39-6d50-4744-a11a-30398325e0d9\plan.md:11-25`, `140-150`, `430-447`, `571-618`, `702-721` — current Scafforge plan framing host-agnostic generation, OpenCode-only v1 output, local git-only default, packaged adapters, and repair-oriented roadmap.
[^23]: [anomalyco/opencode](https://github.com/anomalyco/opencode) `README.md` (SHA `79ccf8b3491003ae0b20f8c10da185b45c280e1d`) — provider agnosticism, client/server architecture, SDKs, and installation/distribution model.
[^24]: [anomalyco/opencode](https://github.com/anomalyco/opencode) `.opencode/command/commit.md` (SHA `e88932a24485ea8e4ef5b22dbb3306039e48cefb`) — command template that injects `git diff`, `git diff --cached`, and `git status --short` into the prompt.
[^25]: [anomalyco/opencode](https://github.com/anomalyco/opencode) `packages/` directory listing (dev branch `0befa1e57e2b5ec2cd7b0fcfce7e572866393154`) — includes `plugin`, `sdk`, `extensions`, `desktop`, `web`, `console`, and `opencode` packages.
[^26]: [anomalyco/opencode](https://github.com/anomalyco/opencode) `packages/extensions/` directory listing (dev branch `0befa1e57e2b5ec2cd7b0fcfce7e572866393154`) — includes at least a `zed` extension package.
[^27]: [liamdmcgarrigle/agent-config-sync](https://github.com/liamdmcgarrigle/agent-config-sync) `README.md` (SHA `a1e79eccdbf8c9e856900a7f07c0a5c4254690a4`) — cross-tool sync pattern for skills, MCP, hooks, and config distribution.
[^28]: [nickjvandyke/opencode.nvim](https://github.com/nickjvandyke/opencode.nvim) `README.md` (SHA `e4775992e556ecade464e8efe8d9a32edfca1dd8`) — editor contexts, server usage, commands, SSE event handling, and diff-based edit approval.
[^29]: [smartfrog/opencode-froggy](https://github.com/smartfrog/opencode-froggy) `README.md`, locally inspected at `C:\Users\rowan\AppData\Local\Temp\1773523797392-copilot-tool-output-98jq77.txt:10-220` — hooks, specialist agents, skills such as `ask-questions-if-underspecified`, and discovery locations.
[^30]: [OpenCode docs: Ecosystem](https://opencode.ai/docs/ecosystem/) — community plugins and projects including background agents, dynamic pruning, worktree/workspace tools, skillful loading, auth plugins, and editor/desktop/web clients.
[^31]: `C:\Users\rowan\AppData\Local\Temp\1773523726919-copilot-tool-output-kdsyxx.txt:40-220` — rendered contents of [awesome-opencode/awesome-opencode](https://github.com/awesome-opencode/awesome-opencode) `README.md` (SHA `9ac8a315932629a0ff49dfacf159b2f8b3b95d1d`), showing plugin categories such as identity, memory, background agents, safety nets, context analysis, devcontainers, env protection, hooks, notifications, and handoff tooling.
