# GPTTalker Fixture Corpus

These fixtures are the curated replacement for the former `out/scafforge audit archive/` and `scafforgechurnissue/` trees.

They preserve the deadlock families that repeatedly surfaced in GPTTalker without keeping the full operational exhaust in the product repo.

Each fixture family includes:

- a stable slug
- the original archive-origin paths for provenance
- the invariant or regression family it represents
- the current Scafforge coverage that is expected to protect against recurrence

The current corpus includes dedicated greenfield families for bootstrap layout drift, host blockage, planning and implementation contract drift, verdict routing drift, and resume surface drift, alongside the repair and pivot regressions.

Use `tests/fixtures/gpttalker/index.json` as the canonical index.
