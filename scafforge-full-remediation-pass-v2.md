# Scafforge Full Remediation Pass

## Scope

Second-pass remediation plan for Scafforge using the prior deadlock review as baseline and verifying against the live repo surfaces at commit `7e2040f817e3578c6eec2a628b84cfdc0f5cc5a8`.

## Core conclusion

Scafforge still has one dominant defect:

**it can generate a workflow machine before it proves a simple executable first lane exists.**

Everything below is aimed at eliminating that class of failure and the churn it creates.

---

## Non-negotiable fixes

| Priority | Fix | Files to change | Exact instruction | Done when |
|---|---|---|---|---|
| P0 | Add a mandatory T0 bootstrap lane invariant | `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`, `skills/repo-scaffold-factory/SKILL.md`, `scripts/validate_scafforge_contract.py`, `scripts/smoke_test_scafforge.py` | Every generated repo must contain one bounded first lane that only does environment bootstrap + first deterministic smoke proof. No team reasoning, no later-ticket dependency, no inferred workflow transitions. | Validator fails any scaffold that lacks a single explicit first lane with owner, command, proof artifact, and completion rule. |
| P0 | Fix the greenfield flow order | `skills/skill-flow-manifest.json`, `skills/scaffold-kickoff/SKILL.md` | Insert an explicit post-generation verification stage before handoff. Greenfield must not go straight from generation into handoff. Replace the current manual conformance-only step with a deterministic audit/validator step. | Greenfield sequence becomes: normalize -> scaffold -> bootstrap lane proof -> local skills/team/prompt pass -> tickets -> post-generation verification -> handoff. |
| P0 | Remove the “no audit on initial generation” rule | `skills/scaffold-kickoff/SKILL.md` | Delete the prohibition that prevents routing the initial greenfield pass into `scafforge-audit` or equivalent deterministic verification. Initial generation must be allowed to verify itself before handoff. | A greenfield scaffold cannot be marked complete unless verification passes in the same run. |
| P0 | Delay orchestration complexity until motion is proven | `skills/skill-flow-manifest.json`, `skills/opencode-team-bootstrap/SKILL.md`, `skills/agent-prompt-engineering/SKILL.md`, `skills/project-skill-bootstrap/SKILL.md` | Split the flow into two layers: **minimal-operable scaffold first**, then advanced team/prompt specialization second. Do not front-load multi-agent topology before the repo proves it can move. | The first successful path can be executed without specialist-team choreography. |
| P0 | Make one lease model canonical everywhere | Team/bootstrap templates under `skills/repo-scaffold-factory/assets/project-template/`, `skills/opencode-team-bootstrap/`, `scripts/validate_scafforge_contract.py` | Standardize on: **team leader claims/releases; specialists never claim/release**. Remove any worker-owned lease language from prompts, docs, commands, and template skills. | No generated surface contradicts coordinator-owned lease control. |
| P0 | Make `ticket_lookup.transition_guidance` the single next-step authority | Template `ticket_lookup.ts`, `ticket_update.ts`, team-leader prompt templates, repo-local `ticket-execution` skill templates, validator, smoke tests | Agents must not infer stage transitions from prose, stale handoff text, or ticket labels. They must route from `transition_guidance` or return a blocker. | Repeated lifecycle probing is impossible without failing validation/tests. |
| P0 | Reserve stage-artifact ownership strictly | Team-leader prompt templates, artifact tools, stage-gate logic, `smoke_test.ts`, validator, smoke tests | Coordinator must never author planning, implementation, review, QA, or smoke-test artifacts directly. `smoke_test` remains the only producer of smoke-test PASS proof. | Generated prompts/tools reject coordinator-authored specialist artifacts as invalid evidence. |
| P0 | Make executable smoke scope mandatory at ticket creation time | `skills/ticket-pack-builder/SKILL.md`, ticket templates, `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`, validator | If a ticket can close, it must have an executable smoke/acceptance command or an explicit reason it cannot yet close. Do not allow heuristic smoke scope to be the primary path. | Ticket builder either emits canonical smoke commands or blocks ticket closeout. |
| P1 | Collapse managed repair into a smaller, fail-closed sequence | `skills/scafforge-repair/SKILL.md`, `skills/scafforge-repair/scripts/apply_repo_process_repair.py`, `skills/scafforge-repair/scripts/run_managed_repair.py` | Keep managed repair to: deterministic refresh -> mandatory verification -> explicit result. Do not chain extra regeneration passes unless verification identifies exact drift classes that require them. | Repair output is small, explicit, and ends in one of three states: fixed / source-follow-up / blocked. |
| P1 | Treat placeholder local skills as a generation failure, not a later warning | `skills/project-skill-bootstrap/SKILL.md`, `scripts/validate_scafforge_contract.py`, `scripts/smoke_test_scafforge.py` | Placeholder repo-local skills must fail the initial scaffold package tests. They should never survive into a handoff-ready repo. | `SKILL001`-style placeholder drift is impossible immediately after generation. |
| P1 | Reduce restart-surface authority | `skills/handoff-brief/SKILL.md`, restart-surface generation code/templates, validator | `START-HERE.md` and `latest-handoff.md` must be derived-only. They cannot be treated as stronger than canonical workflow/ticket/tool state. | Resume always starts from canonical state files first; restart text is secondary. |
| P1 | Add an explicit “one legal next move” package test | `scripts/smoke_test_scafforge.py`, `scripts/validate_scafforge_contract.py` | Add a package-level test that loads a fresh generated repo and asserts there is one valid first action, one owner, one proof path, and one blocker path. | Scafforge fails CI if a scaffold leaves agents with multiple contradictory or zero viable next moves. |
| P1 | Remove audit/archive exhaust from the product repo | `out/scafforge audit archive/`, `scafforgechurnissue/`, `.gitignore`, README/process docs | Move accumulated audit logs, diagnosis packs, and churn records out of the main product tree into either `tests/fixtures/`, a separate repo, or ignored local storage. Keep only curated minimal fixtures. | The main repo contains product code, templates, and deliberate tests—not operational exhaust. |
| P1 | Split curated fixtures from live process dumps | New fixture path such as `tests/fixtures/churn/` plus cleanup of current archive paths | Keep only the minimum reproducible deadlock fixtures needed for regression tests. Remove raw bulk archives from versioned paths. | Regression fixtures are intentional, small, and referenced by tests. |
| P1 | Tighten the definition of “done” for `scaffold-kickoff` | `skills/scaffold-kickoff/SKILL.md`, `README.md`, validator | A scaffold is only done when a fresh agent can continue immediately **without** needing a later audit, later repair, or extra process invention. | “handoff-ready” equals “immediately continuable,” not merely “document-complete.” |

