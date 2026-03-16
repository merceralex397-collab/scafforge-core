# OpenCode ecosystem research for Scafforge

## Executive Summary

The OpenCode ecosystem is real, but the highest-signal artifacts are not giant forks; they are the official repo itself, a curated index of ecosystem projects, and a set of thin plugins that solve one concrete problem well.[^2][^3] The most reusable patterns for Scafforge are: repo-local extension surfaces that the official project already dogfoods, dynamic skill loading with compaction resilience, persisted read-only delegation, and guardrail plugins that narrow dangerous file access without disabling useful workflows.[^2][^4][^5][^6]

The strongest non-core wrapper is OpenWork, which treats OpenCode as an engine inside a larger host/product layer with local/remote modes, sidecars, plugin management, and skill distribution.[^7] That is useful as host-adapter inspiration, but it should remain outside Scafforge's default generated-repo contract.[^1][^7]

Provider/auth plugins and safety-stripped forks also exist, but they are not good default imports. The Antigravity auth plugin is technically substantial and worth studying as an example of a serious provider extension, while `evil-opencode` is mainly a cautionary example showing how easy it is for forks to remove safety boundaries rather than improve workflow quality.[^8][^9]

Overall, the public ecosystem mostly confirms the direction already in `/home/a/Scafforge/devdocs/research-opencode-ecosystem.md`: use the ecosystem as a pattern source, keep the generated scaffold deterministic and OpenCode-native, and make advanced integrations opt-in instead of default.[^1]

## Architecture / ecosystem overview

```text
                         ┌──────────────────────────┐
                         │  anomalyco/opencode      │
                         │  official core surfaces  │
                         │  agents / commands /     │
                         │  tools / repo config     │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
          ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐
          │ curated index  │  │ thin plugins   │  │ host wrappers   │
          │ awesome-       │  │ skills / bg    │  │ OpenWork        │
          │ opencode       │  │ env guard /    │  │ orchestrator    │
          │                │  │ provider auth  │  │                 │
          └────────────────┘  └────────────────┘  └─────────────────┘
                    │                 │                 │
                    └────────────┬────┴──────┬──────────┘
                                 │           │
                                 ▼           ▼
                        patterns Scafforge can adapt
                     (repo-local contracts, bounded
                      delegation, safety plugins,
                      optional profile packs)
```

The official repo is the center of gravity because it proves which extension surfaces are first-class in practice: repo-local `.opencode` config, repo-local agents, repo-local commands, and repo-local tools.[^2] The broader ecosystem then branches into three usable layers: a discovery/catalog layer (`awesome-opencode`), a thin-plugin layer (skills, delegation, env safety, provider auth), and a host-wrapper layer (`openwork`) that sits above the CLI and turns it into a productized multi-client runtime.[^3][^4][^5][^6][^7][^8]

## Key repositories summary

