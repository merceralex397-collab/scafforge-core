---
name: skill-testing-harness
description: >-
  Build trigger tests, output-format tests, and baseline comparisons for a
  skill's evals/ directory. Use when: "create tests for this skill", "set up
  evals", "build a test harness", a new skill needs test coverage, or a skill
  lacks an evals/ directory. Do not use for running existing tests (use
  skill-evaluation), comparing skill variants (use skill-benchmarking), or
  updating tests that already exist (edit directly).
license: Apache-2.0
compatibility:
  clients: [opencode, copilot, codex, gemini-cli, claude-code]
---

# Purpose

Build test infrastructure for a skill: trigger tests (positive and negative JSONL cases), output-format tests, and baseline comparisons. Enables repeatable evaluation during development and refinement.

# When to use

- User says "create tests for this skill", "set up evals", "build a test harness"
- New skill needs test coverage
- Skill lacks an evals/ directory or test fixtures
- Skill refinement requires regression tests

# Do NOT use when

- Running existing tests → `skill-evaluation`
- Comparing skill variants → `skill-benchmarking`
- Tests exist and need minor edits → edit directly

# Procedure

## Step 1 — Analyze the target skill

Read the target SKILL.md and extract:
- Trigger signals from the `description` field
- Positive cases from "When to use" section
- Negative cases from "Do NOT use when" section
- Expected output format from output contract
- Quality criteria from procedure steps

## Step 2 — Create trigger-positive.jsonl

File: `evals/trigger-positive.jsonl`

Each line is a JSON object for a prompt that SHOULD activate the skill. Include 8–15 cases covering core use cases, edge cases, and paraphrasings.

```jsonl
{"prompt": "Create a new skill for handling PDF extraction", "expected": "trigger", "category": "core", "notes": "Direct request matching primary use case"}
{"prompt": "I need a reusable procedure for database migrations", "expected": "trigger", "category": "indirect", "notes": "Implicit skill creation — repeated task pattern"}
{"prompt": "Can you make a skill that handles our deploy workflow?", "expected": "trigger", "category": "paraphrase", "notes": "Casual phrasing"}
{"prompt": "Package this workflow as a skill for the team", "expected": "trigger", "category": "edge", "notes": "Packaging intent implies creation first"}
```

| Field | Required | Description |
|-------|----------|-------------|
| `prompt` | Yes | User message that should trigger the skill |
| `expected` | Yes | Always `"trigger"` for positive cases |
| `category` | Yes | One of: `core`, `indirect`, `paraphrase`, `edge` |
| `notes` | No | Why this case should trigger |

## Step 3 — Create trigger-negative.jsonl

File: `evals/trigger-negative.jsonl`

Each line is a JSON object for a prompt that should NOT activate the skill. Include 8–15 cases covering adjacent skills, out-of-scope tasks, and common confusion.

```jsonl
{"prompt": "Fix the trigger description on this skill", "expected": "no_trigger", "better_skill": "skill-trigger-optimization", "notes": "Trigger fix, not test creation"}
{"prompt": "Run the existing eval suite", "expected": "no_trigger", "better_skill": "skill-evaluation", "notes": "Running tests, not building them"}
{"prompt": "Compare these two skill variants", "expected": "no_trigger", "better_skill": "skill-benchmarking", "notes": "Benchmarking, not test infrastructure"}
{"prompt": "Write a Python function to parse JSON", "expected": "no_trigger", "better_skill": null, "notes": "General coding, not skill engineering"}
```

| Field | Required | Description |
|-------|----------|-------------|
| `prompt` | Yes | User message that should NOT trigger the skill |
| `expected` | Yes | Always `"no_trigger"` for negative cases |
| `better_skill` | Yes | Correct skill name, or `null` if none matches |
| `notes` | No | Why this case should not trigger |

## Step 4 — Create output tests

File: `evals/output-tests.jsonl`

Each line defines a prompt with expected output characteristics.

```jsonl
{"prompt": "Create trigger tests for skill-authoring", "expected_files": ["evals/trigger-positive.jsonl", "evals/trigger-negative.jsonl"], "required_patterns": ["\"expected\": \"trigger\"", "\"expected\": \"no_trigger\""], "forbidden_patterns": ["TODO", "placeholder"], "min_cases": 5}
{"prompt": "Build a full test harness for the pdf-extraction skill", "expected_files": ["evals/trigger-positive.jsonl", "evals/trigger-negative.jsonl", "evals/output-tests.jsonl", "evals/README.md"], "required_patterns": ["\"category\""], "forbidden_patterns": [], "min_cases": 8}
```

## Step 5 — Create test fixtures (if needed)

Directory: `evals/fixtures/`

Only create fixtures when the skill processes files or external data: sample inputs, mock data for deterministic testing, expected output examples.

## Step 6 — Create evals README

File: `evals/README.md`

```markdown
# Eval Suite for [skill-name]

## Files
| File | Purpose | Case Count |
|------|---------|------------|
| trigger-positive.jsonl | Prompts that SHOULD trigger | N |
| trigger-negative.jsonl | Prompts that should NOT trigger | N |
| output-tests.jsonl | Output format/content validation | N |

## Running
- Trigger tests: Feed each prompt to router, verify trigger/no_trigger matches expected
- Output tests: Run skill on each prompt, verify files/patterns/counts

## Adding Cases
Append new JSON lines to the appropriate .jsonl file. Follow the field schema:
- trigger-positive: prompt, expected ("trigger"), category, notes
- trigger-negative: prompt, expected ("no_trigger"), better_skill, notes
```

# Output contract

```
evals/
├── README.md              # How to run and extend tests
├── trigger-positive.jsonl # 8–15 should-trigger cases
├── trigger-negative.jsonl # 8–15 should-not-trigger cases
├── output-tests.jsonl     # Output validation cases
└── fixtures/              # Optional test data
```

All JSONL files use one JSON object per line, newline-delimited.

# Failure handling

- **No clear triggers in description**: Cannot write trigger tests — flag for `skill-trigger-optimization` first
- **Output format undefined**: Cannot write output tests — flag for `skill-improver` to add output contract
- **Too few distinct trigger phrases**: Minimum 5 positive, 5 negative; if the skill is too narrow, merge via `skill-variant-splitting` or widen the trigger set
- **Skill too complex for single harness**: Split into sub-capabilities with separate JSONL files per capability
- **No comparable baseline**: Skip baseline comparison; focus on trigger accuracy and output format compliance