---

## Repo-specific evidence that these fixes are needed

1. The published flow manifest still sends **greenfield** from generation to handoff without an explicit audit step.
2. `scaffold-kickoff` still says the initial greenfield pass must **not** route into `scafforge-audit` or `scafforge-repair`, and relies on a same-session conformance check instead.
3. The repair runner still derives extra required follow-on stages like `project-skill-bootstrap`, `opencode-team-bootstrap`, `agent-prompt-engineering`, and `ticket-pack-builder` when drift remains, which is a sign that generation is not converging tightly enough.
4. The repo itself contains repeated diagnosis/archive artifacts and churn records, which means the system is spending a lot of energy diagnosing and replaying workflow failure.
5. Archived diagnosis manifests show recurring repair-routed issues such as workflow bypass search, coordinator artifact authorship, split lease ownership, smoke-scope drift, pending process verification, and lingering placeholder skills.

---

## Exact execution order for the repository owner

1. **Flow contract first**
   - Edit `skills/skill-flow-manifest.json`.
   - Change greenfield so it cannot end before post-generation verification.
   - Remove early assumptions that handoff can certify correctness by itself.

2. **Kickoff contract second**
   - Edit `skills/scaffold-kickoff/SKILL.md`.
   - Remove the rule that forbids audit/repair on initial greenfield generation.
   - Rewrite completion criteria around immediate continuability.

