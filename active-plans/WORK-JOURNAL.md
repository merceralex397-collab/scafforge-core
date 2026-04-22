# Active Plans Work Journal

## 2026-04-21

### Entry 1: Scope lock

The brief was explicitly planning-only. No package implementation, runtime changes, or validator changes were allowed in this pass. The correct output is therefore a plan portfolio, not a prototype.

### Entry 2: Reorganization decision

The original `active-plans/` shape mixed four different things:

- active package planning
- copied downstream failure notes
- raw research dumps
- copied vendor or external documentation

That is exactly the kind of ambiguity `AGENTS.md` warns against. I moved the raw inputs under `_source-material/` and reserved the top level for numbered plan folders plus root summaries.

### Entry 3: Reliability before autonomy

The womanvshorse and spinner material changed the sequencing. Scafforge currently has evidence that downstream agents can claim completion while the project still fails to open, fails to load assets, or looks visibly broken. That means the factory cannot safely scale autonomy yet. Runtime proof, import proof, and visual proof must land before large autonomous orchestration work.

### Entry 4: Asset quality is not optional

The failure set is not only technical. The repos also look bad. That means the package is currently weak at:

- visual direction
- UI/menu layout guidance
- Blender output quality bars
- asset-route selection
- post-generation visual review

That justified splitting asset work into architecture/provenance and quality/polish instead of treating it as one vague “improve assets” task.

### Entry 5: SDK architecture conclusion

Current evidence points to a hybrid future, not a rewrite:

- OpenCode already matches Scafforge’s current repo contracts, agent model, session control, and `.opencode/` surfaces.
- The AI SDK is strong for provider abstraction, orchestration services, MCP clients, and app-facing control planes.
- The Apps SDK is appropriate for ChatGPT-facing ingress and visualization, not for replacing the package core.

So the planning stance is: keep OpenCode as the substrate, add AI SDK around it where useful, and isolate Apps SDK use to ChatGPT exposure.

### Entry 6: Control-plane boundary

The “Spec Maker Workspace” and the WinUI viewer should be treated as adjacent systems, not as silent extensions stuffed into the package repo. Scafforge should publish the contracts they consume, but the services themselves should remain separately deployable.

### Entry 7: Documentation strategy

The documentation sweep could not be left as a final polish item. This repository is too contract-heavy. The doc plan now starts early and repeats after each implemented plan so agents always have an accurate source-of-truth map.

### Entry 8: Skill-system gap

The first full draft still under-modeled one user requirement: the background `scafforge-meta-skill-engineer-agent` and the use of the Meta-Skill-Orchestration repository. Archive mining alone does not solve that. A separate plan was added so skill ingestion, distillation, packaging, and downstream skill repair are treated as their own product surface.

### Entry 9: First-pass failure

The first structured rewrite fixed the folder layout but did not meet the user’s actual bar for “plans.” The numbered folders were still mostly generic outlines. That was the wrong abstraction layer. Folder hygiene is necessary, but it is not the same thing as implementation planning.

### Entry 10: Second-pass correction

The second pass rewrote all twelve numbered folders into TODO-state implementation plans. Each one now carries:

- explicit status
- dependencies and unblocks
- concrete package or adjacent surfaces
- phase-by-phase checkbox work
- validation requirements
- documentation obligations

That is the minimum shape required for these to function as real plans instead of placeholders.

### Entry 11: Agent-caller workflow added

The user asked for an implementation workflow built around a local wrapper CLI instead of hand-composing `copilot` and `opencode` commands every time. That produced `tools/agent-caller/` plus per-plan prompt packs and a root execution guide in `active-plans/codexinstructions.md`.

Important boundary decision:

- `agent-caller` is local-only and exists to save tokens and standardize invocation during this program.
- It is not a Scafforge product surface.
- Most plan prompts still assume the real implementation targets are Linux/headless and free/open-source where applicable.

### Entry 12: First live planchecker pass

The first real `planchecker` run on plan `02` found useful issues, but it also flushed out two wrapper bugs:

- subprocess output from `copilot` used Unicode that broke default Windows decode settings
- the wrapper initially failed to prepend the shared reviewer methodology to `planprreviewer` model prompts

Both wrapper defects were fixed before continuing.

### Entry 13: Plan 02 tightened after evidence check

The `planchecker` findings for `02-downstream-reliability-hardening` were mostly real after direct verification against the repo. The plan was expanded to:

- acknowledge existing Godot audit coverage instead of implying those checks do not exist
- name the missing Godot finding-code gaps explicitly
- map human labels onto existing disposition classes rather than inventing a second classification system
- require fixture `index.json` and `truth_expectations.checks` parity with the GPTTalker fixture model
- name harness registration and seeder surfaces explicitly
- clarify that the new greenfield guard is a pre-handoff proof step, not a stage-gate parser for diagnosis packs
- add `validate_gpttalker_migration.py` back into the required validation set

