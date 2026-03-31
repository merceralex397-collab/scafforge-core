# Placeholder Skill After Refresh

This family captures the cases where deterministic repair refreshed managed workflow surfaces but still left scaffold placeholder skills in place, making the repo look newer while remaining unusable.

Archive origin:

- `scafforgechurnissue/ScafforgeAudits/20260328-115024/manifest.json`
- `out/scafforge audit archive/GPTTalker Logs and Audits/GPTTalkerChurnlogs/20260327-014404/07-scafforge-repair-gap-analysis.md`

What mattered:

- placeholder local skills are generation or repair failure, not an advisory warning
- repair had to stay honest about required repo-local regeneration
- the repo needed a recorded follow-on path instead of an implied “someone should fix prompts and skills later”

Current protection:

- shared verifier emits placeholder-skill failures as hard blockers
- repair cannot report clean if placeholder local skills survive refresh
- the repair integration test keeps that regeneration path explicit