3. **Generator third**
   - Edit `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py` and related skill/docs.
   - Force emission of a T0 bootstrap lane and the exact proof surfaces it needs.

4. **Template/tool contract fourth**
   - Update template `environment_bootstrap.ts`, `smoke_test.ts`, ticket tools, stage-gate logic, and workflow docs.
   - Ensure they all describe the same first lane, same ownership model, same smoke-proof rules.

5. **Validator and smoke tests fifth**
   - Expand `scripts/validate_scafforge_contract.py` and `scripts/smoke_test_scafforge.py`.
   - Fail package validation if a scaffold needs immediate repair, contains placeholder skills, has contradictory lease rules, or lacks a single legal first move.

6. **Repair simplification sixth**
   - Shrink `scafforge-repair` so it becomes a strict fail-closed fixer rather than a large secondary workflow engine.

7. **Repo cleanup seventh**
   - Remove or relocate `out/scafforge audit archive/` and `scafforgechurnissue/` from the main product tree.
   - Preserve only minimal curated fixtures referenced by tests.

---

## Final target state

Scafforge is fixed when all of the following are true:

- A new scaffold always contains one explicit first lane.
- That first lane can be executed without agent-team interpretation.
- Greenfield generation always verifies before handoff.
- No placeholder skill survives generation.
- No prompt/tool/doc surface contradicts lease ownership or artifact ownership.
- `smoke_test` always uses canonical executable smoke scope.
- Managed repair is rare and small.
- The main repo is mostly product code plus deliberate fixtures, not accumulated process exhaust.
- A fresh agent entering a generated repo has **one clear viable move forward**.



---

## Pivoting With Scafforge

## Direct answer

**Right now, pivoting with Scafforge is possible, but not clean.**

Difficulty by pivot class:

| Pivot type | Current difficulty | Why |
|---|---|---|
| Add a small feature after generation | Moderate | Scafforge already has backlog refinement support, so this is mostly a ticketing problem. |
| Add a medium feature that touches multiple lanes or workflow surfaces | Moderate to hard | You can refine tickets, but the repo can still drift across skills, prompts, tools, and restart surfaces if the change is not re-verified. |
| Change the repo’s design or architecture part way through | Hard | The support exists, but it is split across `scaffold-kickoff`, `ticket-pack-builder`, `scafforge-audit`, and `scafforge-repair` rather than exposed as one canonical pivot flow. |
| Change the managed workflow layer itself | Hard but supported | This is what `scafforge-repair` is for, but it assumes diagnosis, safe repair boundaries, regeneration, and post-repair verification. |

### What the repo already supports

Scafforge already contains several pieces of pivot support:

- `scaffold-kickoff` supports **retrofit** and **managed repair / update** modes for existing repos, not just first-time generation.
- `ticket-pack-builder` already supports **refine** and **remediation-follow-up** modes for changing or expanding an existing backlog later.
- `scafforge-repair` already supports managed workflow refresh, same-run regeneration, and post-repair verification for existing repos.

The problem is that these are **separate paths**, not one clear “pivot the design safely” route.

## Current practical answer

### If you generated a repo and then want to add a feature

That is the easiest pivot class.

Current best route:

1. Update the canonical brief with the new feature or changed requirement.
2. Run `ticket-pack-builder` in **refine** mode.
3. Add new tickets or split existing tickets rather than silently expanding in-flight tickets.
4. Re-align `tickets/manifest.json`, `tickets/BOARD.md`, and `.opencode/state/workflow-state.json`.
5. Re-run a verification pass before handoff.

