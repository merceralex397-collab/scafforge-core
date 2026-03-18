---
name: skill-evaluation
description: Evaluate whether a skill routes correctly and produces better output than a baseline — measuring precision, recall, output quality, and win rate against no-skill runs. Use this when validating a new skill before promotion, verifying a refinement worked, or auditing whether an existing skill still adds value. Do not use for building the test harness itself (use skill-testing-harness), benchmarking multiple variants head-to-head (use skill-benchmarking), or debugging a skill that is obviously broken (fix it first with skill-refinement).
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-evaluation
  maturity: draft
  risk: low
  tags: [skill, evaluation]
---

# Purpose
Measures whether a skill is working: does it route correctly (trigger when should, not trigger when shouldn't) and does it produce better output than not having the skill? Produces quantitative evidence that a skill adds value.

# When to use this skill
Use when:
- User says "is this skill working?", "evaluate this skill", "does this help?"
- New skill needs validation before promotion to stable
- Skill was refined and needs verification fix worked
- Comparing skill variants to decide which to keep
- Periodic audit of skill library quality

Do NOT use when:
- Building the test harness/suite (use `skill-testing-harness`)
- Running existing automated evals (use `skill-eval-runner`)
- Benchmarking performance metrics (use `skill-benchmarking`)
- Skill is obviously broken—fix it first (use `skill-refinement`)

# Operating procedure
1. **Define what "working" means for this skill**:
   - **Routing accuracy**: Triggers on positive cases? Not trigger on negative?
   - **Output quality**: Correct, well-formatted, complete?
   - **Baseline comparison**: Better than without skill?
2. **Prepare evaluation inputs**:
   - 5-10 positive trigger cases (should trigger)
   - 5-10 negative trigger cases (should NOT trigger)
   - 3-5 cases for output quality assessment
3. **Run routing evaluation**:
   - Each positive case: Did skill trigger? (target: 100%)
   - Each negative case: Did skill NOT trigger? (target: 100%)
   - Calculate Precision = TP / (TP + FP)
   - Calculate Recall = TP / (TP + FN)
4. **Run output quality evaluation**:
   - For each quality case, run with skill active
   - Assess against rubric:
     - Correct: Solves the problem?
     - Complete: All parts present?
     - Well-formatted: Matches expected format?
     - No hallucination: Claims accurate?
5. **Run baseline comparison** (recommended):
   - Same quality cases, run without skill
   - Compare: Which better? (blind if possible)
   - Calculate win rate: skill wins / total
6. **Synthesize results**:
   - Routing: Pass if precision ≥95%, recall ≥90%
   - Quality: Pass if ≥80% outputs meet rubric
   - Baseline: Pass if skill wins ≥60%
7. **Issue verdict**: Pass / Fail / Needs Work (with specific issues)

# Output defaults
```
## Skill Evaluation: [skill-name]

### Routing Accuracy
| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| Precision | X% | ≥95% | ✓/✗ |
| Recall | X% | ≥90% | ✓/✗ |

**Issues**: [false negatives/positives]

### Output Quality (N cases)
**Score**: X/N pass (Y%)

### Baseline Comparison
**Win rate**: X/N (Y%)

### Verdict: [Pass | Fail | Needs Work]
**Issues**: [list or "None"]
```

# References
- https://docs.anthropic.com/en/docs/test-and-evaluate/eval-overview — Anthropic eval framework
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skills overview
- https://developers.openai.com/codex/skills — Codex skill format
- Skill's evals/ directory if it exists

# Failure handling
- **No eval cases exist**: Create minimum set (3 positive, 3 negative triggers)
- **Can't determine if triggered**: Check client logs or add instrumentation
- **Baseline inconclusive**: Increase sample size or define clearer rubric
- **Routing passes but quality fails**: Route to `skill-refinement`
