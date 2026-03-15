# Scafforge Review Notes

> Status note:
> These notes captured the critical review before the current contract-hardening pass. The main recommendations here — one-cycle scaffolding, bootstrap ticket generation, controlled local-skill synthesis, and stronger workflow discipline — are now implemented in the current baseline and retained here as rationale.

## Executive verdict

The package direction is good, but the desired setup needs a firmer contract.

Right now the strongest improvement is not “add more skills.” It is:

- make the default path a true one-cycle scaffold run
- make ticket generation part of that first run
- keep local skill synthesis controlled and evidence-based
- avoid turning public skill search into random skill ingestion

That combination would make the system sharper, not just bigger.

## Critical review of the current idea set

## 1. One-cycle generation is the right goal

This is a strong idea.

If a greenfield scaffold requires a second remembered pass to become fully usable, then the default flow is too loose.

A scaffold package like this should leave behind a repo that already has:
- the structural docs
- the OpenCode layer
- the initial ticket pack
- the local workflow pack
- the restart surface

If those are split into “base now, maybe enrich later,” weaker models are more likely to stop halfway.

### Verdict
Good idea. Keep it.

## 2. Folding ticket generation into the first run is also right

This is another good correction.

The base scaffold can still own the ticket directories and starter files, but the ticket specialist should run in **bootstrap mode** during the first cycle so the resulting queue is not half-born.

### Risk
If both the scaffold root and ticket builder think they own the same truth, you will get overlap and drift.

### Fix
Make the base scaffold own the raw structure and make `ticket-pack-builder` own ticket detail and refinement logic, including bootstrap-mode population.

### Verdict
Good idea, but only if ownership is explicit.

## 3. Project-local skill synthesis is promising, but dangerous if left loose

This is the idea that needs the most discipline.

### Why it is good

A generic base skill pack can only go so far. Real projects usually need a few repo-specific procedural helpers, especially around:
- framework conventions
- testing norms
- migrations
- API contracts
- deployment paths
- stack-specific gotchas

OpenCode is a strong target for this because it supports repo-local rules, skills, commands, tools, and plugins. citeturn375117search2turn375117search0turn375117search12turn375117search18turn375117search8

### Why it can go bad fast

If the synthesis layer is unconstrained, it can easily produce:
- too many local skills
- overlapping local skills
- skills that paraphrase docs instead of encoding procedure
- imported public assumptions that do not match the project
- a maintenance swamp where the repo carries stale instruction packs forever

### Verdict
Good idea in principle. High risk if unconstrained.

## 4. Using Vercel Skills as an input source is sensible, but direct import is a bad default

The Vercel skills ecosystem is real, cross-agent, and explicitly built around reusable skill packages and discovery. It includes a `find-skills` helper for automated workflows and works across many agent hosts. citeturn375117search3turn375117search5turn375117search13turn375117search19

That makes it a useful **pattern library**.

But direct import into generated repos is still the wrong default because:
- the discovered skill may solve a nearby but not identical problem
- the discovered skill may assume a different stack or workflow model
- the generated repo may end up with external baggage it does not actually need

### Best use
Use public skills as:
- research inputs
- workflow examples
- naming and packaging references
- validation-pattern hints

Then synthesize a local variant that matches the actual project.

### Verdict
Good source of patterns. Bad default deployment mechanism.

## 5. Synthesizing from project documentation is probably better than public discovery in many cases

This idea is stronger than random skill search, because the docs are often closer to the truth of the project.

Good examples:
- generating a local migrations skill from the actual migration tool docs plus the repo’s migration layout
- generating a test-running skill from the real test runner, fixtures, and CI pattern
- generating an API change skill from the actual OpenAPI contract and release procedure

### Risk
Documentation synthesis becomes bad when it produces reference spam instead of action rails.

A good local skill should answer:
- what to do
- when to do it
- what files matter
- what checks to run
- what failure modes to avoid

It should not become a miniature textbook.

### Verdict
Potentially excellent, but only if the synthesis step extracts procedure rather than copying explanation.

## Recommended model

Use a conservative ladder.

### Step 1: always generate the minimum foundation pack
This keeps workflow tight from the start.

### Step 2: inspect the project itself
Read stack, repo structure, docs, and interfaces.

### Step 3: consult curated internal patterns
Use trusted patterns before public discovery.

### Step 4: consult public skill ecosystems if needed
Only for inspiration, comparison, and workflow patterns.

### Step 5: synthesize a project-local result
Emit a local skill only if it clears a quality bar.

### Step 6: run a doctor-style audit later
Flag local skill sprawl, overlap, drift, or contradiction.

## The biggest design risk

The biggest danger is that Scafforge could drift into becoming a **skill hoarder** instead of a **workflow shaper**.

That would look like:
- too many generated local skills
- too many specialist branches in the flow
- too much public-skill influence
- too little discipline around what is actually core

That path feels powerful at first, then turns into sludge.

## The right bias

Bias toward:
- fewer skills
- sharper boundaries
- stronger one-cycle orchestration
- evidence-based synthesis
- smaller, more procedural local skill packs

Bias against:
- “install more things” as a default answer
- auto-import from the public internet
- broad best-practice dumps inside local skills
- parallel overlapping routes to do the same job

## Bottom line

Your revised instinct is mostly right.

### Strong ideas
- one orchestrated full-cycle scaffold
- ticket generation included in the first pass
- local skill generation as part of the default build
- synthesis from project docs
- public skill ecosystems used as research inputs

### Weak ideas if taken too far
- direct public skill installation
- generating lots of local skills just because it is possible
- treating documentation summaries as local workflow skills
- leaving ownership unclear between scaffold root and specialist refiners

### Final judgment

The setup you want is **good**, but only if it stays disciplined.

The winning version is not:
> “the repo finds and installs lots of skills.”

The winning version is:
> “the repo performs one tight scaffold cycle, then synthesizes a small number of high-fit local skills from evidence.”
