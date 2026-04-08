# Report 3: Scafforge Prevention Actions

These actions describe package-side changes that prevent the same failures from reappearing in future generated repos.

- Make `smoke_test` parse shell-style override commands correctly, treat leading `KEY=VALUE` tokens as environment overrides, and detect transcript-level `ENOENT` override failures as workflow-surface defects instead of generic test failures.

- Tighten generated review and QA guidance so runtime validation and test collection proof exist before closure.

- Teach audit and repair to treat pending backlog process verification as a first-class verification state so repaired repos are not declared clean while historical done tickets remain untrusted.

