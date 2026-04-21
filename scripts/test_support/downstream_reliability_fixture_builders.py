from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from test_support.repo_seeders import (
    read_json,
    seed_godot_target,
    seed_spinner_layout_failure,
    seed_womanvshorse_failure_family,
    write_json,
)
from test_support.scafforge_harness import ROOT, bootstrap_full


@dataclass(frozen=True)
class FixtureCorpus:
    slug: str
    source_repo: str
    index_path: Path
    contract_path: str


WOMANVSHORSE_CORPUS = FixtureCorpus(
    slug="womanvshorse",
    source_repo="womanvshorse",
    index_path=ROOT / "tests" / "fixtures" / "womanvshorse" / "index.json",
    contract_path=".opencode/meta/womanvshorse-fixture.json",
)

SPINNER_CORPUS = FixtureCorpus(
    slug="spinner",
    source_repo="spinner",
    index_path=ROOT / "tests" / "fixtures" / "spinner" / "index.json",
    contract_path=".opencode/meta/spinner-fixture.json",
)

FIXTURE_CORPORA = (WOMANVSHORSE_CORPUS, SPINNER_CORPUS)


def fixture_index_by_slug(corpus: FixtureCorpus) -> dict[str, dict[str, Any]]:
    payload = read_json(corpus.index_path)
    families = payload.get("families") if isinstance(payload, dict) else None
    if not isinstance(families, list):
        raise RuntimeError(f"{corpus.source_repo} fixture index must define a families list.")
    indexed: dict[str, dict[str, Any]] = {}
    for item in families:
        if isinstance(item, dict) and isinstance(item.get("slug"), str):
            indexed[item["slug"]] = item
    return indexed


def write_fixture_contract(
    dest: Path,
    *,
    corpus: FixtureCorpus,
    slug: str,
    family: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "corpus": corpus.slug,
        "slug": slug,
        "title": family.get("title"),
        "flow": family.get("flow"),
        "invariant_focus": family.get("invariant_focus", []),
        "expected_finding_codes": family.get("expected_finding_codes", []),
        "expected_coverage": family.get("expected_coverage", []),
        "truth_expectations": family.get("truth_expectations", {}),
        "archive_origin": family.get("archive_origin", []),
        "notes": family.get("notes"),
    }
    if extra:
        payload.update(extra)
    write_json(dest / corpus.contract_path, payload)
    return payload


def build_womanvshorse_downstream_breaker(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    seed_godot_target(dest, project_name="WomanVsHorse Fixture")
    seed_womanvshorse_failure_family(dest)
    return write_fixture_contract(
        dest,
        corpus=WOMANVSHORSE_CORPUS,
        slug="downstream-boot-and-config-breaker",
        family=family,
        extra={
            "expected_recommended_next_step": "subject_repo_repair",
            "expected_ticket_routes": ["scafforge-repair", "ticket-pack-builder"],
        },
    )


def build_spinner_layout_truth_regression(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    seed_godot_target(dest, project_name="Spinner Fixture")
    seed_spinner_layout_failure(dest)
    return write_fixture_contract(
        dest,
        corpus=SPINNER_CORPUS,
        slug="layout-truth-regression",
        family=family,
        extra={
            "expected_recommended_next_step": "subject_repo_repair",
            "expected_ticket_routes": ["scafforge-repair", "ticket-pack-builder"],
        },
    )


WOMANVSHORSE_BUILDERS: dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]] = {
    "downstream-boot-and-config-breaker": build_womanvshorse_downstream_breaker,
}

SPINNER_BUILDERS: dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]] = {
    "layout-truth-regression": build_spinner_layout_truth_regression,
}

CORPUS_BUILDERS: dict[str, dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]]] = {
    WOMANVSHORSE_CORPUS.slug: WOMANVSHORSE_BUILDERS,
    SPINNER_CORPUS.slug: SPINNER_BUILDERS,
}

CORPUS_BY_SLUG = {corpus.slug: corpus for corpus in FIXTURE_CORPORA}


def build_fixture_family(corpus_slug: str, slug: str, dest: Path) -> dict[str, Any]:
    corpus = CORPUS_BY_SLUG.get(corpus_slug)
    if corpus is None:
        known = ", ".join(sorted(CORPUS_BY_SLUG))
        raise RuntimeError(f"Unknown downstream fixture corpus `{corpus_slug}`. Known corpora: {known}")
    builders = CORPUS_BUILDERS[corpus_slug]
    if slug not in builders:
        known = ", ".join(sorted(builders))
        raise RuntimeError(f"No {corpus_slug} fixture builder exists for `{slug}`. Known builders: {known}")
    family = fixture_index_by_slug(corpus).get(slug)
    if not isinstance(family, dict):
        raise RuntimeError(f"{corpus_slug} fixture index does not contain family metadata for `{slug}`.")
    if dest.exists():
        shutil.rmtree(dest)
    builders[slug](dest, family)
    return read_json(dest / corpus.contract_path)