### If you want to change the design substantially

That is harder.

Current best route:

1. Treat it as a **design pivot**, not ordinary backlog growth.
2. Update `docs/spec/CANONICAL-BRIEF.md`.
3. Run diagnosis first to see which workflow, skill, prompt, and ticket surfaces are now stale.
4. Run managed repair only for safe workflow-layer refresh.
5. Re-run project-local skill generation if stack rules, model profile, or local skills changed.
6. Re-run team bootstrap if agent topology or ownership assumptions changed.
7. Re-run prompt hardening if agent behavior or delegation rules changed.
8. Rebuild or refine the backlog only after the above surfaces are consistent again.
9. Re-verify before handoff.

### If you want to change architecture midstream

Treat this as the hardest pivot type.

Examples:
- switching storage approach
- changing framework or runtime shape
- adding a new bounded context
- adding a major integration
- turning a single-service design into multi-service
- moving from simple sequential work into lane-parallel execution

In those cases, do **not** just add tickets.

You need a pivot flow that refreshes:
- brief
- affected local skills
- affected agents
- prompt rules
- workflow docs
- ticket graph
- restart surfaces
- validation commands

---

## Missing capability: a canonical pivot flow

Scafforge should have one explicit operator-facing path for midstream design change.

### Add this new run type

Add a new run type to `skills/skill-flow-manifest.json`:

- `pivot-update`

Recommended sequence:

1. `spec-pack-normalizer:pivot-update`
2. `scafforge-audit:pivot-impact-diagnosis`
3. `scafforge-repair:apply-safe-repair_if_needed`
4. `project-skill-bootstrap:repair-or-regeneration_if_needed`
5. `opencode-team-bootstrap:follow_up_if_project_specific_drift`
6. `agent-prompt-engineering:repair-hardening_if_needed`
7. `ticket-pack-builder:refine_or_remediation-follow-up`
8. `scafforge-audit:post-pivot-verification`
9. `handoff-brief`

### Add a new classification path to `scaffold-kickoff`

`scaffold-kickoff` should explicitly recognize:

- **Pivot / design change** — the repo exists, but the user wants to change requirements, add a feature that alters design assumptions, or revise architecture part way through.

That should route to the new pivot flow instead of forcing the user to guess between:
- retrofit
- managed repair
- backlog refine
- diagnosis only

---

## Canonical pivot protocol Scafforge should enforce

## 1. Classify the pivot first

Before doing anything, classify the pivot:

| Pivot class | Definition | Route |
|---|---|---|
| `feature-add` | New feature with low architectural impact | Brief update + ticket refine + verification |
| `feature-expand` | Feature addition that touches multiple lanes or changes acceptance scope | Pivot diagnosis + ticket refine + verification |
| `design-change` | Existing design assumptions changed | Pivot diagnosis + repair/regeneration + backlog refresh |
| `architecture-change` | Structural change to system boundaries, workflow, infra, or runtime assumptions | Full pivot flow with mandatory regeneration and post-pivot verification |
| `workflow-change` | Change to the managed OpenCode / workflow layer itself | Managed repair path |

Scafforge should not let the operator blur these together.

## 2. Update the brief first

Every pivot must start by updating the repo’s truth source:

- `docs/spec/CANONICAL-BRIEF.md`

Add a dedicated section:

- `## Pivot History`
- date
- requested change
- what assumptions changed
- what remained stable
- whether this is safe repair, design change, or architecture change

That prevents drift between the old scaffold intent and the new repo direction.

## 3. Run pivot-impact diagnosis

Before regenerating anything, Scafforge should determine what surfaces are now stale.

The diagnosis should answer:

- Are local skills stale?
- Are agent prompts stale?
- Is team topology stale?
- Are workflow docs stale?
- Are current tickets now contradictory?
- Do acceptance criteria now reach into later-ticket scope?
- Are restart surfaces lying about the current route?
- Does the active ticket still make sense?

