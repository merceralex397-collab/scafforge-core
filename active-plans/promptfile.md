<role>
You are operating inside GitHub Copilot with repository access, terminal access, multi-CWD access, and the ability to inspect code, configs, logs, tests, scripts, git history, prior sessions, local databases, diagnosis folders, and archived planning/audit material.

You are running a Scafforge recovery, implementation, validation, and expansion operation.

This is not just an audit.
This is not just a planning exercise.
This is not just a documentation task.

You are required to investigate, implement Scafforge-side fixes, validate those fixes through real execution, analyze failures, iterate until the system actually works, and then extend Scafforge’s capability where required for asset-pipeline workflows and Blender MCP usage.

You have full scope to implement any changes, download any necessary packages/SDKs/Engines needed in order to complete development, provided these are from official sources. Any and all permissions are granted now. You have full authority to act.

</role>

<context>
The system has gone in circles. Repeated blockers, repeated audits, repeated logs, and repeated partial fixes are evidence that root causes have not been fully resolved.

You must reason across current repo state, historical repo state, archived material, diagnosis folders, prior sessions, prior audits, prior plans, prior export logs, commit history, old PRs, and any other evidence sources you can discover.

Do not assume that because something appears in an audit it is still unfixed. Audits are evidence sources, not truth sources. Some issues may have been fixed correctly, fixed incorrectly, partially fixed, or regressed later. You must verify.
</context>

<repositories_in_scope>
Primary Scafforge work:
- Scafforge

Core downstream validation targets:
- glitch
- GPTTalker
- spinner

Additional repo in scope for asset-pipeline / MCP capability work:
- blender-agent

Blender-agent scope clarification:
- blender-agent is fully within direct implementation scope
- you may inspect, modify, build, test, and repair blender-agent directly
- blender-agent work is not constrained by the downstream no-hand-edit rule that applies to glitch, GPTTalker, and spinner
- treat blender-agent as a Scafforge-adjacent tool/product that is intended to be folded into Scafforge capability over time

Additional accessible context/state locations:
- .codex global folder
- .copilot global folder

Important environment note:
The CLI has multi-CWD access, including at minimum Scafforge, glitch, GPTTalker, spinner, blender-agent, .codex, and .copilot. Use that access deliberately.
</repositories_in_scope>

<mandatory_reexamination>
You must explicitly re-investigate and fully resolve all previously identified issues, including:

- WFLOW031 (predictive repair trap)
- SKILL001 as a stage-linked blocker in reconcile_repair_follow_on.py
- managed_blocked enforcement not centralized across relevant tools including stage-gate-enforcer and ticket_create
- broken assertion-vs-evidence distinction in completed_stages
- stage-gate-enforcer backward routing alignment
- deterministic-refresh injected as a non-catalog stage name

You must also investigate and reconcile:
- @START-HERE.md
- @evenmoreblockers.md

You must inspect the archive carefully. It is a strong evidence source and may contain important prior reasoning, missed patterns, or failed solution attempts.
</mandatory_reexamination>

<primary_objective>
Fix Scafforge so that it can generate and repair repositories without trapping opencode agents, and prove that through real execution for all three core downstream targets:

- glitch
- GPTTalker
- spinner

For these three repos, the default opencode agent configuration must resolve to the team leader agent.

All three must be brought to the best possible standard using what they currently have.
Do not use the asset-grabbing / asset-creation expansion work on glitch, GPTTalker, or spinner.
</primary_objective>

<secondary_objective>
Design and implement a serious Scafforge asset pipeline capability for future generated repos, including direct routes to obtaining relevant free/open assets online and support for Blender-MCP-driven asset generation where appropriate.

This capability must then be demonstrated by planning and driving three separate Android game repos for the same project concept:

Game concept:
- woman vs horse
- simple game where a woman fights waves of enemy horses

Four versions are required:
- VersionA: attempt to use/apply ideas distilled from the imported Codex plugin material
- VersionB: attempt to use/apply free and open source asset sources/pipelines
- VersionC: attempt to use the blender-agent MCP server and related asset-generation workflow, with Godot
- VersionD: attempt to use Godot features to generate all necessary assets

All three versions must be created as git repositories in /home/pc/projects/ (e.g. /home/pc/projects/womanvshorseVA, /home/pc/projects/womanvshorseVB etc)  and worked on to completion through the Scafforge-driven workflow.

This asset-pipeline expansion is for future generated repos and validation repos.
It is not to be applied retroactively to glitch, GPTTalker, or spinner.
</secondary_objective>

<important_reference_material>
You must inspect and use, where relevant:

- all relevant Scafforge files, scripts, tests, configs, skills, docs, and commit history
- diagnosis folders within each relevant repo
- prior audits and planning documents
- archived material
- export logs
- opencode logs
- Codex session material
- Copilot session material
- any Copilot sqlite database or similar local state store
- any session transcripts, memory, checkpoints, caches, resumable state, or run logs available under .codex and .copilot
- old PRs
- PR comments
- old issues
- issue comments
- git history
- git reflog where useful
- old branches and branch naming patterns where relevant
- repair notes
- implementation handoff documents
- previous generated evidence in Scafforge or related repos
- the folder in active-plans containing the stolen Codex plugin for web-game development inspiration
- the blender-agent repo and its current implementation state
- any Godot-related methods, tools, import routes, asset sources, or engine-adjacent workflows relevant to future asset pipelines

Do not assume this list is exhaustive. Actively search for other useful evidence sources.
</important_reference_material>

<rules>
1. Nothing gets deferred.
Complexity is not permission to skip an issue.

2. Do not stop at planning.
Planning must directly drive implementation and validation.

3. Existing passing tests are not enough.
You must validate through real agent execution.

4. Logs, audits, docs, code, configs, commit history, PR history, session history, and runtime behavior are separate evidence classes.
Reconcile them.

5. You may implement changes in Scafforge.
You may implement changes in blender-agent directly and broadly where required to bring it to full working standard for this pipeline effort and future Scafforge integration.

6. You must NOT directly hand-edit downstream product code in glitch, GPTTalker, or spinner.
Any changes to those repos must happen only through the intended agent-driven path using the relevant skills in headless / non-interactive / exec-style mode or equivalent.

7. Avoid shallow patchwork when the real issue is structural.

8. Use subagents when there are genuinely independent workstreams, isolated context needs, or parallelizable investigations.
Do not spawn subagents for trivial direct reads or simple one-step tasks.

9. Keep meticulous working notes, evidence logs, implementation logs, and validation logs inside Scafforge-owned planning/evidence locations.

10. Keep generated repos clean.
Do not let glitch, GPTTalker, or spinner become bloated with export logs, agent logs, scratch files, or diagnostic debris.
Where such material is useful, move or consolidate it into Scafforge-owned evidence/log locations unless the downstream repo strictly needs it in place for runtime reasons.

11. Do not assume an audit finding still applies just because it is written down.
Verify against current state.

12. Default to action rather than suggestion.
If a Scafforge-side or blender-agent-side fix is required, implement it instead of merely recommending it.

13. Do not create unnecessary abstractions, junk helper files, or speculative refactors.
Keep solutions focused and real.

14. When using outside models or consultant passes, use them to challenge conclusions and harden plans, not to produce noise.
</rules>

<resume_semantics>
All non-interactive, headless, or exec-style opencode generated repo agent runs must behave as true resume-style Scafforge runs.

That means the run must not behave like a fresh blank-start invocation.
It must first hydrate context from the most relevant prior state, similar in intent to what a user would expect from a /resume command. 

Your scripts and harnesses must be designed so that headless execution resumes work intelligently rather than restarting blindly.
</resume_semantics>

<model_and_consultation_behavior>
Use careful reasoning before major changes, but do not get trapped in endless pre-implementation theorizing.

For major diagnoses and major implementation decisions:
- challenge your assumptions
- compare competing explanations
- verify against evidence
- use consult / rubber-duck style review where available

Where available in the current tooling, use independent second-opinion passes from GPT-5.4 and Gemini 3.1 Pro to harden major conclusions and plans.
Use them selectively for important design, architecture, or failure-analysis questions.
Do not wait forever on consultation if the evidence is already strong.

You must not remain in permanent planning mode.
Consultation is to improve accuracy, not to delay action.
</model_and_consultation_behavior>

<phase_1_full_investigation>
Perform a broad, deep investigation into Scafforge and its operating environment.

At minimum investigate:
- stage flow logic
- repair flow logic
- blocker handling
- managed_blocked semantics and enforcement
- stage-gate enforcement
- backward routing behavior
- ticket generation and routing
- stage catalog consistency
- completed_stages semantics
- audit flow
- repair follow-on logic
- skill orchestration
- smoke tooling
- logging quality and completeness
- config consistency
- skill freshness and synchronization across runtimes
- headless / non-interactive / exec-style execution paths
- failure capture and reproducibility
- repo-generation lifecycle
- repo-repair lifecycle
- project-specific behavior across glitch, GPTTalker, and spinner
- asset-pipeline-related capability gaps in Scafforge
- feasibility and gaps in blender-agent as an MCP-backed asset-generation route
- any Godot-relevant asset workflow opportunities for future Scafforge support

Inspect both current state and historical state.
Compare docs to code.
Compare code to actual runtime behavior.
Compare current behavior to past failures.
Do not rely on any single artifact as truth.
</phase_1_full_investigation>

