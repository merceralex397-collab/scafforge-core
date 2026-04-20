---
name: spec-pack-normalizer
description: Normalize one or more source specs, notes, pasted chats, and Markdown planning documents into a single canonical brief, decision packet, and constraints summary. Use when given messy or multi-file project requirements that need to become a clean source of truth before scaffolding.
---

# Spec Pack Normalizer

Use this skill to convert messy project inputs into a deterministic brief.

## Procedure

### 1. Scan the workspace for project inputs

Search for spec-like files opportunistically. Look for:
- `*.md` files in the root, `docs/`, `specs/`, `plans/`, `requirements/`, `notes/`, `design/`
- `README.md`, `SPEC.md`, `REQUIREMENTS.md`, `PRD.md`, `DESIGN.md`
- Any directory that looks like it contains project planning material
- Pasted chat logs, informal notes, architecture documents
- API specifications (OpenAPI, GraphQL schemas, etc.)
- Existing code if this is a retrofit (scan for structure, not implementation)

**Before reading any file in full, enumerate ALL spec-like files found.** Record each file path and its approximate line count. This enumeration becomes a required sub-artifact referenced in the canonical brief as `source_spec_inventory`. Only begin extraction (step 2) after the full inventory is recorded.

Read primary specs first, then supporting material. For each file in the inventory, read it fully — not just the first section. Long files must be read in full using paginated reads if necessary.

### 1a. Spec inventory check

After reading all spec files, verify:
- Every file in `source_spec_inventory` was read in full (not just the first portion)
- Every file contributed at least one durable fact, constraint, feature, or explicit non-goal to the extraction in step 2
- If a file contributed nothing after a full read, record it in the brief as a confirmed non-contributing file with a one-line reason (e.g., "duplicate content" or "out of scope")
- If a file's line count suggests you may have only read a partial view, re-read it before proceeding

### 2. Extract durable facts

From everything you read, extract ONLY:
- Durable facts (what is being built, why)
- Constraints (platform, runtime, model, process)
- Desired outcomes (goals)
- Explicit non-goals (what is NOT being built)
- Clearly stated preferences (stack choices, model choices, tooling)

Separate facts from assumptions. Mark each clearly.

### 3. Identify contradictions and ambiguities

- Resolve obvious duplication by preferring the most specific or latest source
- Do NOT smooth over meaningful disagreements — call them out
- Create a **batched decision packet** for all blocking ambiguities:
  - Blocking: choices that materially change implementation (stack, provider, model, architecture)
  - Non-blocking: open questions that don't prevent the first execution wave

### 4. Present the decision packet

Present ALL blocking ambiguities to the user at once. Do not ask one at a time. Include:
- What the ambiguity is
- What the options are (if known)
- What the implications of each option are
- Which option you recommend and why (if you have enough information)

Wait for user decisions before proceeding.

The batched decision packet is a required generation artifact. Record it in `docs/spec/CANONICAL-BRIEF.md` or in a companion markdown file that the canonical brief points to directly.

### 5. Write the canonical brief

Write to `docs/spec/CANONICAL-BRIEF.md` using the schema in `references/brief-schema.md`.

Required sections (all 12 core sections must be present; section 13 is required for consumer-facing repos):

1. **Project Summary** — one paragraph, what and why
2. **Goals** — flat bullet list of desired outcomes
3. **Non-Goals** — flat bullet list of explicit exclusions
4. **Constraints** — platform, runtime, model, process, integration
5. **Required Outputs** — repo structure, docs, agent/tool outputs, validation
6. **Tooling and Model Constraints** — provider, models, runtime, host
7. **Canonical Truth Map** — which file owns which kind of state
8. **Blocking Decisions** — resolved choices from the decision packet
9. **Non-Blocking Open Questions** — things that don't block the first wave
10. **Backlog Readiness** — whether ticketing can proceed, which areas are blocked
11. **Acceptance Signals** — what must be true for the result to be usable
12. **Assumptions** — non-blocking assumptions that don't silently decide major behavior
13. **Product Finish Contract** — required for consumer-facing repos; records deliverable kind, placeholder policy, visual and audio finish bars, content source plan, licensing constraints, and finish acceptance signals

For consumer-facing repos (mobile apps, games, distributed software products), treating the finish contract as optional is a blocking gap, not a non-blocking open question. If the intake material does not resolve whether placeholder or procedural output is acceptable final output, that must become an explicit blocking decision before generation continues.

For internal tools and services, section 13 may be intentionally minimal or explicitly state that no consumer-facing finish bar applies.

### 6. Validate

Verify the brief:
- All 12 core sections are present and non-empty
- Section 13 is present and non-empty for consumer-facing repos; for internal tools, it may state "not applicable" but must not be silently absent
- Facts and assumptions are separated
- The batched blocking-decision packet is written down in the canonical brief or an explicitly referenced companion file
- Blocking decisions are all resolved before greenfield generation continues
- Backlog readiness clearly states whether the first execution wave can be detailed
- Exact product names, provider strings, and model identifiers are preserved

## After this step

Return to `../scaffold-kickoff/SKILL.md` step 2 to resolve ambiguities, then proceed to step 3 only after all blocking decisions are resolved.

## Output contract

Before leaving this skill, confirm all of these are true:
- `docs/spec/CANONICAL-BRIEF.md` exists and contains all 12 core sections plus section 13 when the repo is consumer-facing
- section 13 (Product Finish Contract) is non-empty for consumer-facing repos; for internal tools it explicitly states it does not apply
- the batched decision packet is written into the canonical brief or a directly referenced companion file
- blocking decisions are explicitly separated from non-blocking open questions
- backlog readiness states whether ticket generation may proceed now or which areas remain blocked
- `source_spec_inventory` is recorded in the canonical brief listing all discovered spec files with line counts
- every file in `source_spec_inventory` was fully read and its contributions (or confirmed non-contribution) are documented

## Rules

- Prefer opportunistic intake over rigid required input structure
- Do not invent implementation detail for work that depends on unresolved choices
- Do not let the greenfield path proceed with unresolved blocking decisions
- Keep the brief concise enough for weaker models to load
- Preserve exact names, providers, and model strings when specified

## References

- `references/brief-schema.md` for the output structure