This should be a dedicated diagnosis mode, not just generic audit.

## 4. Partition affected surfaces

Scafforge should explicitly label surfaces as:

- `stable`
- `needs_regeneration`
- `needs_repair`
- `needs_ticket_follow_up`
- `needs_human_decision`

Without that partition, pivots turn into broad, fuzzy repo surgery.

## 5. Freeze or supersede invalid tickets

When a pivot invalidates old work, Scafforge should not leave the old ticket graph half-alive.

Required behavior:

- supersede tickets that no longer fit the design
- reopen tickets whose trust is invalidated
- create follow-up tickets where old work partially survives
- update `source_ticket_id`, `follow_up_ticket_ids`, and `source_mode`
- prevent acceptance criteria from silently spanning pre-pivot and post-pivot assumptions

## 6. Rebuild only the affected layers

Pivoting should be surgical.

### For a small feature
Only refresh:
- brief
- backlog
- workflow-state alignment
- verification

### For a design change
Refresh:
- brief
- local skills
- affected agents
- prompts
- backlog
- verification

### For an architecture change
Refresh:
- brief
- managed workflow docs if needed
- local skills
- team topology
- prompts
- backlog
- restart surfaces
- verification
- handoff

## 7. Require post-pivot verification

A pivot is not complete when the files were changed.

It is complete when Scafforge proves:

- one clear foreground ticket exists
- acceptance criteria are still scope-isolated
- bootstrap / validation commands still make sense
- restart surfaces match canonical state
- no stale prompts or placeholder skills remain
- the repo still exposes one legal next move

---

## Exact repository changes required to support pivoting properly

## P0 — Add `pivot-update` as a first-class run type

### Files
- `skills/skill-flow-manifest.json`
- `skills/scaffold-kickoff/SKILL.md`

### Instruction
Add a new canonical run type for existing repos whose design or feature set changed part way through work.

### Done when
The user can say “change the design” or “add this feature” and Scafforge routes into one explicit flow instead of forcing manual mode selection.

## P0 — Add pivot classification to kickoff

### Files
- `skills/scaffold-kickoff/SKILL.md`

### Instruction
Add a new decision-tree branch for:
- feature add
- design change
- architecture change

### Done when
Kickoff can distinguish backlog growth from a true design pivot.

## P0 — Add a pivot-impact diagnosis mode

### Files
- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-audit/scripts/audit_repo_process.py`

### Instruction
Add a mode that determines what changed because of the pivot and which surfaces are now stale.

### Done when
Audit can emit:
- affected surfaces
- unchanged surfaces
- invalid ticket graph edges
- stale skills/agents/prompts
- required regeneration stages
- post-pivot ticket actions

## P0 — Add ticket invalidation / supersede rules for pivots

### Files
- `skills/ticket-pack-builder/SKILL.md`
- related generated ticket tooling/templates from `repo-scaffold-factory`

### Instruction
Teach Scafforge to:
- supersede invalid tickets
- reopen tickets when trust changed
- split surviving work into follow-up tickets
- preserve source lineage cleanly

### Done when
A pivot cannot leave old tickets pretending to still fit the new design.

## P0 — Require post-pivot verification before handoff

### Files
- `skills/skill-flow-manifest.json`
- `skills/scaffold-kickoff/SKILL.md`
- `skills/handoff-brief/SKILL.md`
- `scripts/validate_scafforge_contract.py`
- `scripts/smoke_test_scafforge.py`

### Instruction
A pivot flow must run deterministic verification before publishing handoff.

### Done when
No pivot can finish on handoff text alone.

## P1 — Add pivot history to canonical brief

### Files
- canonical brief schema references and any scaffolded spec templates

### Instruction
Add a required pivot/change log section so the repo remembers what changed and why.

### Done when
Midstream design changes are part of repo truth, not just chat history.

## P1 — Add a “stale surface map” output

### Files
- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-repair/SKILL.md`
- repair execution record surfaces

