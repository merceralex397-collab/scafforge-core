# Bootstrap Dependency-Layout Drift

This family captures the GPTTalker cases where generated bootstrap guidance assumed one dependency layout and then dead-ended when the repo used a different layout or repo-local executable path.

Archive origin:

- `out/scafforge audit archive/GPTTalker Logs and Audits/gpttalker agent logs/bootstrapfail.md`
- `out/scafforge audit archive/GPTTalker Logs and Audits/gpttalker agent logs/smoketestbroken.md`

What mattered:

- bootstrap guidance kept falling back to the wrong executable or install path
- the generated repo needed to classify missing executables as host-surface failures, not generic repo breakage
- weaker agents were getting blocked before one clear legal first move was established

Current protection:

- generated bootstrap and smoke tools are dependency-layout aware
- host-surface classification is execution-backed in smoke coverage
- the greenfield integration test verifies a fresh repo becomes immediately continuable once project-local placeholder skill drift is removed
