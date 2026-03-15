# Contributing

## Prerequisites

- Node.js 20 or newer
- Python 3.10 or newer
- npm (ships with Node.js)

Install repo dependencies if the package grows them later:

```bash
npm install
```

## Validation commands

Run both checks before opening a pull request:

```bash
npm run validate:contract
npm run validate:smoke
```

- `validate:contract` checks the core package contract, skill flow, and required scaffold surfaces.
- `validate:smoke` renders fresh scaffold outputs and verifies the expected files and directories exist.

## Running the doctor

Audit the current repository with the doctor script:

```bash
python skills/repo-process-doctor/scripts/audit_repo_process.py . --format both
```

Use the findings to decide whether follow-up work belongs in audit, propose-repair, or apply-repair mode.

## Safely modifying the scaffold

Scafforge is the generator package, not the generated project. Keep changes scoped accordingly.

- Prefer editing the source skills, references, and root package surfaces instead of generated output snapshots.
- Treat `skills/repo-scaffold-factory/assets/project-template/` as the canonical generated template. When you change it, keep related docs and checklist-driven expectations aligned.
- Avoid mixing host-adapter changes with core scaffold or workflow-contract changes unless the task explicitly calls for both.
- Do not commit Python cache files, virtual environments, editor settings, or local environment files.
- After changing scaffold or template behavior, rerun both validation commands so the render path and contract stay in sync.

## Pull request checklist

- Keep changes surgical and within the requested lane.
- Update directly related documentation when behavior changes.
- Include the validation commands you ran and note any pre-existing failures that are unrelated to your change.