| Repository | Type | Why it matters | Scafforge verdict |
|---|---|---|---|
| [anomalyco/opencode](https://github.com/anomalyco/opencode) | Official core | Dogfoods repo-local agents, commands, tools, and per-repo permissions.[^2] | Treat as the primary contract source. |
| [awesome-opencode/awesome-opencode](https://github.com/awesome-opencode/awesome-opencode) | Curated index | Best public map of current plugins, agents, themes, and official SDK repos.[^3] | Use as a discovery surface, not an install list. |
| [joshuadavidthomas/opencode-agent-skills](https://github.com/joshuadavidthomas/opencode-agent-skills) | Plugin | Shows dynamic skill discovery, synthetic skill injection, and compaction resilience.[^4] | High-value pattern source. |
| [kdcokenny/opencode-background-agents](https://github.com/kdcokenny/opencode-background-agents) | Plugin | Persists read-only delegation results and enforces read-only vs write-capable boundaries.[^5] | Adapt carefully as an optional profile. |
| [boxpositron/envsitter-guard](https://github.com/boxpositron/envsitter-guard) | Plugin | Strong example of security-first tool interception plus safer replacement tools.[^6] | Strong candidate for an optional safety pack. |
| [different-ai/openwork](https://github.com/different-ai/openwork) | Wrapper / host | Shows how OpenCode can sit under a desktop/server/client product with plugin and skill management.[^7] | Valuable host-layer inspiration, not a generated default. |
| [NoeFabris/opencode-antigravity-auth](https://github.com/NoeFabris/opencode-antigravity-auth) | Provider/auth plugin | Demonstrates that provider plugins can be deep policy-bearing integrations, not just config snippets.[^8] | Study for adapter patterns; keep out of core defaults. |
| [winmin/evil-opencode](https://github.com/winmin/evil-opencode) | Fork | Shows a fork whose main differentiator is removing safety guardrails.[^9] | Avoid; useful only as a warning sign. |

## 1. The official repo is already the best proof of the extension model

The single most useful finding is that OpenCode's own repo already uses the same extension surfaces Scafforge wants to generate. Its repo-local `.opencode/opencode.jsonc` applies permission policy, disables specific tools by default, and keeps configuration local to the project.[^2] That means Scafforge is not inventing an exotic workflow layer; it is leaning into the product's own intended customization model.[^2]

The official repo also includes repo-local agents and tools wired together in a very explicit way. The hidden `triage` agent is declared as a primary agent, has all tools disabled except `github-triage`, and states that its file is the source of truth for routing rules; the paired `github-triage.ts` tool then enforces deterministic assignee/label rules in code.[^2] For Scafforge, that is strong evidence that "prompt file + narrow tool + config gate" is a healthy pattern for generated specialists.[^2]

The official `learn` command is also highly relevant to Scafforge's restart-surface goals. It tells the agent to extract non-obvious learnings from a session into the nearest relevant `AGENTS.md`, explicitly distinguishing durable codebase knowledge from obvious docs or one-off session details.[^2] That maps neatly onto Scafforge's truth hierarchy: facts should land in durable repo surfaces instead of being left inside ephemeral chat context.[^1][^2]

## 2. `awesome-opencode` is the best current public ecosystem map

The `awesome-opencode` catalog is useful less as authority and more as a high-quality radar screen. It explicitly organizes the ecosystem into official repos, plugins, themes, agents, projects, and resources, and it lists the official JS, Go, and Python SDK repos alongside community projects.[^3] For Scafforge, this is the most efficient place to discover what kinds of extension points the community is actually using.[^3]

The plugin entries are especially informative because they reveal the current shape of real-world demand. The catalog highlights plugins for agent identity, agent memory, dynamic skills, Antigravity auth, background processes, background agents, devcontainers, direnv loading, dynamic context pruning, env protection, hooks/specialized agents, and session handoff.[^3] That is a stronger signal than raw search results because it groups the ecosystem by operational job rather than by repo name.[^3]

The most promising secondary leads from the curated list are:

- `opencode-devcontainers`, because it frames isolated multi-branch dev environments as an OpenCode plugin concern rather than a separate platform.[^3]
- `opencode-dynamic-context-pruning`, because token hygiene and context trimming are directly relevant to long-running generated workflows.[^3]
- `opencode-froggy`, because it emphasizes hooks and specialized agents, which overlaps with Scafforge's orchestration and guardrail interests.[^3]
- `opencode-handoff`, because handoff continuity is already part of Scafforge's `handoff-brief` spine.[^1][^3]

I did not independently audit those four repos in this pass, so they should be treated as follow-up leads rather than confirmed recommendations.[^3]

## 3. High-signal plugin patterns

### 3.1 Dynamic skill loading is a real extension pattern, not just a docs concept

`opencode-agent-skills` is one of the strongest pattern sources because it turns skills into a live discovery system rather than a static folder. The plugin advertises dynamic discovery across project, user, and Claude-compatible locations, loads skill content directly into context, survives compaction, and optionally integrates with Superpowers.[^4] More importantly, the implementation is opinionated about precedence: project OpenCode skills win before Claude project skills, then user OpenCode skills, then user Claude skills, then cached or marketplace Claude plugin skills.[^4]

That ordering is directly useful for Scafforge. If Scafforge ever wants compatibility with external skill ecosystems, this repo shows a sane override model: project-local procedural truth should win over global convenience packs.[^1][^4] It also shows a good compaction strategy: inject a compact available-skills list on session start and again after session compaction, then use synthetic messages to keep the discovery surface available without polluting user-visible chat.[^4]

The caution is equally important: this plugin is optimized for dynamic skill pickup across multiple homes, including Claude plugin caches and marketplaces.[^4] Scafforge should probably borrow the precedence and compaction ideas, but not the "discover everything on the machine" default; the rough guide is right to resist broad automatic imports.[^1][^4]

### 3.2 Persisted background delegation is valuable when it stays read-only

`opencode-background-agents` is the clearest example of a bounded background-task pattern. Its source says it replaces the native `task` tool with persistent, async-first delegation and persists outputs to storage; the implementation generates readable IDs, checks whether the target agent is truly read-only, refuses write-capable agents, writes results to markdown files, and injects delegation rules into the system prompt.[^5] The README makes the same design intent explicit: keep working, survive compaction, retrieve results later, and restrict delegation to read-only agents because write-capable background work would break undo/branching assumptions.[^5]

This is a very good match for Scafforge's weaker-model-first design. An optional "background research / audit" pack that is strictly read-only, artifact-backed, and clearly separated from write-capable implementation work would reinforce determinism rather than weaken it.[^1][^5] The key is to preserve the plugin's discipline: read-only only, explicit retrieval surfaces, durable artifacts, and no hidden write activity.[^5]

It is also notable that this plugin is explicitly based on `oh-my-opencode` ideas while being much thinner and more focused.[^5] That is a useful lesson for Scafforge: when mining the ecosystem, prefer distilled mechanism plugins over giant workflow harnesses unless you are intentionally building a host-layer product.[^5]

### 3.3 `envsitter-guard` is a model security plugin for generated repos

`envsitter-guard` is probably the best directly adaptable safety plugin in the set I inspected. Its source distinguishes `.env.example` from sensitive `.env*` files, blocks access to `.envsitter/pepper`, constrains its own tools to `.env`-style files inside the project, and intercepts standard `read`, `edit`, `write`, `patch`, and `multiedit` calls on sensitive paths.[^6] The replacement tools are deliberately shaped to avoid value leakage: keys, fingerprints, booleans, validation issues, copy plans, and mutation plans instead of raw secret contents.[^6]

This is exactly the kind of plugin pattern that Scafforge can package safely. It is narrow, auditable, npm-packaged in a conventional way, and explicit about local plugin-file installation for project scope via `.opencode/plugin/` plus `.opencode/package.json` dependencies.[^6] That makes it a good model for Scafforge-generated optional security profiles: protect secrets by redirecting dangerous generic tools into specialized safe tools instead of simply denying all access.[^6]

The bigger design lesson is that OpenCode plugins can enforce workflow boundaries at tool-hook level, not just through prose. That aligns with the rough guide's emphasis on "plugins and custom tools are the correct place for guardrails, synchronization, and enforcement logic."[^1][^6]

## 4. The wrapper / host layer is real, but it is a different layer than generated repo output

`openwork` is the clearest example I found of a host-layer product built around OpenCode rather than a plugin inside OpenCode. Its README describes a local-first, cloud-ready wrapper with host mode, client mode, SSE event streaming, templates, permissions handling, and a skill manager that can list local `.opencode/skills`, install from OpenPackage, or import local skill folders.[^7] It also says OpenCode plugins are the native extension mechanism and that OpenWork manages them by reading and writing `opencode.json` in either project or global scope.[^7]

The orchestrator README pushes that further: `openwork` can download and manage sidecars, run in detached or sandboxed modes, expose health checks, run a multi-workspace router daemon, and print connection details for remote clients.[^7] In other words, OpenWork treats OpenCode as a composable engine inside a broader runtime product.[^7]

For Scafforge, this is valuable mainly as a boundary reminder. The rough guide says not to collapse host and output layers together, and OpenWork proves why that distinction matters.[^1][^7] Its ideas are excellent if Scafforge ever grows host adapters or bootstrap flows, but they are too heavy to leak into the default generated repo contract.[^1][^7]

## 5. Provider/auth plugins exist, but they are usually policy-heavy

`opencode-antigravity-auth` is useful research material because it is much more than a one-line auth tweak. Its README describes Google OAuth login, multi-account rotation, dual Antigravity/Gemini quota routing, thinking-model variants, Google Search grounding, and auto-recovery behavior.[^8] Its package manifest shows a normal OpenCode plugin package with explicit dependencies on `@opencode-ai/plugin`, `@openauthjs/openauth`, `proper-lockfile`, `xdg-basedir`, and `zod`, which is a good reminder that serious provider integrations quickly become substantial software modules.[^8]

The source constants file reinforces that point. It contains provider endpoint sets, OAuth-related constants, additional system instructions for tool-use hardening, and a Google Search system instruction, all inside the plugin package itself.[^8] The takeaway for Scafforge is not "ship this"; it is "treat provider/auth integrations as adapters with their own policy surface, tests, and risk profile."[^8]

This repo also comes with an explicit terms-of-service warning in its README.[^8] That matters because it is the opposite of what should land in Scafforge defaults: a generated operating framework should stay broadly safe and policy-neutral, while risky provider workarounds remain explicit opt-in add-ons.[^1][^8]

## 6. Forks are not where the best ideas are

The most visible fork pattern I inspected was `evil-opencode`, and it is instructive mostly as a red flag. Its README says the project automatically rebuilds upstream OpenCode binaries after removing safety guardrails from prompt files and inserting an unrestricted instruction in their place.[^9] That may make it interesting as ecosystem evidence, but it is not a workflow or architecture improvement for Scafforge.[^9]

The practical lesson is that "fork exists" is weak evidence. Thin plugins and wrappers tend to contain the reusable ideas; forks often contain either local experiments or deliberate policy changes that should stay far away from a default scaffold.[^5][^6][^9]

## What Scafforge should adapt

### Adopt now

1. **Lean harder into repo-local `.opencode` surfaces.** The official repo already validates repo-local config, tools, agents, and commands as first-class extension points.[^2]

2. **Add an optional safety profile pack built around plugin-backed enforcement.** `envsitter-guard` is a strong model for "deny generic access, provide safer specialized tools instead."[^6]

3. **Keep knowledge capture close to code.** The official `learn` command's "write non-obvious facts into the nearest `AGENTS.md`" pattern is directly compatible with Scafforge's durable-truth model.[^2]

### Adapt carefully

4. **Offer read-only background research as an optional pack, not a core default.** The background-agents plugin is valuable specifically because it is read-only, persisted, and explicit about retrieval.[^5]

5. **Borrow dynamic skill precedence rules, not broad skill auto-import.** `opencode-agent-skills` has a useful override order and compaction strategy, but its wide discovery surface is too permissive for Scafforge defaults.[^1][^4]

6. **Treat host wrappers like OpenWork as adapter inspiration, not output-layer scaffold content.** The wrapper/sidecar/orchestrator model belongs above the generated repo, not inside it.[^1][^7]

### Keep opt-in or avoid

7. **Keep provider/auth plugins out of the default scaffold.** Antigravity auth is a real integration, but it is large, provider-specific, and carries explicit policy risk.[^8]

8. **Do not auto-import public ecosystem plugins from discovery alone.** The curated list is a radar screen, not permission to install dozens of community extensions.[^1][^3]

9. **Avoid safety-stripped forks entirely.** They are evidence of ecosystem activity, not trustworthy building blocks.[^9]

## Bottom line

The OpenCode ecosystem is most useful to Scafforge as a library of narrow, concrete patterns: repo-local contract surfaces from the official project, skill-loading patterns from `opencode-agent-skills`, persisted read-only delegation from `opencode-background-agents`, safety tooling from `envsitter-guard`, and host-layer separation lessons from `openwork`.[^2][^4][^5][^6][^7] That supports the rough guide almost exactly: sharpen project-specific customization, keep the baseline small, and expose advanced capability through optional profile packs instead of broad default imports.[^1]

## Confidence Assessment

**High confidence:** The official repo's extension model, the existence and purpose of the curated index, the mechanics of dynamic skill loading, the read-only design of background delegation, the hook-based secret-protection pattern, the host-wrapper nature of OpenWork, and the risk posture of the Antigravity and `evil-opencode` repos are all directly supported by repo files I inspected.[^2][^3][^4][^5][^6][^7][^8][^9]

**Medium confidence:** The broader ecosystem appears to be moving toward more wrappers, registries, and optional plugin packs, but I did not exhaustively audit every repo listed in `awesome-opencode` or every OpenCode fork. Where I mention secondary leads such as devcontainers, context pruning, Froggy, or handoff plugins, I am relying on the curated index descriptions rather than direct source review.[^3]

**Main uncertainty:** Ecosystem churn is high. Several community projects are young, and the public repo landscape changes quickly, so Scafforge should re-run this scan before locking in any default extension pack or external distribution integration.[^3][^7][^8]

## Footnotes

[^1]: `/home/a/Scafforge/devdocs/research-opencode-ecosystem.md:74-101`.

[^2]: [anomalyco/opencode](https://github.com/anomalyco/opencode), `.opencode/opencode.jsonc:1-14`; `.opencode/agent/triage.md:1-15`; `.opencode/tool/github-triage.ts:1-36, 44-98`; `.opencode/command/learn.md:1-31`.

[^3]: [awesome-opencode/awesome-opencode](https://github.com/awesome-opencode/awesome-opencode), `README.md:21-45, 49-177, 181-213`.

[^4]: [joshuadavidthomas/opencode-agent-skills](https://github.com/joshuadavidthomas/opencode-agent-skills), `README.md:1-137`; `src/plugin.ts:1-122`; `src/skills.ts:1-241`.

[^5]: [kdcokenny/opencode-background-agents](https://github.com/kdcokenny/opencode-background-agents), `README.md:1-75`; `src/plugin/background-agents.ts:1-9, 170-189, 275-301, 374-419, 645-669, 1237-1285`.

[^6]: [boxpositron/envsitter-guard](https://github.com/boxpositron/envsitter-guard), `README.md:1-287`; `index.ts:20-33, 99-121, 139-182, 891-912`; `package.json:1-40`.

[^7]: [different-ai/openwork](https://github.com/different-ai/openwork), `README.md:1-140`; `packages/orchestrator/README.md:1-185`.

[^8]: [NoeFabris/opencode-antigravity-auth](https://github.com/NoeFabris/opencode-antigravity-auth), `README.md:1-220`; `package.json:1-59`; `src/constants.ts:1-25, 150-215`.

[^9]: [winmin/evil-opencode](https://github.com/winmin/evil-opencode), `README.md:1-109`.
