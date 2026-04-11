from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
import sys

from android_scaffold import (
    normalize_android_package_name,
    renders_godot_android_assets,
)


TEXT_SUFFIXES = {
    ".md",
    ".json",
    ".jsonc",
    ".txt",
    ".ts",
    ".js",
    ".mjs",
    ".cjs",
    ".yaml",
    ".yml",
}

FULL_SCOPE_FILES = {
    "README.md",
    "AGENTS.md",
    "START-HERE.md",
    "opencode.jsonc",
    "docs",
    "tickets",
    ".opencode",
}

OPENCODE_SCOPE_FILES = {
    "opencode.jsonc",
    ".opencode",
}

PROCESS_CONTRACT_VERSION = 7
TICKET_CONTRACT_VERSION = 3
DEFAULT_PARALLEL_MODE = "sequential"
PLACEHOLDER_PATTERN = re.compile(r"__[A-Z0-9_]+__")
DEFAULT_DELIVERABLE_KIND = "prototype unless the normalized brief records a stricter final product bar"
DEFAULT_PLACEHOLDER_POLICY = "placeholder_ok unless the normalized brief records a stricter finish policy"
DEFAULT_VISUAL_FINISH_TARGET = (
    "record the project-specific visual finish bar here, or state that no consumer-facing visual bar applies"
)
DEFAULT_AUDIO_FINISH_TARGET = "record the project-specific audio finish bar here, or state that no audio bar applies"
DEFAULT_CONTENT_SOURCE_PLAN = "record whether content is authored, licensed, procedural, mixed, or intentionally absent"
DEFAULT_LICENSING_OR_PROVENANCE_CONSTRAINTS = "record any asset or content provenance constraints here"
DEFAULT_FINISH_ACCEPTANCE_SIGNALS = (
    "record the explicit finish-proof signals that must be met before the repo is treated as finished"
)
ASSET_PIPELINE_INIT_PATH = (
    Path(__file__).resolve().parents[2] / "asset-pipeline" / "scripts" / "init_asset_pipeline.py"
)


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "project"