### Entry 14: Plan 03 needed contract ownership, not just better nouns

The first live review of `03-asset-pipeline-architecture` exposed a familiar planning failure mode: the plan had the right ambition but not enough ownership detail. The weak points were:

- no old-to-new mapping from current route names to the new taxonomy
- no authoritative machine owner for provenance truth
- no minimum schema for `assets/requirements.json` or `assets/manifest.json`
- no clean split between source routes and pipeline stages
- no explicit free/open-source ruling for local AI routes
- no decision on `assets/import-reports/` versus `assets/qa/`

The plan was rewritten to make those choices explicit, including canonical asset-surface ownership, schema sketches, migration guidance, and fixture/harness expectations.

### Entry 15: Plan 04 needed gate design and path discipline

The live review of `04-asset-quality-and-blender-excellence` exposed a different class of weakness: the plan had the right quality ambition, but not enough implementation discipline around where the contract lives and how it is enforced.

The main corrections were:

- remove local Windows absolute-path assumptions for `blender-agent`
- name a real output file for the Blender support matrix
- define the visual-proof gate as conditional instead of universal
- name a fixture location and integration-harness responsibility for ugly/failed visual examples
- add an explicit free/open-source distillation guardrail so source notes do not leak paid-tool recommendations into package output
- tie Blender evidence fields back to plan `03` instead of letting them invent a parallel schema

### Entry 16: Plan 05 needed architecture decisions, not just matrix language

The live review of `05-completion-validation-matrix` showed that the plan still left too much open at the exact layer where implementation drift usually happens:

- where the machine-readable matrix lives
- what a proof artifact actually looks like
- how family-level proof interacts with Tier 1 stack proof
- how `target_completion.py` is extended without turning into another Android-only if/elif pile
- how fixtures connect to the existing multi-stack harness

That plan is now tightened around explicit decisions:

- `references/validation-proof-matrix.json` is the matrix home
- proof artifacts use a compact JSON schema under `.opencode/state/artifacts/`
- Tier 1 stack proof remains the baseline and family proof layers on top
- `target_completion.py` becomes a dispatcher over sibling family modules or equivalent registry-backed logic
- fixture work extends `multi_stack_targets()` rather than forking a second proof system

### Entry 17: Plan 06 needed hard approval and handoff boundaries

The live review of `06-spec-factory-and-intake-mcp` showed that the plan had the right adjacency posture but still left too much ambiguity at the exact seams where boundary leakage would happen.

The key corrections were:

- make approved-state human-gated by default
- require a persistent approved artifact bundle before any generation trigger is valid
- freeze the storage model as file-backed plus machine-readable metadata for the first implementation pass
- define `spec-pack-normalizer` as a validator-alignment pass for already-approved factory briefs rather than a second creative normalizer
- make the actual generation trigger belong to plan `07`, not to the spec factory itself
- mark the MCP and ChatGPT ingress topology as blocked on plan `09`

### Entry 18: Plan 07 needed explicit non-ownership in the recovery loop

The orchestration plan was conceptually sound, but the live review showed that the most dangerous parts were still implied instead of frozen:

- which phases are actually blocked on plans `05`, `06`, and `09`
- what `scaffold-verified` really means in relation to VERIFY009/010/011
- how package-defect waits differ from repo-local repair waits
- whether orchestration is allowed to write back into generated ticket or workflow state

The corrected plan now treats those as explicit contract decisions instead of friendly suggestions. That matters because orchestration is exactly where hidden duplicate authority tends to appear.

### Entry 19: Plan 08 needed real trigger values and a concrete resume signal

The meta-improvement loop had the right architectural separation, but the live review showed that it still lacked the hard contract surfaces that would let plan `07` consume it safely.

The main corrections were:

- add a draft escalation trigger matrix instead of leaving all thresholds blank
- define an evidence-bundle extension path rather than implying a parallel artifact with no schema
- make `post_package_revalidation` the required downstream revalidation audit kind
- define a concrete machine-readable `resume-ready` carrier
- require skill-manifest and AGENTS updates if the investigator/fixer roles become real package skills
- explicitly treat archive mining as design-only until the orchestration/event substrate is stable

### Entry 20: Plan 09 needed a real proof step

The SDK and provider-strategy plan had the right architectural answer from the start, but it was still too easy to “complete” it with only more prose.

The key corrections were:

- require a small executable hybrid prototype rather than “prototype or design”
- make the contract validator check for the required package-side policy artifacts
- define the router contract output split between package policy docs and adjacent service docs
- add AI SDK support tier as a matrix dimension
- explicitly remove or replace the stale hard-coded model string already living in `architecture.md`

