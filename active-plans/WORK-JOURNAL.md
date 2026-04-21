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