### Instruction
Emit a machine-readable map of:
- stale
- regenerated
- stable
- escalated
- ticket-follow-up-required

### Done when
Pivot repair becomes explainable and bounded.

## P1 — Create a pivot-safe restart surface

### Files
- restart-surface generation logic
- `START-HERE.md`
- `.opencode/state/latest-handoff.md`
- `.opencode/state/context-snapshot.md`

### Instruction
Add explicit fields:
- `pivot_in_progress`
- `pivot_class`
- `pivot_changed_surfaces`
- `pre_pivot_ticket_superseded`
- `post_pivot_foreground_ticket`

### Done when
Resume cannot mistake a repo mid-pivot for a stable repo.

## P1 — Separate product repo from audit/archive exhaust

### Files
- repo structure and output policy

### Instruction
Do not keep large historical audit/archive churn inside the main product repo by default.

### Done when
Scafforge the product repo stays focused on:
- skills
- scripts
- templates
- references
and not accumulated diagnosis exhaust from subject repos.

---

## Operator instructions: what to do today with the current Scafforge

Until the repo gains a clean pivot flow, use this practical runbook.

## Small feature add

Use this when:
- no major architecture changes
- existing workflow still fits
- existing validation commands still make sense

Do this:

1. update `docs/spec/CANONICAL-BRIEF.md`
2. describe the new feature and acceptance clearly
3. run backlog refinement
4. create new small tickets rather than enlarging one already in flight
5. align manifest, board, and workflow state
6. verify before handoff

## Design pivot

Use this when:
- feature changes assumptions
- acceptance boundaries changed
- some old tickets no longer fit

Do this:

1. update `docs/spec/CANONICAL-BRIEF.md`
2. mark the change as a pivot, not just backlog growth
3. run diagnosis first
4. identify stale surfaces
5. run safe repair where the workflow layer drifted
6. regenerate skills/agents/prompts if affected
7. supersede or reopen invalid tickets
8. rebuild the backlog
9. verify before handoff

## Architecture pivot

Use this when:
- service boundaries changed
- framework/runtime assumptions changed
- infra or execution model changed
- team topology assumptions changed

Do this:

1. update the canonical brief
2. run full pivot-impact diagnosis
3. refresh safe workflow surfaces
4. regenerate local skills
5. regenerate team topology
6. re-harden prompts
7. replace invalid ticket graph sections
8. verify deterministically
9. publish handoff only after the above converges

---

## Acceptance criteria for “pivot-safe Scafforge”

Scafforge should not be considered pivot-safe until all of these are true:

- a user can request a midstream design change without manually choosing internal repair modes
- the system classifies pivot type explicitly
- the canonical brief records pivot history
- the audit can map stale versus stable surfaces
- invalid tickets are superseded or reopened cleanly
- backlog refinement after a pivot is deterministic
- restart surfaces expose pivot state truthfully
- post-pivot verification is mandatory
- handoff cannot be published from stale workflow assumptions
- the repo still exposes one clear legal next move after the pivot

---

## Final judgement on pivot difficulty

**As Scafforge stands now:**

- **small feature pivots** are workable
- **medium design pivots** are awkward but manageable
- **architecture pivots** are too manual and too spread across different skills
- **clean pivot UX does not yet exist as a first-class Scafforge capability**

So the answer is:

**pivoting is not impossible, but it is currently more difficult than it should be, because Scafforge treats it as a combination of refine + audit + repair + regeneration rather than as one canonical flow.**

---

## Repo evidence used for this section

Based on the live repo at commit `7e2040f817e3578c6eec2a628b84cfdc0f5cc5a8`, especially:

- `skills/skill-flow-manifest.json`
- `skills/scaffold-kickoff/SKILL.md`
- `skills/ticket-pack-builder/SKILL.md`
- `skills/scafforge-repair/SKILL.md`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
