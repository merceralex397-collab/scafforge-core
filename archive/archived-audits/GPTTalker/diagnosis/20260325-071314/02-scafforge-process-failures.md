# Scafforge Process Failures

## Scope

- Subject repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-25T07:13:14Z`
- Failure mapping scope: validated findings from Report 1 only

## Failure Map

### PF-01

- linked Report 1 finding id: `R1-F1`
- implicated surface:
  - generated repo managed surface `.opencode/tools/smoke_test.ts`
  - derived restart surfaces `START-HERE.md`, `.opencode/state/latest-handoff.md`, `.opencode/state/context-snapshot.md`
- ownership classification: generated-repo managed-surface drift
- why it counts as a process failure:
  - the repo is a Python project with `uv.lock`, `.venv`, and explicit ticket acceptance criteria that require repo-managed commands
  - the managed smoke-test tool still selects `python3 -m pytest`, so the stage gate records a FAIL unrelated to the actual ticket acceptance commands
  - the derived handoff text then narrows the blocker to the smoke-test tool and overstates downstream readiness

### PF-02

- linked Report 1 finding id: `R1-F2`
- implicated surface:
  - diagnosis/audit flow
  - derived handoff/restart surfaces
- ownership classification: Scafforge package defect
- why it counts as a process failure:
  - the packaged `audit_repo_process.py` run emitted `0` findings even though the repo still reproduces a failing full suite and an active smoke-test-stage blocker
  - the current audit surface is therefore too narrow to catch execution failures that matter to active-ticket closeout
- note:
  - this ownership is an inference from the behavior of the bundled audit script, not from a package-repo diff

## Ownership Classification

- `R1-F1`: generated-repo managed-surface drift
- `R1-F2`: Scafforge package defect
- `R1-F3`: subject-repo source bug
- `R1-F4`: subject-repo source bug
- `R1-F5`: subject-repo source bug
- `R1-F6`: subject-repo source bug

## Root Cause Analysis

### PF-01 Root Cause

- the smoke-test tool uses generic language detection but does not honor repo-native Python environment signals such as `uv.lock` or `.venv`
- the closeout narrative then trusted a manually corrected PASS artifact while leaving the managed smoke-test stage unresolved

### PF-02 Root Cause

- the current audit script validates workflow/process smells but does not verify the active ticket against live repo-managed execution evidence
- as a result, the diagnosis pack can say "no findings" while open EXEC tickets and failing suite evidence still exist

### Source-Layer Root Causes Not Attributed To Scafforge

- `R1-F3`: absolute-path rejection was added to `OperationExecutor._validate_path()` ahead of boundary checks, breaking legitimate in-boundary paths
- `R1-F4`: path normalization compares a relative normalized path against an absolute base prefix without joining them first
- `R1-F5`: hub handler and transport signatures drifted from the tested contract
- `R1-F6`: log redaction uses overly broad key matching and inconsistent shape/truncation behavior
