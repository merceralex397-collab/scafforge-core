# Report 3: Scafforge Prevention Actions

These actions describe package-side changes that prevent the same failures from reappearing in future generated repos.

- Make generated Python bootstrap manager-aware (`uv` or repo-local `.venv`), classify missing prerequisites accurately, and audit bootstrap deadlocks before routing source remediation.

- Tighten generated review and QA guidance so runtime validation and test collection proof exist before closure.

- Detect deprecated or missing model-profile surfaces, regenerate the repo-local model operating profile, and align model metadata plus agent defaults before development resumes.

