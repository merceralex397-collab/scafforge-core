---
name: scaffold-kickoff
description: Orchestrate the full spec-to-repo kickoff flow for greenfield or early-stage projects. Use when a host agent needs one clear starting point that reads messy project inputs, normalizes requirements, scaffolds the repository, generates the ticket system, bootstraps the OpenCode team, creates project-local skills, and writes the first handoff documents.
---

# Scaffold Kickoff

Use this as the default entrypoint for repo planning and scaffold creation.

## Workflow

1. Load `spec-pack-normalizer` and convert the messy input repo, notes, or spec pack into a canonical brief, source-of-truth map, and batched ambiguity packet.
2. Resolve blocking ambiguities before detailed ticketing. Do not guess at provider, model, stack, runtime, or other materially divergent choices.
3. Confirm the project name, slug, destination path, agent prefix, provider, primary model, and optional helper model. Never bury a model choice as a silent default.
4. Use `repo-scaffold-factory` to generate the repo skeleton, docs, `opencode.jsonc`, `.opencode/` tree, and base state surfaces.
5. Use `ticket-pack-builder` in bootstrap mode to generate the queue, including an implementation-ready first execution wave and explicit blocked or decision tickets where ambiguity remains.
6. Use `project-skill-bootstrap` in foundation mode, then add synthesis only where project evidence is good enough to justify it.
7. Use `agent-prompt-engineering` when weak-model rails, anti-doom-loop behavior, or stage contracts need project-specific hardening.
8. Run `repo-process-doctor` against the freshly generated repo. Audit first, then allow safe repairs if drift is already visible and not explicitly blocked.
9. Use `handoff-brief` to refresh `START-HERE.md` and the restart surface before stopping.
10. Leave `review-audit-bridge` for later implementation and QA cycles.

## Required outputs

- a canonical brief that separates facts, assumptions, and open questions
- a decision packet that records blocking vs non-blocking ambiguities
- a scaffolded repo with `README.md`, `AGENTS.md`, `START-HERE.md`, docs, and tickets
- a structured truth hierarchy with clear ownership for facts, queue state, transient workflow state, artifacts, provenance, and handoff
- the OpenCode agent, command, tool, plugin, and local skill layer
- a process audit confirming the generated repo did not drift into raw-file stage control
- a short handoff surface that another machine or session can resume from

## Rules

- Prefer this umbrella flow for greenfield work instead of manually starting with the lower-level scaffold skills.
- The default output profile is full orchestration, but heavier packs should stay thin or lazy-activated unless the project already justifies deeper specialization.
- Keep the generated docs and prompts weak-model friendly: short sections, explicit steps, and obvious source-of-truth files.
- If the repo already exists and only needs the OpenCode layer, switch to `opencode-team-bootstrap` instead of forcing a full scaffold reset.
- When the stack is still unknown, keep the scaffold framework-agnostic and record the unresolved choices in the canonical brief.
- Do not let `ticket-pack-builder` fabricate implementation detail for unresolved major decisions. Convert them into explicit blocked or decision tickets instead.
- Preserve exact model/provider strings and project names when the source material specifies them.
- Do not ship a repo-local workflow until a doctor pass confirms queue state, approval state, and stage artifacts are separated cleanly.

## Hand-off points

- Use `ticket-pack-builder` only when the initial ticket set needs expansion or standardization after the first scaffold.
- Use `opencode-team-bootstrap` when the repo already has docs and tickets but still needs `.opencode/`.
- Use `review-audit-bridge` once implementation starts and the project needs deterministic review, QA, or audit passes.

This skill is intentionally thin. Its job is to make the starting sequence obvious and route into the existing modular skills.

`repo-scaffold-factory` remains the only source of truth for scaffold template assets. This skill should orchestrate that flow, not fork template logic.
