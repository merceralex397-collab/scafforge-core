# Failure Taxonomy

## Canonical failure families

| Family | Observable signal | Likely package-owned cause | Likely repo-local cause | Evidence artifact | Default routing |
| --- | --- | --- | --- | --- | --- |
| Build and load breakers | Parse failure, missing autoload, broken `extends`, headless load failure | Scaffold or validator did not gate parse/load truth before handoff | Broken script, missing base class, missing autoload target | current-cycle execution proof or static audit finding (`EXEC-GODOT-001/003/004/009`) | block handoff immediately |
| Resource linkage failures | Broken `res://` or `ext_resource` target, missing import dependency | Template or proof ladder never checked resource integrity on the shipped tree | Downstream repo deleted or renamed a resource without updating manifests | scene/resource audit evidence (`EXEC-GODOT-002`) | block handoff immediately |
| Renderer/profile drift | `project.godot` renderer path contradicts declared mobile/export target | Stack guidance or validator let repo guidance and config diverge | Repo changed renderer settings without reconciling stack/export contract | `project.godot` plus provenance/brief evidence (`EXEC-GODOT-014`) | repo-local follow-up plus package prevention work |
| Input-map drift | malformed input action payload, invalid deadzone, missing events array | No deterministic config audit for interaction-critical input state | Repo edited `project.godot` input actions into an invalid shape | `project.godot` input section (`EXEC-GODOT-015`) | block handoff immediately |
| Viewport/layout truth failures | missing or wrong stretch mode for 2D viewport-first repo, first screen no longer trustworthy | Handoff proof never checked first-screen configuration truth | Repo changed display/stretch config without validating presentation | `project.godot` display section (`EXEC-GODOT-013`) | block handoff immediately |
| Completion-truth failures | START-HERE or handoff says ready while proof is missing, failed, or contradicted | Restart publication outranks proof state or smoke evidence | Repo manually edited restart surfaces without republishing canonical truth | handoff proof state plus restart surfaces (`WFLOW035`, `EXEC-GODOT-006`) | package defect; may coexist with repo-local follow-up |

## Human-facing labels on top of disposition classes

- `package defect` -> `managed_blocker`
- `repo-local defect` -> `source_follow_up`
- `mixed defect` -> both package-managed and repo-local outputs present in the same diagnosis pack; do **not** create a new disposition class

## Proven source anchors

- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVA.md`
- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVB.md`
- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVC.md`
- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVD.md`
- `../../_source-material/asset-pipeline/assetsplanning/spinner.md`

## Planning consequence

No autonomy or scale-up work should bypass these proof layers. If Scafforge cannot distinguish package defect, repo-local defect, and mixed defect with named evidence, it is not ready to trust a larger autonomous loop.