One checker complaint was rejected: the `agent-caller` prompt placeholders are intentional and are expanded by the wrapper at runtime, so they are not missing content in the plan files themselves.

### Entry 21: Plan 10 needed enforceable client boundaries, not just good instincts

The WinUI control-plane plan had the right shape, but the checker correctly pushed on the places where “client only” can collapse back into hidden orchestration if the contract is not explicit.

The main corrections were:

- require all mutations to route through plan `07`’s orchestration API instead of direct GitHub, shell, or transport bypasses
- define concrete phase-exit artifacts for boundary, backend consumption, connectivity, screen mapping, and security
- name a shared transport-decision artifact with plan `07` instead of leaving protocol choice informal
- make the meta-loop dashboard depend explicitly on plan `08`’s evidence and `resume-ready` contract
- name Windows-native secret storage choices and require fail-closed proof, not only prose

### Entry 22: Plan 11 needed validator awareness and repeatable context tests

The documentation sweep plan was already headed in the right direction, but the next review exposed a serious trap: the contract validator pins literal strings in several of the exact files the sweep intends to rewrite.

The plan now:

- requires `npm run validate:contract` after changing validator-pinned docs
- names the authority-map and context-test artifacts explicitly
- seeds the sweep with already confirmed contradictions instead of a vague “go find drift” instruction
- lands the standing doc-update rule back into `AGENTS.md` as the durable policy home
- scopes `docscleanup.md` and the Meta-Skill-Engineering extra-intake note into the inventory so the planning layer does not drift from the root routing layer

### Entry 23: Plan 12 needed hard policy outputs and starter thresholds

The skill-system plan had clear anti-sprawl intent, but it still left too many governance choices open for implementers to invent later.

The corrections were:

- name the external-source evaluation rubric file explicitly
- define a staging record for rejected or quarantined external source material
- make the validator path explicit by extending `validate:contract` instead of deferring that decision
- add draft starter thresholds for overlap and duplicate-authority failure
- make the `stolenfromcodex` bundle the first formal disposition exercise
- update the companion notes file now that the Meta-Skill-Engineering repo path is known

### Entry 24: Plan 13 needed a real definition of “complete CLI”

The Meta-Skill-Engineering repo plan was too easy to “complete” with broad statements about headless friendliness and evaluation rigor.

It now:

- depends explicitly on the plan `12` rubric artifact, not a vague future state
- removes machine-local path assumptions in favor of repo-relative identity
- requires named MSE-repo artifacts for feature inventory, action contract, plugin-eval disposition, and surface authority
- clarifies that blocking CLI bugs must be handled before Phase 2 verification can pass
- treats the Python CLI as the cross-platform execution surface and WPF as a convenience shell

### Entry 25: Plan 14 needed a stricter cross-repo handoff back into Scafforge

The Blender hardening plan was structurally strong, but the cross-repo truth handoff was still too loose after the first checker pass.

The main changes were:

- remove absolute local path assumptions and refer to the adjacent repo logically
- correct the Blender support-matrix update path back to `skills/project-skill-bootstrap/references/blender-support-matrix.md`
- require a concrete `blender-agent` proof package before Scafforge updates its own Blender references
- frame Unity and Unreal checks as interchange-format validation only by default
- make the post-hardening Scafforge matrix refresh an explicit second pass rather than an implied side effect

### Entry 26: Source-spec audit found a few real omissions

After the planchecker passes, I ran a direct audit against the moved source material the user originally pointed at. Most of the autonomy/spec content was already represented, but a few meaningful gaps were real:

- vector or retrieval indexing was only implicit in the autonomy notes and AI SDK source material, not explicit in the spec-factory or archive-mining plans
- the asset research files were cited, but the route policy had not yet distilled their actual ecosystem choices clearly enough
- the SDK and provider plan still did not state clearly enough that OpenCode can front many external provider/model paths and that the same model family can be used through both native SDKs and OpenCode-compatible implementation routes
- the validation plan covered most of the tooling note already, but it benefited from an explicit “answer the research list” step

The fixes landed in plans `03`, `05`, `06`, `08`, `09`, and `10`:

- plan `03` now turns the asset research into explicit route-policy and fallback guidance
- plan `05` now answers the current validation-tool list directly
- plan `06` now treats retrieval or vector indexing as an optional derived cache over file-backed spec truth
- plan `08` now does the same for archive intelligence and also tightens GitHub issue-linkage expectations
- plan `09` now distinguishes provider, SDK, and execution-host access paths and models multi-path cases like MiniMax and Kimi correctly
- plan `10` now mirrors the rough-idea and attachment-drop “Forge” workflow more explicitly from the autonomy source notes

