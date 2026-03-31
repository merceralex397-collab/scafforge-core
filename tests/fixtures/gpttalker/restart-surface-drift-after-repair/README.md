# Restart-Surface Drift After Repair

This family preserves the false-clean post-repair cases where diagnosis output and restart publication disagreed about whether the repo was actually ready to proceed.

Archive origin:

- `scafforgechurnissue/ScafforgeAudits/20260328-131434/manifest.json`
- `scafforgechurnissue/ScafforgeAudits/20260328-135857/manifest.json`

What mattered:

- restart surfaces could not be treated as hand-authored narratives
- `WFLOW010` needed to remain a hard repair-contract failure
- repair-side stage recording itself could not create fresh restart drift

Current protection:

- restart surfaces are regenerated from canonical state during repair and follow-on recording
- repair verification treats restart drift as a hard contract failure
- synthetic restart-drift cases remain in smoke coverage and repair integration
