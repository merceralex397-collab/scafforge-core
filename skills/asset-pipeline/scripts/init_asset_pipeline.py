from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ASSET_SUBDIRS = ("briefs", "models", "sprites", "audio", "fonts", "themes")
DEFAULT_LICENSE_FILTER = ["CC0", "CC-BY", "MIT", "OFL"]
KNOWN_LICENSES = (
    "CC0",
    "CC-BY",
    "CC-BY-SA",
    "MIT",
    "OFL",
    "Apache-2.0",
    "GPL",
    "LGPL",
    "Proprietary",
)


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _read_bootstrap_provenance(repo_root: Path) -> dict[str, object]:
    path = repo_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _contract_value(
    provenance: dict[str, object],
    explicit: str | None,
    field: str,
    fallback: str,
) -> str:
    explicit_text = _normalize_text(explicit)
    if explicit_text:
        return explicit_text
    finish = provenance.get("product_finish_contract")
    if isinstance(finish, dict):
        value = _normalize_text(str(finish.get(field, "")))
        if value:
            return value
    return fallback


def _route_choice(primary: str, *fallbacks: str | None) -> dict[str, str]:
    ordered: list[str] = []
    for candidate in (primary, *fallbacks):
        if candidate and candidate not in ordered:
            ordered.append(candidate)
    payload = {"primary": ordered[0]}
    if len(ordered) > 1:
        payload["fallback"] = ordered[1]
    return payload


def _license_filter(text: str) -> list[str]:
    lowered = text.lower()
    found = [license_name for license_name in KNOWN_LICENSES if license_name.lower() in lowered]
    return found or DEFAULT_LICENSE_FILTER


def _target_platform(stack_label: str) -> str:
    lowered = stack_label.lower()
    if "android" in lowered:
        return "android"
    if "ios" in lowered:
        return "ios"
    if "web" in lowered:
        return "web"
    return "desktop"


def _art_style(stack_label: str, content_source_plan: str) -> str:
    lowered = f"{stack_label} {content_source_plan}".lower()
    if "pixel" in lowered:
        return "pixel-art"
    if "low poly" in lowered or "low-poly" in lowered:
        return "low-poly"
    if "3d" in lowered:
        return "stylized-3d"
    if "2d" in lowered:
        return "stylized-2d"
    return "mixed"


