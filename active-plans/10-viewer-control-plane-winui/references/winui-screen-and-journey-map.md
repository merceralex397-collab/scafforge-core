# WinUI Screen And Journey Map

This document is the Phase 4 exit artifact for plan `10-viewer-control-plane-winui`.

## Shell structure

Use a multi-pane operations shell:

- **left navigation rail** for top-level areas
- **primary content pane** for the selected workflow or dashboard
- **right context pane** for approvals, entity metadata, and quick actions
- **collapsible bottom feed** for live logs and event-stream detail

This keeps long-running operational context visible without turning the app into an embedded terminal-first experience.

## Navigation map

| Screen | Primary purpose | Primary truth domain | Mutation surface |
| --- | --- | --- | --- |
| Forge | start a project from a rough idea or handoff bundle | orchestration intake | yes, through backend intake endpoint |
| Pipeline Overview | active jobs, queue state, review blockers, route health | orchestration jobs | yes, pause/resume/retry via backend |
| Project Detail | per-project phase, PR, review, proofs, ticket summary, restart status | orchestration plus repo truth projection | yes, approvals and escalation via backend |
| Live Feeds | event stream, logs, correlation timeline | event stream | no direct mutation |
| Approvals | pending merge/spec/override/resume approvals | orchestration approvals | yes, approve/reject via backend |
| Router And Providers | provider policy summaries, degraded lanes, recent router decisions | provider/router summaries | yes, policy activation through backend |
| Meta-Loop | package investigations, package-fix PR linkage, revalidation, resume-ready | package investigation state | limited, backend-mediated acknowledgements only |
| Archive Intelligence | historical blockers, trends, and archive-derived summaries | archive/analytics surfaces | no direct mutation |
| Settings | connection profiles, trust enrollment, local storage choices, redaction/export settings | app-local settings | yes, local settings only |

## Read-only vs mutation rules

### Read-only dashboards

- Live Feeds
- Archive Intelligence
- most of Meta-Loop
- repo-truth proof panels inside Project Detail

### Backend-mediated command surfaces

- Forge submission
- pause, resume, retry, escalate controls
- approval and merge-approval actions
- router-policy activation

No screen may contain a "run shell command" mutation path for repo or orchestration changes.

## State-disambiguation rules

The app must visually keep these domains separate:

| Domain | Example objects | Required UI cue |
| --- | --- | --- |
| Downstream orchestration | job, phase, PR, approval queue | job/phase badges and orchestration-state labels |
| Generated repo truth | tickets, workflow state, proof artifacts, restart surfaces | repo-truth badge and canonical-source links |
| Package investigation | diagnosis pack, investigator report, package-fix PR, resume-ready | package-investigation badge and evidence-chain links |
| Provider/router | policy, route kind, degraded-mode marker, recent decision | router badge and lane summary |
| Local safety overlay | stale cache, trust failure, auth expiry | local overlay banner separate from backend status |

The UI must never show a package investigation as if it were just another repo job failure.

## Core journeys

### 1. Start a project from a rough idea

1. Open **Forge**.
2. Enter a rough idea or attach a handoff bundle/reference files.
3. Submit through the backend intake endpoint.
4. Watch the job appear in **Pipeline Overview** with the resulting orchestration state.

### 2. Inspect a downstream repo failure

1. Open **Pipeline Overview** and select the blocked job.
2. In **Project Detail**, view the current phase, PR status, review summary, and repo-truth projection.
3. Open **Live Feeds** or the bottom feed for the correlated event/log trail.
4. If escalation is needed, send a backend-mediated escalation request.

### 3. Approve or reject a merge

1. Open **Approvals** or the approval pane in **Project Detail**.
2. Review PR, proof summary, and current operator mode.
3. Approve or reject through the backend approval endpoint.
4. The resulting state change appears back in orchestration events and review summaries.

### 4. Pause or resume work

1. Select the job in **Pipeline Overview** or **Project Detail**.
2. Use backend-mediated pause or resume controls.
3. If the app is in `read-only-degraded`, show why the control is disabled instead of attempting a fallback mutation path.

### 5. Inspect a package-fix loop

1. Open **Meta-Loop** from the navigation rail.
2. Review the diagnosis kind, triggering findings, investigator report, package-fix PR, and resume-ready signal.
3. Jump to the affected repo or package-fix record without mixing that state into the repo job card.

### 6. Adjust provider or router policy

1. Open **Router And Providers**.
2. Review current policy, degraded mode, and recent router decisions.
3. Apply an allowed policy change through the backend.
4. Confirm the new policy through the event feed and policy summary, not by trusting local optimistic state.

## Meta-loop dependencies on plan 08

The Meta-Loop screen depends on plan `08` exposing at least:

- investigator report references
- package-fix PR or commit linkage
- package commit reference
- `resume-ready.json` with `repo_name`, `package_commit`, `revalidation_audit_timestamp`, `resume_ready`, and `remaining_repo_local_work`

This screen remains **provisional** until plan `08` finalizes the `resume-ready.json` field contract. Before implementation begins in the adjacent WinUI repo, run one lock pass to ensure the UI contract matches the final plan `08` evidence schema.
