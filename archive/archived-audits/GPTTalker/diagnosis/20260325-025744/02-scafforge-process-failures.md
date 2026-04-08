# Scafforge Process Failures

## Scope

- Subject repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-25T02:57:44Z`
- Scope of this report: map each validated finding to the workflow layer, managed surface, or source layer that allowed it through

## Failure Map

### PF-BOOT001

- Linked finding id: `F-BOOT001`
- Implicated surface: Scafforge-managed bootstrap tool in `.opencode/tools/environment_bootstrap.ts`
- Ownership class: Scafforge package defect
- How the workflow allowed the issue through: the managed bootstrap surface still assumes bare `python3 -m pip` and does not inspect `uv.lock` or a uv-managed `.venv`, so a repo can deadlock before write-capable ticket work even when the project environment is otherwise present.

### PF-EXEC001

- Linked finding id: `F-EXEC001`
- Implicated surface: generated-repo implementation and QA enforcement surfaces
- Ownership class: subject-repo source bug
- How the workflow allowed the issue through: source tickets reached closeout without a required import check on `src.node_agent.main`, so a FastAPI dependency error remained latent until a later audit.

### PF-EXEC002

- Linked finding id: `F-EXEC002`
- Implicated surface: generated-repo implementation and QA enforcement surfaces
- Ownership class: subject-repo source bug
- How the workflow allowed the issue through: QA evidence was treated as sufficient without forcing `pytest --collect-only` and full-suite proof, so collection failure survived into a later wave.

### PF-MODEL001

- Linked finding id: `F-MODEL001`
- Implicated surface: Scafforge-managed model/profile regeneration layer
- Ownership class: Scafforge package defect
- How the workflow allowed the issue through: the process refresh preserved or reintroduced deprecated MiniMax defaults without regenerating the repo-local model profile and the downstream managed metadata together.

### PF-SKILL001

- Linked finding id: `F-SKILL001`
- Implicated surface: project-skill-bootstrap output in scaffold-managed local skills
- Ownership class: Scafforge package defect
- How the workflow allowed the issue through: the skill-regeneration path left baseline placeholder text in a repo that already has a concrete Python/FastAPI stack, so weaker models lose project-specific guidance.

## Ownership Classification

- `F-BOOT001`: `Scafforge package defect`
- `F-EXEC001`: `subject-repo source bug`
- `F-EXEC002`: `subject-repo source bug`
- `F-MODEL001`: `Scafforge package defect`
- `F-SKILL001`: `Scafforge package defect`

## Root Cause Analysis

### F-BOOT001

- Concrete problem: bootstrap fails before work starts on machines that do not expose global `pip`.
- Root cause: the managed bootstrap detector prefers `python3 -m pip` rather than repo-native `uv` or repo-local `.venv` execution.
- Safer target pattern: detect `uv.lock` and uv-managed environments first, then fall back to repo-local `.venv`, and only use global `python3 -m pip` when that is actually the repo contract.

### F-EXEC001

- Concrete problem: the node-agent import path aborts with a FastAPI dependency error.
- Root cause: `src/node_agent/dependencies.py` still injects `app: FastAPI` directly into dependency providers instead of using `request: Request` and reading `request.app.state`.
- Safer target pattern: require import verification before implementation closeout and keep the node-agent dependency surface aligned with valid FastAPI dependency injection.

### F-EXEC002

- Concrete problem: the test suite cannot even collect, so prior QA evidence is not trustworthy as execution proof.
- Root cause: the workflow accepted insufficient execution proof and did not enforce `pytest --collect-only` plus full-suite command output before closure.
- Safer target pattern: implementer and QA prompts must require import proof, collection proof, and full test output before artifacts are accepted.

### F-MODEL001

- Concrete problem: repo-local model guidance is stale and incomplete.
- Root cause: managed refresh replaced deterministic workflow surfaces but did not fully regenerate the project-specific model-profile layer.
- Safer target pattern: regenerate model-operating-profile plus all managed references to the active runtime model together, or escalate if the repo is intentionally pinned by a human decision.

### F-SKILL001

- Concrete problem: a baseline local skill still contains scaffold filler.
- Root cause: project-local skill generation was not completed or was overwritten by a later managed refresh.
- Safer target pattern: ensure every scaffold-managed local skill is replaced with repo-specific content before implementation resumes.