def _infer_routes(stack_label: str, content_source_plan: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    lowered = f"{stack_label} {content_source_plan}".lower()
    uses_blender = any(token in lowered for token in ("blender", ".blend", ".glb", "3d model"))
    uses_free_open = any(
        token in lowered
        for token in (
            "free",
            "open",
            "licensed",
            "kenney",
            "opengameart",
            "quaternius",
            "freesound",
            "google fonts",
            "ofl",
            "cc0",
            "cc-by",
        )
    )
    uses_godot_builtin = any(
        token in lowered
        for token in ("godot", "procedural", "shader", "particle", "theme", "tilemap", "builtin")
    )
    is_3d = any(token in lowered for token in ("3d", "low poly", "low-poly", ".glb", ".blend"))

    routes = {
        "characters": _route_choice(
            "blender-mcp" if uses_blender or is_3d else "free-open" if uses_free_open else "codex-derived",
            "free-open" if uses_free_open else None,
            "godot-builtin" if uses_godot_builtin else None,
        ),
        "environments": _route_choice(
            "godot-builtin" if uses_godot_builtin else "free-open" if uses_free_open else "codex-derived",
            "free-open" if uses_free_open else None,
            "codex-derived",
        ),
        "props": _route_choice(
            "blender-mcp"
            if uses_blender and is_3d
            else "free-open"
            if uses_free_open
            else "godot-builtin"
            if uses_godot_builtin
            else "codex-derived",
            "free-open" if uses_free_open else None,
            "godot-builtin" if uses_godot_builtin else None,
        ),
        "ui": _route_choice(
            "godot-builtin" if uses_godot_builtin else "free-open" if uses_free_open else "codex-derived",
            "free-open" if uses_free_open else None,
            "codex-derived",
        ),
        "audio": _route_choice("free-open" if uses_free_open else "codex-derived"),
        "vfx": _route_choice(
            "godot-builtin" if uses_godot_builtin else "codex-derived",
            "free-open" if uses_free_open else None,
        ),
    }
    brief_targets = [category for category, choice in routes.items() if choice["primary"] == "blender-mcp"]
    return routes, brief_targets


def _pipeline_payload(
    *,
    stack_label: str,
    deliverable_kind: str,
    placeholder_policy: str,
    content_source_plan: str,
    licensing_or_provenance_constraints: str,
    finish_acceptance_signals: str,
) -> dict[str, object]:
    routes, brief_targets = _infer_routes(stack_label, content_source_plan)
    target_platform = _target_platform(stack_label)
    is_mobile = target_platform in {"android", "ios"}
    return {
        "version": 1,
        "stack_label": stack_label,
        "deliverable_kind": deliverable_kind,
        "placeholder_policy": placeholder_policy,
        "art_style": _art_style(stack_label, content_source_plan),
        "target_platform": target_platform,
        "content_source_plan": content_source_plan,
        "licensing_or_provenance_constraints": licensing_or_provenance_constraints,
        "finish_acceptance_signals": finish_acceptance_signals,
        "routes": routes,
        "brief_targets": brief_targets,
        "provenance_tracking": True,
        "license_filter": _license_filter(licensing_or_provenance_constraints),
        "texture_max_size": 1024 if is_mobile else 2048,
        "model_max_tris": 5000 if is_mobile else 12000,
        "initialized_by": "skills/asset-pipeline/scripts/init_asset_pipeline.py",
    }


def _bootstrap_metadata(pipeline: dict[str, object]) -> dict[str, object]:
    routes = pipeline.get("routes", {})
    primary_routes = {
        category: choice.get("primary")
        for category, choice in routes.items()
        if isinstance(choice, dict) and isinstance(choice.get("primary"), str)
    }
    suggested_agents: list[str] = []
    suggested_skills: list[str] = []
    if "blender-mcp" in primary_routes.values():
        suggested_agents.append("blender-asset-creator")
        suggested_skills.extend(["asset-description", "blender-mcp-workflow"])
    if "free-open" in primary_routes.values():
        suggested_agents.append("asset-sourcer")
    if "godot-builtin" in primary_routes.values():
        suggested_agents.append("godot-finish-implementer")
    return {
        "version": 1,
        "asset_root": "assets",
        "pipeline_path": "assets/pipeline.json",
        "provenance_path": "assets/PROVENANCE.md",
        "briefs_dir": "assets/briefs",
        "stack_label": pipeline.get("stack_label"),
        "target_platform": pipeline.get("target_platform"),
        "routes": primary_routes,
        "brief_targets": pipeline.get("brief_targets", []),
        "suggested_agents": suggested_agents,
        "suggested_skills": sorted(set(suggested_skills)),
        "initialized_by": "skills/asset-pipeline/scripts/init_asset_pipeline.py",
    }


def _provenance_markdown(
    *,
    placeholder_policy: str,
    licensing_or_provenance_constraints: str,
    finish_acceptance_signals: str,
) -> str:
    return "\n".join(
        (
            "# Asset Provenance",
            "",
            "Track every sourced or generated asset added to this repo in the same ticket that introduces it.",
            "",
            "## Rules",
            "",
            "- Every entry must use a repo-relative path under `assets/` or a Godot `res://` import path.",
            "- Generated assets must record the exact workflow or tool used to create them.",
            "- Third-party assets must keep the source URL and precise license value.",
            f"- Placeholder policy: {placeholder_policy}",
            f"- Licensing/provenance constraints: {licensing_or_provenance_constraints}",
            f"- Finish acceptance signals: {finish_acceptance_signals}",
            "",
            "| asset_path | source_or_workflow | license | author | acquired_or_generated_on | notes |",
            "| --- | --- | --- | --- | --- | --- |",
            "",
        )
    )


def _briefs_readme(pipeline: dict[str, object]) -> str:
    brief_targets = pipeline.get("brief_targets", [])
    route_line = ", ".join(brief_targets) if isinstance(brief_targets, list) and brief_targets else "none yet"
    return "\n".join(
        (
            "# Asset Briefs",
            "",
            "Write one asset brief per Blender-MCP or high-complexity generated asset.",
            "",
            f"- Current brief-target categories: {route_line}",
            "- Store briefs as `assets/briefs/<asset-name>.md`.",
            "- Include silhouette, proportions, materials, triangle budget, export target, and finish constraints.",
            "- Keep the brief aligned with `assets/pipeline.json` and update `assets/PROVENANCE.md` after generation.",
            "",
        )
    )


def _write_text(path: Path, content: str, *, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def initialize_asset_pipeline(
    repo_root: Path,
    *,
    stack_label: str,
    deliverable_kind: str,
    placeholder_policy: str,
    content_source_plan: str,
    licensing_or_provenance_constraints: str,
    finish_acceptance_signals: str,
    force: bool = False,
) -> list[Path]:
    repo_root = repo_root.expanduser().resolve()
    asset_root = repo_root / "assets"
    meta_root = repo_root / ".opencode" / "meta"
    created: list[Path] = []

    pipeline = _pipeline_payload(
        stack_label=stack_label,
        deliverable_kind=deliverable_kind,
        placeholder_policy=placeholder_policy,
        content_source_plan=content_source_plan,
        licensing_or_provenance_constraints=licensing_or_provenance_constraints,
        finish_acceptance_signals=finish_acceptance_signals,
    )
    metadata = _bootstrap_metadata(pipeline)

    for subdir in ASSET_SUBDIRS:
        directory = asset_root / subdir
        directory.mkdir(parents=True, exist_ok=True)
        keep_path = directory / ".gitkeep"
        if _write_text(keep_path, "", force=force):
            created.append(keep_path)

    pipeline_path = asset_root / "pipeline.json"
    if _write_text(pipeline_path, json.dumps(pipeline, indent=2) + "\n", force=force):
        created.append(pipeline_path)

    provenance_path = asset_root / "PROVENANCE.md"
    if _write_text(
        provenance_path,
        _provenance_markdown(
            placeholder_policy=placeholder_policy,
            licensing_or_provenance_constraints=licensing_or_provenance_constraints,
            finish_acceptance_signals=finish_acceptance_signals,
        ),
        force=force,
    ):
        created.append(provenance_path)

    briefs_readme_path = asset_root / "briefs" / "README.md"
    if _write_text(briefs_readme_path, _briefs_readme(pipeline), force=force):
        created.append(briefs_readme_path)

    metadata_path = meta_root / "asset-pipeline-bootstrap.json"
    if _write_text(metadata_path, json.dumps(metadata, indent=2) + "\n", force=force):
        created.append(metadata_path)

    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed repo-local asset pipeline surfaces for game projects.")
    parser.add_argument("repo_root", help="Repository root to initialize.")
    parser.add_argument("--stack-label", default="")
    parser.add_argument("--deliverable-kind", default="")
    parser.add_argument("--placeholder-policy", default="")
    parser.add_argument("--content-source-plan", default="")
    parser.add_argument("--licensing-or-provenance-constraints", default="")
    parser.add_argument("--finish-acceptance-signals", default="")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    provenance = _read_bootstrap_provenance(repo_root)
    stack_label = _normalize_text(args.stack_label or str(provenance.get("stack_label", ""))) or "framework-agnostic"
    deliverable_kind = _contract_value(
        provenance,
        args.deliverable_kind,
        "deliverable_kind",
        "prototype unless the normalized brief records a stricter final product bar",
    )
    placeholder_policy = _contract_value(
        provenance,
        args.placeholder_policy,
        "placeholder_policy",
        "placeholder_ok unless the normalized brief records a stricter finish policy",
    )
    content_source_plan = _contract_value(
        provenance,
        args.content_source_plan,
        "content_source_plan",
        "record whether content is authored, licensed, procedural, mixed, or intentionally absent",
    )
    licensing_or_provenance_constraints = _contract_value(
        provenance,
        args.licensing_or_provenance_constraints,
        "licensing_or_provenance_constraints",
        "record any asset or content provenance constraints here",
    )
    finish_acceptance_signals = _contract_value(
        provenance,
        args.finish_acceptance_signals,
        "finish_acceptance_signals",
        "record the explicit finish-proof signals that must be met before the repo is treated as finished",
    )

    created = initialize_asset_pipeline(
        repo_root,
        stack_label=stack_label,
        deliverable_kind=deliverable_kind,
        placeholder_policy=placeholder_policy,
        content_source_plan=content_source_plan,
        licensing_or_provenance_constraints=licensing_or_provenance_constraints,
        finish_acceptance_signals=finish_acceptance_signals,
        force=args.force,
    )
    print(f"Initialized asset pipeline in {repo_root} ({len(created)} files written)")
    for path in created:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
