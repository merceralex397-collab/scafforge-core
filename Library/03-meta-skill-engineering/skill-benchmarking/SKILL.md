---
name: skill-benchmarking
description: Compare skill variants or before-and-after versions using pass rate, token usage, latency, and qualitative win rate. Use this when choosing between multiple skill variants, measuring whether a refinement helped, or justifying skill maintenance investment. Do not use for evaluating a single skill in isolation (use skill-evaluation) or for building test infrastructure (use skill-testing-harness).
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-benchmarking
  maturity: draft
  risk: low
  tags: [skill, benchmarking]
---

# Purpose
Compares skill variants or before/after versions using quantitative metrics: pass rate, token usage, latency, and qualitative win rate. Produces data to decide which variant to keep, whether refinement helped, or if skill is worth maintaining.

# When to use this skill
Use when:
- Multiple skill variants exist and one needs choosing
- Skill was refined and impact needs measurement
- User asks "which is better?", "did this help?", "benchmark these"
- Periodic audit to cull underperformers
- Justifying skill maintenance investment

Do NOT use when:
- No variants to compare (use `skill-evaluation` for single skill)
- Building test harness (use `skill-testing-harness`)
- Debugging why skill fails (use `skill-refinement`)
- Single quick check, not systematic comparison

# Operating procedure
1. **Define comparison**:
   - What variants? (A vs B, before vs after, skill vs no-skill)
   - What metrics matter?
   - Minimum sample size? (recommend N≥10 per variant)
2. **Select benchmark cases**:
   - Use evals/ cases if exist
   - Cover: typical, edge, adversarial
   - Same cases for all variants
3. **Collect quantitative metrics**:
   - **Pass rate**: % meeting acceptance criteria
   - **Token usage**: Avg input + output tokens
   - **Latency**: Time to complete (if measurable)
   - **Routing accuracy**: Precision and recall
4. **Collect qualitative metrics** (blind comparison):
   - Present outputs without labels
   - Rate: Which better? (A/B/Tie)
   - Calculate win rate
5. **Statistical analysis**:
   - Pass rate: Significant difference? (chi-squared)
   - Continuous metrics: Meaningful? (>10% = meaningful)
   - Win rate: Different from 50%?
6. **Produce benchmark report**:
   - Summary table
   - Statistical notes
   - Recommendation

# Output defaults
```
## Benchmark: [Skill A] vs [Skill B]

### Summary
| Metric | A | B | Winner |
|--------|---|---|--------|
| Pass Rate | 85% | 92% | B |
| Avg Tokens | 1200 | 980 | B |
| Win Rate | 35% | 65% | B |

### Detailed Results
[By category if applicable]

### Statistical Notes
- Pass rate difference: p=X
- Win rate: significantly > 50%? Yes/No

### Recommendation
**Keep [winner]**, [deprecate/archive] [loser].
Rationale: [why]
```

# References
- https://docs.anthropic.com/en/docs/test-and-evaluate/eval-overview — Anthropic eval guidance
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skills overview
- Skill evals/ directories for test cases

# Failure handling
- **Not enough test cases**: Note results preliminary; minimum N=10
- **Metrics too close**: Keep simpler/smaller as tiebreaker
- **Variants serve different purposes**: Don't force winner; document when each appropriate
- **Can't blind comparison**: Note bias risk