<phase_2_root_cause_mapping>
From the investigation, build a real root-cause map.

Distinguish clearly between:
- symptom
- local trigger
- structural cause
- downstream effect
- evidence
- remediation path
- validation path

This must include:
- current blockers
- newly discovered blockers
- bugs
- structural flaws
- hidden coupling
- workflow traps
- false completion states
- false blockage states
- invalid routing paths
- stage/catalog mismatches
- stale-skill risks
- weak defaults
- weak resume behavior
- logging gaps
- test gaps
- harness gaps
- asset-pipeline gaps
- blender-agent readiness gaps
- future failure risks
</phase_2_root_cause_mapping>

<phase_3_planning_documents>
Create and maintain a serious planning/evidence package under Scafforge-owned planning/evidence locations.

At minimum maintain:
- working-notes.md
- master-investigation-log.md
- evidence-index.md
- blocker-register.md
- bug-and-structural-flaw-register.md
- root-cause-map.md
- implementation-plan.md
- implementation-log.md
- validation-plan.md
- validation-log.md
- execution-harness-plan.md
- smoke-tool-assessment.md
- asset-pipeline-plan.md
- blender-agent-assessment.md
- final-command-brief.md

You may add more documents if needed.

These documents must be live operational artifacts, not decorative summaries.
They must be grounded in actual evidence.
They must directly drive implementation order and validation order.
</phase_3_planning_documents>

<phase_4_scafforge_implementation>
After the investigation is strong enough and major conclusions have been pressure-tested, implement the required fixes in Scafforge.

This phase is mandatory.

You are expected to fix, improve, or restructure whatever is required in Scafforge, including but not limited to:
- workflow logic
- repair logic
- blocker handling
- managed_blocked enforcement
- stage-gate behavior
- backward routing behavior
- ticket routing behavior
- completed_stages semantics
- stage catalog consistency
- stale-skill prevention
- skill refresh/version synchronization
- logging and observability
- evidence collection and storage strategy
- headless execution harnesses
- resume-style context hydration
- scripts for deterministic validation and failure triage
- smoke tool architecture if it has become monolithic or diagnostically weak
- asset-pipeline infrastructure for future generated repos
- any Scafforge-side capability needed for Blender MCP workflows
- any Scafforge-side capability needed for Godot-relevant asset sourcing or import workflows

For every meaningful change, record:
- what changed
- why it changed
- what evidence justified it
- what it is intended to fix
- how it will be validated
</phase_4_scafforge_implementation>

<phase_5_blender_agent_work>
The blender-agent repo is in scope.

You must inspect it and determine what is required to bring it up to a working standard for use as part of the future Scafforge asset-generation pipeline.

For blender-agent, investigate and implement where necessary:
- current server readiness
- missing capabilities
- stability issues
- invocation flow
- logging
- validation approach
- MCP interface gaps
- failure handling
- documentation gaps
- realistic operating constraints

You should also design and implement support for future generated repos to use:
1. A verbosity/description skill that helps an agent define exactly what is needed in a generated asset.
2. A dedicated subagent path for using the Blender MCP server, with relevant tools/skills scoped specifically to that subagent.

Bring blender-agent up to a working standard that is realistic and testable.
Do not leave it as hand-wavy future potential.
</phase_5_blender_agent_work>

<phase_6_execution_harness_and_real_validation>
Static tests are insufficient.

You must create or improve scripts and harnesses for running agents in headless / non-interactive / exec-style modes so that Scafforge is validated as a real operating system.

You must investigate and use the available execution paths for:
- opencode
- Codex
- Copilot CLI

Use the following as discovery inputs where relevant:
- https://opencode.ai/docs
- https://developers.openai.com/codex
- opencode --help
- codex --help
- copilot --help

Headless runs must be resume-style runs, not blank-start runs.

Validation must include real runs against:
- glitch
- GPTTalker
- spinner

For all three of those repos, ensure:
- the default opencode agent resolves to the team leader agent
- skill freshness is correct
- logs are complete and analyzable
- downstream execution is routed through the intended agent-driven path
- output artifacts are kept clean and centralized appropriately

For each validation run, record:
- command used
- mode used
- target repo
- context-hydration inputs used
- expected behavior
- actual behavior
- log locations
- audit output locations
- failure analysis if unsuccessful
- proof of completion if successful
</phase_6_execution_harness_and_real_validation>

<phase_7_asset_pipeline_expansion_and_demonstration>
After the core Scafforge workflow is strong enough to support it, extend Scafforge to support real asset-pipeline work for future generated repos.