### Entry 27: Final plan-portfolio hygiene rules

Plan `01` closed the remaining ambiguity in `active-plans/` by freezing the actual placement rules instead of leaving them implied.

The durable rule set is now:

- numbered folders are the canonical implementation program
- each numbered folder gets exactly one authoritative `README.md`
- plan-local support notes live under that folder's `references/`
- `_source-material/` stays in-repo as active supporting documentation and provenance
- root-level files are only for portfolio-wide navigation, policy, reporting, journal, or execution guidance

The last ambiguous root note was also fixed: the Meta-Skill-Engineering extra-intake doc was moved into plan `13`'s `references/` folder so it no longer reads like a portfolio-wide authority surface.

### Entry 28: Newcomer-context check passed

Using only `active-plans/README.md` and one numbered folder (`02-downstream-reliability-hardening/README.md`), a newcomer can now identify the active portfolio, tell which documents are canonical versus supporting, see the implementation order, and confirm that numbered folders expose status, goal, dependencies, and actionable phases immediately at the top.

### Entry 29: Plan 12 needed one more contract-alignment pass before merge

The plan `12` PR was substantively correct, but the review pass exposed one real gap: the skill-governance flow documented rejected external sources without a first-class resolution path. That was fixed by:

- adding explicit resolution workflow guidance to `references/rejected-sources.md`
- extending the contract validator so it checks for the rejected-source resolution path directly
- aligning `AGENTS.md` so the durable skill-evolution reference set names that document explicitly

This was a useful reminder that Scafforge’s validator-pinned documentation needs the same rigor as code surfaces when a plan is closing.

### Entry 30: Plan 13 required direct Copilot recovery instead of the wrapper path

The interrupted `planimplementer` run in the `Meta-Skill-Engineering` repo could not be resumed cleanly through the normal wrapper loop, so I used direct `copilot -p` with the full interrupted-work context instead. That preserved the existing dirty implementation state and avoided throwing away useful partial work.

The resulting adjacent-repo hardening landed through PR `#19` and confirmed the real definition of “fully agent-usable” for MSE:

- the Studio CLI now exposes a durable, machine-readable action contract
- the evaluation-methodology docs are explicit enough for automation rather than only human interpretation
- the Python CLI is the cross-platform execution surface, with WPF kept as a convenience shell rather than the authoritative path

### Entry 31: Plan 14 proved the cross-repo Blender handoff needed machine-readable evidence

The `blender-agent` hardening work landed through PR `#3`, but the Scafforge-side lesson was broader than just better adjacent-repo docs. The trust boundary only became solid once the adjacent repo emitted machine-readable authority:

- `mcp-server/capability-contract.json`
- `HARDENING-PROOF.json`
- `mcp-server/tests/headless/results.json`

Those artifacts now anchor Scafforge’s own Blender support notes, which is meaningfully better than letting the package rely on prose summaries or outdated skill claims.

### Entry 32: Final portfolio sync exposed the one real remaining open plan

After plans `13` and `14` landed, the root portfolio docs still implied that most of the numbered plans were unfinished. A direct history check showed the opposite:

- plans `02` through `09`, `11`, and `12` are already merged in Scafforge
- plan `13` is merged in `Meta-Skill-Engineering`
- plan `14` is merged in `blender-agent`

The only genuinely open plan is `10-viewer-control-plane-winui`. Its Scafforge-side contract pack is merged, but Phase 6 remains open because it requires the live backend-connected WinUI app build and proof pass, not just package-side contract documents. That distinction matters because the user’s definition of done is “all plans fully implemented to 100%,” and the portfolio needs to say plainly when one plan is still active.

### Entry 33: Plan 10 is now closed and the active-plans program is fully implemented

The adjacent `scafforge-control-plane-winui` repo is now real, not just planned. The implementation landed the WinUI shell, pinned-cert live gateway factory, WSL plus SSH transport proof, fail-closed degraded overlay, and a launch-smoke fix for the App/XAML startup path. The PR review swarm for that repo produced a few factual follow-ups; the only ones worth taking were the machine-local WSL path assumption, request debouncing/in-flight mutation gating, explicit demo-mode messaging, and cleanup of repo-local ephemeral SSH proof material. The other higher-level concerns were either already covered by the contract or unsupported by the actual code.

With that adjacent PR merged, the portfolio no longer has a “final remaining plan.” The Scafforge closeout now needs to say that directly: plans `01` through `14` are implemented, the three adjacent repos (`Meta-Skill-Engineering`, `blender-agent`, and `scafforge-control-plane-winui`) are all merged, and future work should move into either archival or genuinely new numbered plans instead of leaving `active-plans/` in a permanently half-open state.
