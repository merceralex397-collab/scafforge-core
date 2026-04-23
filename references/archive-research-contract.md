# Archive Research Contract

This document freezes the minimum archive contract for researcher-facing evidence and fault routing.

## Storage rule

Archive bundles must be organized by:

- project key
- category
- agent lane
- provider/model/runtime
- capture timestamp or run id

## Minimum categories

- logs
- database
- validation
- review
- audit
- repair
- research
- exports

## Research paths

### Path 1: Direct Scafforge fault

Use when the evidence indicates a defect in Scafforge itself.

Required routing:

1. archive the evidence
2. open or update a Scafforge issue
3. send the issue-linked bundle to the investigator lane
4. preserve links to any resulting package fix and downstream revalidation

### Path 2: Skill fault

Use when the evidence indicates a weak, missing, or wrongly triggered skill.

Required routing:

1. archive the evidence
2. send the bundle to the meta-skill-engineer lane
3. either improve the skill, send verified findings to the Scafforge fixer lane, or promote a permanent library skill in `scafforge-core`

## Non-goal

The archive is not generated repo canonical truth. It is a retained evidence and research surface.