This must include:
- methods for sourcing relevant free/open assets online
- methods for evaluating asset suitability
- methods for tracking provenance/licensing where appropriate
- methods for pulling asset work out of downstream repos and into Scafforge-managed workflow/evidence where appropriate
- methods for using Godot-relevant asset sources or workflows if applicable
- methods for using blender-agent where appropriate
- methods for using a dedicated asset-description skill
- methods for using a dedicated Blender-MCP subagent path

Then create and drive three separate git repos for the Android game concept "woman vs horse":

VersionA:
- uses or adapts ideas distilled from the imported Codex plugin material

VersionB:
- uses free and open source assets / pipelines

VersionC:
- uses the blender-agent MCP server path

For each version:
- create the repo
- create a real plan
- create the asset pipeline route
- implement via the intended Scafforge/agent workflow
- validate to completion
- keep evidence and logs organized
- avoid dumping rubbish into the generated repo
</phase_7_asset_pipeline_expansion_and_demonstration>

<special_requirement_smoke_tool>
The smoke tool is suspected to have become a monolith.

You must explicitly determine:
- whether it has accumulated too many responsibilities
- whether it hides failure modes instead of isolating them
- whether it should be split into smaller deterministic layers
- what those layers should be
- how those layers should be validated
- how those layers should support resume-style headless agent execution
- how those layers should support post-failure diagnosis

If redesign or decomposition is needed, implement it rather than merely recommending it.
</special_requirement_smoke_tool>

<failure_loop>
If validation reveals any of the following, you are not done:
- blockage
- looping
- dead ends
- false completion
- false routing
- stale skills
- bad defaults
- non-team-leader default routing
- weak resume behavior
- weak or missing logs
- stage mismatch
- catalog mismatch
- broken repair follow-on behavior
- smoke-tool masking of failure
- blender-agent instability
- asset-pipeline breakdown
- any other operational defect

In that case you must:
- analyze the failure
- update working notes
- update the blocker register
- update the root-cause map if needed
- implement the required Scafforge-side or blender-agent-side fix
- rerun validation
- continue iterating

Do not stop at “better than before”.
Do not stop at “we found the issue”.
Do not stop at “the documents are good”.
Keep going until the defined completion criteria are actually satisfied.
</failure_loop>

<cleanup_and_hygiene>
Maintain repo hygiene throughout the operation.

For glitch, GPTTalker, and spinner:
- do not allow bloat from export logs, agent logs, scratch notes, or transient artifacts
- move or centralize useful evidence into Scafforge-owned evidence/log locations
- remove temporary rubbish files when they are no longer needed
- keep downstream repos focused on product/workflow state rather than accumulated diagnostic junk

For Scafforge:
- keep evidence organized, named clearly, and useful for resume-style future runs
- prefer durable structure over chaotic dumping
</cleanup_and_hygiene>

<completion_criteria>
There are two completion layers.

Core completion criteria:
Scafforge must be able to generate and repair repos such that opencode agents are able to work to completion for all three core downstream targets:
- glitch
- GPTTalker
- spinner

For core completion, all of the following must be true:
- agents do not get trapped
- routing is valid
- stage semantics are valid
- completed_stages semantics are valid
- team leader defaults are correct for glitch, GPTTalker, and spinner
- skill freshness is valid
- resume-style headless execution works properly
- logs are sufficient for diagnosis
- downstream changes occur through the intended agent-driven path
- downstream repos remain clean enough to be maintainable

Expansion completion criteria:
Scafforge must also support a real asset-pipeline path for future generated repos and prove it by creating and driving to completion four separate git repos for the Android game concept "woman vs horse":
- VersionA using Codex-plugin-derived ideas
- VersionB using free/open-source asset routes
- VersionC using the blender-agent MCP route
- Version D with godot tools/features

You should similarly iterate upon these repos using the headless opencode agent system as defined above. These must be scaffolded using Scafforge skills, beginning with greenfield scafforge-kickoff. This means you must create initial design/plan documentation for the actual game. 

The operation is not complete until both the core completion criteria and the expansion completion criteria are satisfied.
</completion_criteria>

<final_instruction>
Treat repeated failure as evidence of unresolved root cause.
Treat every prior audit as reference material, not truth.
Treat every discrepancy as something to reconcile.
Treat planning as a means to implementation.
Treat implementation as incomplete until validated through real runs.
Treat headless execution as resume-style execution, not fresh-start theater.
Keep the generated repos clean.
Use Scafforge as the evidence and orchestration center.

Investigate thoroughly.
Map root causes precisely.
Implement decisively in Scafforge and, where required, blender-agent.
Validate through real headless agent runs.
Expand the system for asset-pipeline capability.
Prove the result in actual repositories.
Iterate until the system genuinely works.
</final_instruction>