def render_text(content: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        content = content.replace(key, value)
    return content


def render_relative_path(path: Path, replacements: dict[str, str]) -> Path:
    rendered_parts = [render_text(part, replacements) for part in path.parts]
    return Path(*rendered_parts)


def load_asset_pipeline_initializer():
    spec = spec_from_file_location("scafforge_asset_pipeline_init", ASSET_PIPELINE_INIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load asset pipeline initializer from {ASSET_PIPELINE_INIT_PATH}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ASSET_PIPELINE_INIT = load_asset_pipeline_initializer()


def build_model_operating_profile(*, model_tier: str) -> dict[str, str]:
    profiles = {
        "weak": {
            "name": "Weak-tier evidence-first profile",
            "description": (
                "Use the most explicit prompt density. Include full stop conditions, concrete examples, "
                "truth-source reminders, and named blocker paths so weaker models have one legal next move."
            ),
            "prompt_density": "full checklists, explicit examples, and repeated truth-source reminders",
            "rules": "\n".join(
                (
                    "- include explicit stop conditions and escalation triggers in every coordinating prompt",
                    "- spell out verification checklists instead of implying them",
                    "- name the canonical truth surfaces before acting on mutable or derived views",
                    "- use example-shaped outputs when they remove ambiguity",
                    "- keep each ask focused on one bounded goal at a time",
                    "- stop on blockers instead of guessing or silently filling gaps",
                )
            ),
        },
        "standard": {
            "name": "Standard-tier evidence-first profile",
            "description": (
                "Keep prompts explicit and bounded, but use lighter repetition. Preserve stop conditions and "
                "verification checklists while relying more on linked canonical docs than inline examples."
            ),
            "prompt_density": "explicit checklists with selective examples and linked truth sources",
            "rules": "\n".join(
                (
                    "- keep stop conditions and verification checklists explicit",
                    "- reference canonical truth surfaces directly when they already contain the durable procedure",
                    "- use examples only where the workflow would otherwise stay ambiguous",
                    "- keep tasks bounded and evidence-first",
                    "- surface blockers clearly instead of improvising around them",
                )
            ),
        },
        "strong": {
            "name": "Strong-tier evidence-first profile",
            "description": (
                "Use concise prompts that still preserve hard safety boundaries. Keep stop conditions explicit, "
                "link back to local checklists, and avoid unnecessary example density when the model can infer format reliably."
            ),
            "prompt_density": "concise prompts with linked checklists and minimal examples",
            "rules": "\n".join(
                (
                    "- keep stop conditions, ownership boundaries, and blocker returns explicit",
                    "- reference local checklist and truth-source docs instead of repeating them in full",
                    "- use examples only when a repo-specific shape has proven fragile",
                    "- preserve bounded asks and evidence-first completion requirements",
                    "- never trade away verification or escalation rules for brevity",
                )
            ),
        },
    }
    return profiles[model_tier]


def validate_replacement_values(replacements: dict[str, str]) -> None:
    for placeholder, value in replacements.items():
        if PLACEHOLDER_PATTERN.search(value):
            raise SystemExit(
                f"Replacement for {placeholder} contains placeholder-shaped text ({value!r}). "
                "Choose values without double-underscore placeholder markers."
            )


def ensure_idempotent_target(dest_root: Path) -> None:
    if (dest_root / ".opencode").exists():
        raise SystemExit(
            f"Refusing to scaffold into {dest_root}: an existing .opencode/ layer was found. "
            "Use the retrofit or repair flow instead of double-scaffolding an existing repo."
        )
def should_copy(root_name: str, scope: str, stack_label: str) -> bool:
    if scope == "opencode":
        return root_name in OPENCODE_SCOPE_FILES
    if root_name in {"export_presets.cfg", "android"}:
        return renders_godot_android_assets(stack_label)
    return root_name in FULL_SCOPE_FILES


def copy_template(template_root: Path, dest_root: Path, replacements: dict[str, str], scope: str, force: bool) -> list[Path]:
    created: list[Path] = []
    stack_label = replacements.get("__STACK_LABEL__", "")

    for source in template_root.iterdir():
        if not should_copy(source.name, scope, stack_label):
            continue
        target = dest_root / source.name
        if source.is_dir():
            created.extend(copy_dir(source, target, replacements, force))
        else:
            write_file(source, target, replacements, force)
            created.append(target)
    return created


def ensure_asset_pipeline_surfaces(
    dest_root: Path,
    *,
    scope: str,
    stack_label: str,
    deliverable_kind: str,
    placeholder_policy: str,
    content_source_plan: str,
    licensing_or_provenance_constraints: str,
    finish_acceptance_signals: str,
    force: bool,
) -> list[Path]:
    if scope != "full" or not renders_godot_android_assets(stack_label):
        return []
    return ASSET_PIPELINE_INIT.initialize_asset_pipeline(
        dest_root,
        stack_label=stack_label,
        deliverable_kind=deliverable_kind,
        placeholder_policy=placeholder_policy,
        content_source_plan=content_source_plan,
        licensing_or_provenance_constraints=licensing_or_provenance_constraints,
        finish_acceptance_signals=finish_acceptance_signals,
        force=force,
    )


def copy_dir(source_dir: Path, dest_dir: Path, replacements: dict[str, str], force: bool) -> list[Path]:
    created: list[Path] = []
    dest_dir.mkdir(parents=True, exist_ok=True)
    for source in source_dir.rglob("*"):
        relative = render_relative_path(source.relative_to(source_dir), replacements)
        target = dest_dir / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        write_file(source, target, replacements, force)
        created.append(target)
    return created


def write_file(source: Path, target: Path, replacements: dict[str, str], force: bool) -> None:
    if target.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix in TEXT_SUFFIXES:
        text = source.read_text(encoding="utf-8")
        target.write_text(render_text(text, replacements), encoding="utf-8")
    else:
        shutil.copy2(source, target)


def next_ticket_wave(tickets: list[dict[str, object]]) -> int:
    waves = [int(ticket.get("wave", 0)) for ticket in tickets if isinstance(ticket, dict)]
    return max(waves, default=1) + 1


_BOOTSTRAP_RELEASE_INFRA_LANES: frozenset[str] = frozenset(
    {"android-export", "signing-prerequisites", "release-readiness"}
)


def _bootstrap_terminal_feature_ids(tickets: list[dict[str, object]]) -> list[str]:
    """Return IDs of all max-wave non-infrastructure tickets present at bootstrap time.

    At bootstrap time no remediation tickets exist yet, so we only need to exclude
    the three Android infrastructure lanes.  Returns [] when no eligible candidates
    exist (pure pipeline-proof repos with no feature tickets).
    """
    candidates = [
        t for t in tickets
        if isinstance(t, dict)
        and t.get("lane") not in _BOOTSTRAP_RELEASE_INFRA_LANES
        and int(t.get("wave", 0)) > 0
    ]
    if not candidates:
        return []
    max_wave = max(int(t.get("wave", 0)) for t in candidates)
    return [str(t["id"]) for t in candidates if int(t.get("wave", 0)) == max_wave]


def requires_packaged_android_delivery(deliverable_kind: str) -> bool:
    lowered = deliverable_kind.lower()
    indicators = (
        "release_apk",
        "release_aab",
        "packaged_apk",
        "packaged_aab",
        "packaged mobile product",
        "packaged android",
        "signed apk",
        "signed aab",
        "store-ready",
        "release-ready",
        "play store",
        "google play",
    )
    return any(indicator in lowered for indicator in indicators)


def requires_finish_ownership(placeholder_policy: str) -> bool:
    lowered = " ".join(placeholder_policy.lower().split())
    if any(
        marker in lowered
        for marker in (
            "placeholder_ok",
            "placeholder ok",
            "placeholders ok",
            "placeholder acceptable",
            "placeholders acceptable",
            "placeholder allowed",
            "placeholders allowed",
        )
    ):
        return False
    return any(
        marker in lowered
        for marker in (
            "no_placeholders",
            "no placeholder",
            "no placeholders",
            "placeholder-free",
            "placeholder free",
        )
    )


def target_is_intentionally_absent(target: str, *, absent_marker: str) -> bool:
    lowered = target.lower()
    return absent_marker in lowered or "intentionally absent" in lowered


def ensure_godot_android_completion_tickets(
    dest_root: Path,
    project_slug: str,
    stack_label: str,
    *,
    deliverable_kind: str,
) -> None:
    if not renders_godot_android_assets(stack_label):
        return

    manifest_path = dest_root / "tickets" / "manifest.json"
    if not manifest_path.exists():
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tickets = manifest.get("tickets")
    if not isinstance(tickets, list):
        return

    existing_ids = {str(ticket.get("id", "")).strip() for ticket in tickets if isinstance(ticket, dict)}
    packaged_delivery = requires_packaged_android_delivery(deliverable_kind)
    android_tickets: list[dict[str, object]] = []
    if "ANDROID-001" not in existing_ids:
        android_tickets.append(
            {
                "id": "ANDROID-001",
                "title": "Create Android export surfaces",
                "wave": 2,
                "lane": "android-export",
                "parallel_safe": False,
                "overlap_risk": "high",
                "stage": "planning",
                "status": "todo",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": ["SETUP-001"],
                "source_ticket_id": None,
                "follow_up_ticket_ids": ["SIGNING-001"] if packaged_delivery else ["RELEASE-001"],
                "summary": "Create and validate the repo-local Android export surfaces for this Godot Android target, including export_presets.cfg, android/ support files, and the canonical debug export command.",
                "acceptance": [
                    "export_presets.cfg exists at repo root and defines an Android preset",
                    "Repo-local android support surfaces exist and are not placeholder content",
                    f"The canonical Godot Android debug export target is build/android/{project_slug}-debug.apk",
                ],
                "decision_blockers": [],
                "artifacts": [],
            }
        )
    if packaged_delivery and "SIGNING-001" not in existing_ids:
        android_tickets.append(
            {
                "id": "SIGNING-001",
                "title": "Own Android signing prerequisites",
                "wave": 3,
                "lane": "signing-prerequisites",
                "parallel_safe": False,
                "overlap_risk": "high",
                "stage": "planning",
                "status": "todo",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": [],
                "source_ticket_id": "ANDROID-001",
                "follow_up_ticket_ids": ["RELEASE-001"],
                "source_mode": "split_scope",
                "split_kind": "sequential_dependent",
                "summary": "Own the Android signing inputs for packaged delivery, including keystore reference, alias ownership, password handling, and the release-artifact proof path. Scafforge must not fabricate secrets or host signing material.",
                "acceptance": [
                    "The release keystore path or CI secret reference is declared in canonical project truth",
                    "Keystore alias and password ownership is documented for the release pipeline",
                    "The packaged Android delivery flow can produce a signed release APK or AAB once the owned signing inputs are present",
                ],
                "decision_blockers": [
                    "Signing keys and secrets must be supplied by the project team or CI. Scafforge cannot generate or assume them.",
                ],
                "artifacts": [],
            }
        )
    if "RELEASE-001" not in existing_ids:
        release_acceptance = [
            f"`godot4 --headless --path . --export-debug Android\\ Debug build/android/{project_slug}-debug.apk` produces a debug APK at build/android/{project_slug}-debug.apk or the exact blocker is recorded with command evidence",
            "`godot4 --headless --path . --quit` succeeds before release closeout so export proof does not mask broken runtime/script-load state",
            "The APK build uses the Android export surfaces owned by ANDROID-001",
            "Release-readiness evidence names the exact export command and outcome",
        ]
        if packaged_delivery:
            release_acceptance.extend(
                [
                    "A signed release APK or AAB is produced once signing prerequisites are satisfied via SIGNING-001",
                    f"The deliverable-proof artifact path is recorded as build/android/{project_slug}-release.apk",
                ]
            )
        release_feature_gate = _bootstrap_terminal_feature_ids(tickets)
        release_depends_on: list[str] = (
            ["SIGNING-001"] + release_feature_gate if packaged_delivery else release_feature_gate
        )
        android_tickets.append(
            {
                "id": "RELEASE-001",
                "title": "Build Android runnable proof and deliverable APK/AAB" if packaged_delivery else "Build Android debug APK",
                "wave": 4 if packaged_delivery else 3,
                "lane": "release-readiness",
                "parallel_safe": False,
                "overlap_risk": "high",
                "stage": "planning",
                "status": "todo",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": release_depends_on,
                "source_ticket_id": "SIGNING-001" if packaged_delivery else "ANDROID-001",
                "follow_up_ticket_ids": [],
                "source_mode": "split_scope",
                "split_kind": "sequential_dependent",
                "summary": (
                    f"Produce and validate the canonical Android debug APK at build/android/{project_slug}-debug.apk using the repo-managed Godot Android export surfaces."
                    + (
                        " When signing prerequisites are satisfied, additionally produce and validate the signed release deliverable artifact."
                        if packaged_delivery
                        else ""
                    )
                ),
                "acceptance": release_acceptance,
                "decision_blockers": [],
                "artifacts": [],
            }
        )

    if not android_tickets:
        return

    tickets.extend(android_tickets)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def ensure_finish_ownership_tickets(
    dest_root: Path,
    *,
    placeholder_policy: str,
    visual_finish_target: str,
    audio_finish_target: str,
    content_source_plan: str,
    finish_acceptance_signals: str,
) -> None:
    if not requires_finish_ownership(placeholder_policy):
        return

    manifest_path = dest_root / "tickets" / "manifest.json"
    if not manifest_path.exists():
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tickets = manifest.get("tickets")
    if not isinstance(tickets, list):
        return

    existing_ids = {str(ticket.get("id", "")).strip() for ticket in tickets if isinstance(ticket, dict)}
    added_finish_ids: list[str] = []
    wave = next_ticket_wave(tickets)

    if "VISUAL-001" not in existing_ids and not target_is_intentionally_absent(
        visual_finish_target,
        absent_marker="no consumer-facing visual bar applies",
    ):
        tickets.append(
            {
                "id": "VISUAL-001",
                "title": "Own ship-ready visual finish",
                "wave": wave,
                "lane": "finish-visual",
                "parallel_safe": False,
                "overlap_risk": "medium",
                "stage": "planning",
                "status": "todo",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": ["SETUP-001"],
                "summary": f"Replace prototype-grade visuals with the declared ship bar: {visual_finish_target}.",
                "acceptance": [
                    f"The visual finish target is met: {visual_finish_target}",
                    "No placeholder or throwaway visual assets remain in the user-facing product surfaces",
                ],
                "decision_blockers": [],
                "artifacts": [],
                "follow_up_ticket_ids": [],
            }
        )
        existing_ids.add("VISUAL-001")
        added_finish_ids.append("VISUAL-001")
        wave += 1

    if "AUDIO-001" not in existing_ids and not target_is_intentionally_absent(
        audio_finish_target,
        absent_marker="no audio bar applies",
    ):
        tickets.append(
            {
                "id": "AUDIO-001",
                "title": "Own ship-ready audio finish",
                "wave": wave,
                "lane": "finish-audio",
                "parallel_safe": False,
                "overlap_risk": "medium",
                "stage": "planning",
                "status": "todo",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": ["SETUP-001"],
                "summary": f"Deliver the declared user-facing audio bar: {audio_finish_target}.",
                "acceptance": [
                    f"The audio finish target is met: {audio_finish_target}",
                    "No placeholder, missing, or temporary user-facing audio remains where the finish contract requires audio delivery",
                ],
                "decision_blockers": [],
                "artifacts": [],
                "follow_up_ticket_ids": [],
            }
        )
        existing_ids.add("AUDIO-001")
        added_finish_ids.append("AUDIO-001")
        wave += 1

    if not added_finish_ids and "CONTENT-001" not in existing_ids:
        tickets.append(
            {
                "id": "CONTENT-001",
                "title": "Own authored content finish",
                "wave": wave,
                "lane": "finish-content",
                "parallel_safe": False,
                "overlap_risk": "medium",
                "stage": "planning",
                "status": "todo",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": ["SETUP-001"],
                "summary": f"Replace placeholder product content with the declared authored/licensed/procedural bar: {content_source_plan}.",
                "acceptance": [
                    f"The content source plan is owned and implemented: {content_source_plan}",
                    "No placeholder user-facing content remains in the finished product surfaces",
                ],
                "decision_blockers": [],
                "artifacts": [],
                "follow_up_ticket_ids": [],
            }
        )
        existing_ids.add("CONTENT-001")
        added_finish_ids.append("CONTENT-001")
        wave += 1

    finish_dependencies = [ticket_id for ticket_id in ("VISUAL-001", "AUDIO-001", "CONTENT-001") if ticket_id in existing_ids]
    if finish_dependencies and "FINISH-VALIDATE-001" not in existing_ids:
        tickets.append(
            {
                "id": "FINISH-VALIDATE-001",
                "title": "Validate product finish contract",
                "wave": wave,
                "lane": "finish-validation",
                "parallel_safe": False,
                "overlap_risk": "medium",
                "stage": "planning",
                "status": "todo",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": finish_dependencies,
                "summary": "Prove that the declared Product Finish Contract is satisfied and that no placeholder output remains in user-facing surfaces.",
                "acceptance": [
                    f"Finish proof matches the declared acceptance signals: {finish_acceptance_signals}",
                    "`godot4 --headless --path . --quit` succeeds so finish validation is based on a loadable product, not just exported artifacts",
                    "All finish-direction, visual, audio, or content ownership tickets required by the contract are completed before closeout",
                ],
                "decision_blockers": [],
                "artifacts": [],
                "follow_up_ticket_ids": [],
            }
        )

    release_ticket = next(
        (
            ticket
            for ticket in tickets
            if isinstance(ticket, dict) and str(ticket.get("id", "")).strip() == "RELEASE-001"
        ),
        None,
    )
    if isinstance(release_ticket, dict) and "FINISH-VALIDATE-001" in {
        str(ticket.get("id", "")).strip() for ticket in tickets if isinstance(ticket, dict)
    }:
        release_depends_on = [
            str(dep).strip()
            for dep in release_ticket.get("depends_on", [])
            if isinstance(dep, str) and str(dep).strip()
        ]
        if "FINISH-VALIDATE-001" not in release_depends_on:
            release_depends_on.append("FINISH-VALIDATE-001")
            release_ticket["depends_on"] = release_depends_on

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def managed_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def template_commit() -> dict[str, str | bool | None]:
    if os.environ.get("SCAFFORGE_FORCE_MISSING_PROVENANCE") == "1":
        return {
            "success": False,
            "commit": None,
            "reason": "missing_provenance",
            "detail": "SCAFFORGE_FORCE_MISSING_PROVENANCE requested missing provenance for this run.",
        }
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=managed_repo_root(),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return {
            "success": False,
            "commit": None,
            "reason": "git_failure",
            "detail": result.stderr.strip() or result.stdout.strip() or "git rev-parse HEAD failed",
        }
    commit = result.stdout.strip()
    if not commit:
        return {
            "success": False,
            "commit": None,
            "reason": "empty_git_output",
            "detail": "git rev-parse HEAD returned no commit hash",
        }
    return {
        "success": True,
        "commit": commit,
        "reason": None,
        "detail": None,
    }


def write_bootstrap_provenance(
    dest_root: Path,
    *,
    project_name: str,
    project_slug: str,
    package_name: str,
    agent_prefix: str,
    scope: str,
    model_tier: str,
    model_provider: str,
    planner_model: str,
    implementer_model: str,
    utility_model: str,
    stack_label: str,
    deliverable_kind: str,
    placeholder_policy: str,
    visual_finish_target: str,
    audio_finish_target: str,
    content_source_plan: str,
    licensing_or_provenance_constraints: str,
    finish_acceptance_signals: str,
) -> None:
    template_commit_result = template_commit()
    steps = (
        ["repo-scaffold-factory/render-full-scaffold"]
        if scope == "full"
        else ["opencode-team-bootstrap/render-opencode-layer", "repo-scaffold-factory/render-opencode-scope"]
    )
    payload = {
        "managed_repo": str(managed_repo_root()),
        "template_commit": template_commit_result.get("commit") or "missing_provenance",
        "template_commit_result": template_commit_result,
        "template_asset_root": "skills/repo-scaffold-factory/assets/project-template",
        "project_name": project_name,
        "project_slug": project_slug,
        "package_name": package_name,
        "agent_prefix": agent_prefix,
        "generation_scope": scope,
        "runtime_models": {
            "tier": model_tier,
            "provider": model_provider,
            "planner": planner_model,
            "implementer": implementer_model,
            "utility": utility_model,
        },
        "stack_label": stack_label,
        "deliverable_kind": deliverable_kind,
        "deliverable_artifact_path": (
            f"build/android/{project_slug}-release.apk"
            if renders_godot_android_assets(stack_label) and requires_packaged_android_delivery(deliverable_kind)
            else None
        ),
        "product_finish_contract": {
            "deliverable_kind": deliverable_kind,
            "placeholder_policy": placeholder_policy,
            "visual_finish_target": visual_finish_target,
            "audio_finish_target": audio_finish_target,
            "content_source_plan": content_source_plan,
            "licensing_or_provenance_constraints": licensing_or_provenance_constraints,
            "finish_acceptance_signals": finish_acceptance_signals,
        },
        "bootstrap_steps": steps,
        "tracking": {
            "invocation_log": ".opencode/state/invocation-log.jsonl",
            "skill_ping_tool": "skill_ping",
            "tracker_plugin": "invocation-tracker",
        },
        "workflow_contract": {
            "process_version": PROCESS_CONTRACT_VERSION,
            "ticket_contract_version": TICKET_CONTRACT_VERSION,
            "parallel_mode": DEFAULT_PARALLEL_MODE,
            "manager_hierarchy": {
                "first_class_scaffold_profile": False,
                "advanced_customization_allowed": True,
            },
            "post_migration_verification": {
                "enabled": True,
                "backlog_verifier_agent": f"{agent_prefix}-backlog-verifier",
                "ticket_creator_agent": f"{agent_prefix}-ticket-creator",
            },
        },
        "managed_surfaces": {
            "replace_on_retrofit": [
                "opencode.jsonc",
                ".opencode/tools",
                ".opencode/plugins",
                ".opencode/commands",
                "scaffold-managed .opencode/skills",
                "docs/process/workflow.md",
                "docs/process/tooling.md",
                "docs/process/model-matrix.md",
                "docs/process/git-capability.md",
                "START-HERE.md managed block",
            ],
            "project_specific_follow_up": [
                ".opencode/skills",
                ".opencode/agents",
                "docs/process/agent-catalog.md",
            ],
            "preserve_project_sources": [
                "docs/spec/CANONICAL-BRIEF.md",
                "tickets/manifest.json",
                "tickets/*.md",
                ".opencode/state/artifacts",
                ".opencode/state/bootstrap",
                ".opencode/state/plans",
                ".opencode/state/implementations",
                ".opencode/state/reviews",
                ".opencode/state/qa",
                ".opencode/state/smoke-tests",
                ".opencode/state/handoffs",
            ],
        },
        "migration_history": [],
        "repair_history": [],
    }

    target = dest_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_state_directories(dest_root: Path) -> None:
    for relative in (
        ".opencode/state/plans",
        ".opencode/state/implementations",
        ".opencode/state/reviews",
        ".opencode/state/qa",
        ".opencode/state/smoke-tests",
        ".opencode/state/handoffs",
        ".opencode/state/artifacts",
        ".opencode/state/bootstrap",
    ):
        (dest_root / relative).mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the repository scaffold template.")
    parser.add_argument("--dest", required=True, help="Destination repository root")
    parser.add_argument("--project-name", required=True, help="Human-facing project name")
    parser.add_argument("--project-slug", help="Slug used in filenames and defaults")
    parser.add_argument("--agent-prefix", help="OpenCode agent prefix")
    parser.add_argument(
        "--model-tier",
        choices=("strong", "standard", "weak"),
        default="weak",
        help="Prompt-density tier for generated agent guidance; defaults to the weaker-model-first profile.",
    )
    parser.add_argument(
        "--model-provider",
        required=True,
        help="Explicit provider label chosen for this scaffold run",
    )
    parser.add_argument(
        "--planner-model",
        required=True,
        help="Explicit planner/reviewer/team-lead model string",
    )
    parser.add_argument(
        "--implementer-model",
        required=True,
        help="Explicit implementer model string",
    )
    parser.add_argument(
        "--utility-model",
        help="Explicit utility/docs/QA/helper model string; defaults to planner-model when omitted",
    )
    parser.add_argument(
        "--scope",
        choices=("full", "opencode"),
        default="full",
        help="Render the full scaffold or only the OpenCode layer",
    )
    parser.add_argument(
        "--stack-label",
        default="framework-agnostic",
        help="Label used in generated docs for the current stack mode",
    )
    parser.add_argument(
        "--deliverable-kind",
        default=DEFAULT_DELIVERABLE_KIND,
        help="Product finish contract deliverable_kind value to record in the canonical brief.",
    )
    parser.add_argument(
        "--placeholder-policy",
        default=DEFAULT_PLACEHOLDER_POLICY,
        help="Product finish contract placeholder_policy value to record in the canonical brief.",
    )
    parser.add_argument(
        "--visual-finish-target",
        default=DEFAULT_VISUAL_FINISH_TARGET,
        help="Product finish contract visual_finish_target value to record in the canonical brief.",
    )
    parser.add_argument(
        "--audio-finish-target",
        default=DEFAULT_AUDIO_FINISH_TARGET,
        help="Product finish contract audio_finish_target value to record in the canonical brief.",
    )
    parser.add_argument(
        "--content-source-plan",
        default=DEFAULT_CONTENT_SOURCE_PLAN,
        help="Product finish contract content_source_plan value to record in the canonical brief.",
    )
    parser.add_argument(
        "--licensing-or-provenance-constraints",
        default=DEFAULT_LICENSING_OR_PROVENANCE_CONSTRAINTS,
        help="Product finish contract licensing_or_provenance_constraints value to record in the canonical brief.",
    )
    parser.add_argument(
        "--finish-acceptance-signals",
        default=DEFAULT_FINISH_ACCEPTANCE_SIGNALS,
        help="Product finish contract finish_acceptance_signals value to record in the canonical brief.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dest_root = Path(args.dest).expanduser().resolve()
    template_root = Path(__file__).resolve().parent.parent / "assets" / "project-template"

    if not args.force:
        ensure_idempotent_target(dest_root)

    slug = args.project_slug or slugify(args.project_name)
    package_name = normalize_android_package_name(slug)
    agent_prefix = args.agent_prefix or slug
    planner_model = args.planner_model
    implementer_model = args.implementer_model
    utility_model = args.utility_model or planner_model
    model_profile = build_model_operating_profile(model_tier=args.model_tier)

    replacements = {
        "__PROJECT_NAME__": args.project_name,
        "__PROJECT_SLUG__": slug,
        "__PACKAGE_NAME__": package_name,
        "__AGENT_PREFIX__": agent_prefix,
        "__MODEL_TIER__": args.model_tier,
        "__MODEL_PROVIDER__": args.model_provider,
        "__PLANNER_MODEL__": planner_model,
        "__IMPLEMENTER_MODEL__": implementer_model,
        "__UTILITY_MODEL__": utility_model,
        # Combined provider/model tokens — used in agent and command frontmatter `model:` fields
        # so that the rendered files contain the full `provider/model` format that OpenCode requires.
        "__FULL_PLANNER_MODEL__": f"{args.model_provider}/{planner_model}",
        "__FULL_IMPLEMENTER_MODEL__": f"{args.model_provider}/{implementer_model}",
        "__FULL_UTILITY_MODEL__": f"{args.model_provider}/{utility_model}",
        "__MODEL_OPERATING_PROFILE_NAME__": model_profile["name"],
        "__MODEL_OPERATING_PROFILE_DESCRIPTION__": model_profile["description"],
        "__MODEL_PROMPT_DENSITY__": model_profile["prompt_density"],
        "__MODEL_OPERATING_PROFILE_RULES__": model_profile["rules"],
        "__STACK_LABEL__": args.stack_label,
        "__DELIVERABLE_KIND__": args.deliverable_kind,
        "__PLACEHOLDER_POLICY__": args.placeholder_policy,
        "__VISUAL_FINISH_TARGET__": args.visual_finish_target,
        "__AUDIO_FINISH_TARGET__": args.audio_finish_target,
        "__CONTENT_SOURCE_PLAN__": args.content_source_plan,
        "__LICENSING_OR_PROVENANCE_CONSTRAINTS__": args.licensing_or_provenance_constraints,
        "__FINISH_ACCEPTANCE_SIGNALS__": args.finish_acceptance_signals,
    }
    validate_replacement_values(replacements)

    dest_root.mkdir(parents=True, exist_ok=True)
    created = copy_template(template_root, dest_root, replacements, args.scope, args.force)
    created.extend(
        ensure_asset_pipeline_surfaces(
            dest_root,
            scope=args.scope,
            stack_label=args.stack_label,
            deliverable_kind=args.deliverable_kind,
            placeholder_policy=args.placeholder_policy,
            content_source_plan=args.content_source_plan,
            licensing_or_provenance_constraints=args.licensing_or_provenance_constraints,
            finish_acceptance_signals=args.finish_acceptance_signals,
            force=args.force,
        )
    )
    ensure_finish_ownership_tickets(
        dest_root,
        placeholder_policy=args.placeholder_policy,
        visual_finish_target=args.visual_finish_target,
        audio_finish_target=args.audio_finish_target,
        content_source_plan=args.content_source_plan,
        finish_acceptance_signals=args.finish_acceptance_signals,
    )
    ensure_godot_android_completion_tickets(
        dest_root,
        slug,
        args.stack_label,
        deliverable_kind=args.deliverable_kind,
    )
    ensure_state_directories(dest_root)
    write_bootstrap_provenance(
        dest_root,
        project_name=args.project_name,
        project_slug=slug,
        package_name=package_name,
        agent_prefix=agent_prefix,
        scope=args.scope,
        model_tier=args.model_tier,
        model_provider=args.model_provider,
        planner_model=planner_model,
        implementer_model=implementer_model,
        utility_model=utility_model,
        stack_label=args.stack_label,
        deliverable_kind=args.deliverable_kind,
        placeholder_policy=args.placeholder_policy,
        visual_finish_target=args.visual_finish_target,
        audio_finish_target=args.audio_finish_target,
        content_source_plan=args.content_source_plan,
        licensing_or_provenance_constraints=args.licensing_or_provenance_constraints,
        finish_acceptance_signals=args.finish_acceptance_signals,
    )

    print(f"Rendered {len(created)} files into {dest_root}")
    for path in created[:20]:
        print(f"- {path}")
    if len(created) > 20:
        print(f"... and {len(created) - 20} more files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
