---
name: skill-testing-harness
description: Create test infrastructure for a skill — trigger tests (positive and negative cases in JSONL format), output format tests, and baseline comparisons. Use this when building evals for a new or refined skill, when a skill lacks an evals/ directory, or when the user says "create tests for this skill", "set up evals", or "build a test harness". Do not use for running existing tests (use skill-evaluation), benchmarking variants (use skill-benchmarking), or when tests exist and just need minor updates.
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-testing-harness
  maturity: draft
  risk: low
  tags: [skill, testing, harness]
---

# Purpose
Creates test infrastructure for a skill: trigger tests (positive and negative), output tests (format and content), and baseline comparisons. The harness enables repeatable evaluation during development and refinement.

# When to use this skill
Use when:
- User says "create tests for this skill", "set up eval", "build test harness"
- New skill being created needs test coverage
- Skill lacks evals/ directory or test fixtures
- Skill refinement requires regression tests

Do NOT use when:
- Running existing tests (use `skill-eval-runner`)
- Evaluating quality (use `skill-evaluation`)
- Benchmarking performance (use `skill-benchmarking`)
- Tests exist and just need updating (edit directly)

# Operating procedure

## Step 1 — Analyze skill to test

Read the target SKILL.md completely and extract:
- Trigger signals from the `description` field
- Positive cases from "When to use" section
- Negative cases from "Do NOT use when" section
- Expected output format from "Output defaults" section
- Quality criteria from the procedure steps

## Step 2 — Create trigger-positive.jsonl

File: `evals/trigger-positive.jsonl`

Each line is a JSON object representing a prompt that SHOULD activate the skill. Include 8-15 cases covering core use cases, edge cases, and paraphrasings.

```jsonl
{"prompt": "Create a new skill for handling PDF extraction", "expected": "trigger", "category": "core", "notes": "Direct request matching primary use case"}
{"prompt": "Write a SKILL.md that helps with code review", "expected": "trigger", "category": "core", "notes": "Explicit skill authoring request"}
{"prompt": "I need a reusable procedure for database migrations", "expected": "trigger", "category": "indirect", "notes": "Implicit skill creation — repeated task pattern"}
{"prompt": "Can you make a skill that handles our deploy workflow?", "expected": "trigger", "category": "paraphrase", "notes": "Casual phrasing"}
{"prompt": "Package this workflow as a skill for the team", "expected": "trigger", "category": "edge", "notes": "Packaging intent implies creation first"}
```

Fields:
| Field | Required | Description |
|-------|----------|-------------|
| `prompt` | Yes | The user message that should trigger the skill |
| `expected` | Yes | Always `"trigger"` for positive cases |
| `category` | Yes | One of: `core`, `indirect`, `paraphrase`, `edge` |
| `notes` | No | Why this case should trigger |

## Step 3 — Create trigger-negative.jsonl

File: `evals/trigger-negative.jsonl`

Each line is a JSON object representing a prompt that should NOT activate the skill. Include 8-15 cases covering adjacent skills, out-of-scope tasks, and common confusion cases.

```jsonl
{"prompt": "Fix the trigger description on this skill", "expected": "no_trigger", "better_skill": "skill-trigger-optimization", "notes": "Trigger fix, not full creation"}
{"prompt": "This skill is broken, the output is wrong", "expected": "no_trigger", "better_skill": "skill-refinement", "notes": "Refinement, not test creation"}
{"prompt": "Run the existing eval suite", "expected": "no_trigger", "better_skill": "skill-evaluation", "notes": "Running tests, not building them"}
{"prompt": "Write a Python function to parse JSON", "expected": "no_trigger", "better_skill": null, "notes": "General coding, not skill engineering"}
{"prompt": "Compare these two skill variants", "expected": "no_trigger", "better_skill": "skill-benchmarking", "notes": "Benchmarking, not test infrastructure"}
```

Fields:
| Field | Required | Description |
|-------|----------|-------------|
| `prompt` | Yes | The user message that should NOT trigger the skill |
| `expected` | Yes | Always `"no_trigger"` for negative cases |
| `better_skill` | Yes | Name of the correct skill, or `null` if no skill matches |
| `notes` | No | Why this case should not trigger |

## Step 4 — Create output tests

File: `evals/output-tests.jsonl`

Each line defines an input prompt with expected output characteristics.

```jsonl
{"prompt": "Create trigger tests for skill-authoring", "expected_files": ["evals/trigger-positive.jsonl", "evals/trigger-negative.jsonl"], "required_patterns": ["\"expected\": \"trigger\"", "\"expected\": \"no_trigger\""], "forbidden_patterns": ["TODO", "placeholder"], "min_cases": 5}
{"prompt": "Build a full test harness for the pdf-extraction skill", "expected_files": ["evals/trigger-positive.jsonl", "evals/trigger-negative.jsonl", "evals/output-tests.jsonl", "evals/README.md"], "required_patterns": ["\"category\""], "forbidden_patterns": [], "min_cases": 8}
```

## Step 5 — Create test fixtures (if needed)

Directory: `evals/fixtures/`

- Sample input files the skill would process
- Mock data for deterministic testing
- Expected output examples for comparison

Only create fixtures when the skill processes files or external data.

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

# Output defaults
```
evals/
├── README.md              # How to run and extend tests
├── trigger-positive.jsonl # 8-15 should-trigger cases
├── trigger-negative.jsonl # 8-15 should-not-trigger cases
├── output-tests.jsonl     # Output validation cases
└── fixtures/              # Optional test data
```

# References
- https://docs.anthropic.com/en/docs/test-and-evaluate/eval-overview — Anthropic eval framework
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skill routing
- https://developers.openai.com/codex/skills — Codex skill format
- JSONL format specification (one JSON object per line, newline-delimited)
- Existing evals/ in similar skills for precedent

# Failure handling
- **Skill has no clear triggers in description**: Cannot write trigger tests — flag for skill-trigger-optimization first
- **Output format undefined in skill**: Cannot write output tests — flag for skill-refinement to add output defaults
- **Too few distinct trigger phrases**: Aim for minimum 5 positive, 5 negative; if skill is too narrow for this, consider whether it should be merged
- **Skill too complex for single harness**: Break into sub-capabilities, create separate JSONL files per capability
- **No comparable baseline exists**: Skip baseline comparison, focus on absolute trigger accuracy and output format compliance
