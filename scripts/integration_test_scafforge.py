from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from test_support.gpttalker_fixture_builders import build_fixture_family, fixture_index_by_slug
from test_support.repo_seeders import make_stack_skill_non_placeholder, read_json, seed_failing_pytest_suite, seed_ready_bootstrap
from test_support.scafforge_harness import (
    AUDIT,
    BOOTSTRAP,
    PIVOT,
    PIVOT_PUBLISH,
    PIVOT_RECORD,
    PUBLIC_REPAIR,
    RECORD_REPAIR_STAGE,
    ROOT,
    VERIFY_GENERATED,
    run,
    run_generated_tool,
    run_json,
)


FIXTURE_INDEX = ROOT / "tests" / "fixtures" / "gpttalker" / "index.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run focused end-to-end Scafforge integration coverage for greenfield, repair, pivot, and GPTTalker fixture families."
    )
    parser.add_argument("--list-fixtures", action="store_true", help="Print the curated GPTTalker fixture slugs and exit.")
    return parser.parse_args()


def ensure_fixture_index() -> dict[str, dict[str, Any]]:
    payload = read_json(FIXTURE_INDEX)
    if not isinstance(payload, dict):
        raise RuntimeError("Fixture index must be a JSON object.")
    families = payload.get("families")
    if not isinstance(families, list):
        raise RuntimeError("Fixture index must contain a families list.")
    indexed = fixture_index_by_slug()
    expected = {
        "bootstrap-dependency-layout-drift",
        "host-tool-or-permission-blockage",
        "repeated-lifecycle-contradiction",
        "restart-surface-drift-after-repair",
        "placeholder-skill-after-refresh",
        "split-scope-and-historical-trust-reconciliation",
    }
    if set(indexed) != expected:
        raise RuntimeError(f"Fixture index slugs do not match the curated GPTTalker family set: {sorted(indexed)}")
    return indexed


def bootstrap_full(dest: Path) -> None:
    run(
        [
            sys.executable,
            str(BOOTSTRAP),
            "--dest",
            str(dest),
            "--project-name",
            "Integration Probe",
            "--project-slug",
            "integration-probe",
            "--agent-prefix",
            "integration-probe",
            "--model-provider",
            "openrouter",
            "--planner-model",
            "openrouter/openai/gpt-5-mini",
            "--implementer-model",
            "openrouter/openai/gpt-5-mini",
            "--utility-model",
            "openrouter/openai/gpt-5-mini",
            "--stack-label",
            "framework-agnostic",
            "--scope",
            "full",
            "--force",
        ],
        ROOT,
    )


def require_host_prerequisite(name: str, *, context: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{context} requires `{name}` to be available on the current host.")
    return path


def seed_prompt_drift(dest: Path) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    text = team_leader.read_text(encoding="utf-8")
    text = text.replace("next_action_tool", "legacy_next_action_tool")
    text = text.replace("summary-only stopping is invalid", "summary-only stopping may happen")
    team_leader.write_text(text, encoding="utf-8")


def restore_prompt_surface(dest: Path, original_text: str) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    team_leader.write_text(original_text, encoding="utf-8")


def write_repair_completion_artifact(dest: Path, *, stage: str, cycle_id: str) -> None:
    artifact_rel = f".opencode/state/artifacts/history/repair/{stage}-completion.md"
    artifact_path = dest / artifact_rel
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        "# Repair Follow-On Completion\n\n"
        f"- completed_stage: {stage}\n"
        f"- cycle_id: {cycle_id}\n"
        f"- completed_by: {stage}\n\n"
        "## Summary\n\n"
        f"- Completed {stage} for the current repair cycle.\n",
        encoding="utf-8",
    )


def greenfield_integration(workspace: Path) -> None:
    dest = workspace / "greenfield"
    bootstrap_full(dest)
    bootstrap_lane = run_json(
        [
            sys.executable,
            str(VERIFY_GENERATED),
            str(dest),
            "--verification-kind",
            "bootstrap-lane",
            "--format",
            "json",
        ],
        ROOT,
    )
    if bootstrap_lane.get("verification_kind") != "greenfield_bootstrap_lane":
        raise RuntimeError("Greenfield integration should run the bootstrap-lane verifier before specialization.")
    if bootstrap_lane.get("bootstrap_lane_valid") is not True:
        raise RuntimeError("Greenfield integration should preserve one valid bootstrap lane immediately after scaffold render.")
    make_stack_skill_non_placeholder(dest)
    payload = run_json(
        [
            sys.executable,
            str(VERIFY_GENERATED),
            str(dest),
            "--format",
            "json",
        ],
        ROOT,
    )
    if payload.get("verification_kind") != "greenfield_continuation":
        raise RuntimeError("Greenfield integration should run the continuation verifier.")
    if payload.get("immediately_continuable") is not True or payload.get("finding_count") != 0:
        raise RuntimeError("Greenfield integration should prove the generated repo is immediately continuable once placeholder drift is removed.")


def repair_integration(workspace: Path) -> None:
    require_host_prerequisite("uv", context="Scafforge repair integration")
    dest = workspace / "repair"
    bootstrap_full(dest)
    seed_ready_bootstrap(dest)
    seed_failing_pytest_suite(dest)
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    original_team_leader = team_leader.read_text(encoding="utf-8")
    seed_prompt_drift(dest)
    initial = run_json(
        [
            sys.executable,
            str(PUBLIC_REPAIR),
            str(dest),
            "--skip-deterministic-refresh",
        ],
        ROOT,
        allow_returncodes={0, 3},
    )
    required = set(initial["execution_record"]["required_follow_on_stages"])
    expected_required = {
        "project-skill-bootstrap",
        "opencode-team-bootstrap",
        "agent-prompt-engineering",
        "ticket-pack-builder",
    }
    if required != expected_required:
        raise RuntimeError(f"Repair integration expected follow-on stages {sorted(expected_required)}, found {sorted(required)}")
    tracking_path = dest / ".opencode" / "meta" / "repair-follow-on-state.json"
    tracking_state = read_json(tracking_path)
    if not isinstance(tracking_state, dict):
        raise RuntimeError("Repair integration expected persistent follow-on tracking state.")
    cycle_id = tracking_state.get("cycle_id")
    if not isinstance(cycle_id, str) or not cycle_id:
        raise RuntimeError("Repair integration expected a non-empty repair cycle id.")
    provenance_evidence_rel = ".opencode/state/artifacts/history/repair/provenance-probe.md"
    provenance_evidence_path = dest / provenance_evidence_rel
    provenance_evidence_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_evidence_path.write_text("# Provenance probe\n", encoding="utf-8")
    missing_provenance_env = os.environ.copy()
    missing_provenance_env["SCAFFORGE_FORCE_MISSING_PROVENANCE"] = "1"
    missing_provenance_record = subprocess.run(
        [
            sys.executable,
            str(RECORD_REPAIR_STAGE),
            str(dest),
            "--stage",
            "ticket-pack-builder",
            "--completed-by",
            "ticket-pack-builder",
            "--summary",
            "This should fail when repair-package provenance is missing.",
            "--evidence",
            provenance_evidence_rel,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=missing_provenance_env,
    )
    if missing_provenance_record.returncode == 0:
        raise RuntimeError("Repair integration should reject recorded completion when repair-package provenance is missing.")
    combined_provenance_output = f"{missing_provenance_record.stdout}\n{missing_provenance_record.stderr}"
    if "requires repair_package_commit provenance" not in combined_provenance_output or "missing_provenance" not in combined_provenance_output:
        raise RuntimeError("Repair integration should explain missing provenance when recorded completion is rejected.")
    for stage in sorted(expected_required | {"handoff-brief"}):
        write_repair_completion_artifact(dest, stage=stage, cycle_id=cycle_id)
    artifact_recorded = run_json(
        [
            sys.executable,
            str(PUBLIC_REPAIR),
            str(dest),
            "--skip-deterministic-refresh",
        ],
        ROOT,
        allow_returncodes={0, 3},
    )
    recorded_before_fix = set(artifact_recorded["execution_record"]["recorded_execution_completed_stages"])
    expected_recorded = expected_required | {"handoff-brief"}
    if recorded_before_fix != expected_recorded:
        raise RuntimeError(f"Repair integration expected recorded completion for {sorted(expected_recorded)}, found {sorted(recorded_before_fix)}")
    if not artifact_recorded["execution_record"]["blocking_reasons"]:
        raise RuntimeError("Repair integration should stay managed-blocked while placeholder skill and prompt drift still exist.")
    make_stack_skill_non_placeholder(dest)
    restore_prompt_surface(dest, original_team_leader)
    converged = run_json(
        [
            sys.executable,
            str(PUBLIC_REPAIR),
            str(dest),
            "--skip-deterministic-refresh",
        ],
        ROOT,
        allow_returncodes={0, 3},
    )
    if converged["execution_record"]["blocking_reasons"]:
        raise RuntimeError("Repair integration should converge once current-cycle canonical completion artifacts exist for every routed follow-on stage.")
    if set(converged["execution_record"]["recorded_execution_completed_stages"]) != expected_recorded:
        raise RuntimeError("Repair integration should preserve recorded completion for all routed follow-on stages.")
    if converged["execution_record"]["repair_follow_on_outcome"] != "source_follow_up":
        raise RuntimeError("Repair integration should leave only source_follow_up once managed repair follow-on converges.")
    if converged["execution_record"]["handoff_allowed"] is not True:
        raise RuntimeError("Repair integration should allow handoff once only source follow-up remains.")


def pivot_integration(workspace: Path) -> None:
    dest = workspace / "pivot"
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)
    seed_ready_bootstrap(dest)
    run_generated_tool(dest, ".opencode/tools/handoff_publish.ts", {})
    payload = run_json(
        [
            sys.executable,
            str(PIVOT),
            str(dest),
            "--pivot-class",
            "architecture-change",
            "--requested-change",
            "Move from a single service layout to modular domain services with a refreshed workflow contract.",
            "--accepted-decision",
            "Regenerate workflow prompts, skills, and ticket routing around the modular topology.",
            "--format",
            "json",
        ],
        ROOT,
    )
    if payload["verification_status"]["verification_passed"] is not True:
        raise RuntimeError("Pivot integration should pass the post-pivot verification gate on a clean generated repo.")
    pending = payload["downstream_refresh_state"]["pending_stages"]
    if not isinstance(pending, list) or not pending:
        raise RuntimeError("Pivot integration expected routed downstream stages.")
    for stage in pending:
        evidence_rel = f".opencode/state/artifacts/history/pivot/{stage}-completion.md"
        evidence_path = dest / evidence_rel
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(f"# {stage} completion\n", encoding="utf-8")
        run_json(
            [
                sys.executable,
                str(PIVOT_RECORD),
                str(dest),
                "--stage",
                stage,
                "--completed-by",
                stage,
                "--summary",
                f"Completed {stage} during integration coverage.",
                "--evidence",
                evidence_rel,
            ],
            ROOT,
        )
    published = run_json(
        [
            sys.executable,
            str(PIVOT_PUBLISH),
            str(dest),
            "--published-by",
            "integration-test",
        ],
        ROOT,
    )
    state = read_json(dest / ".opencode" / "meta" / "pivot-state.json")
    restart_inputs = state.get("restart_surface_inputs") if isinstance(state, dict) else None
    if not isinstance(restart_inputs, dict) or restart_inputs.get("pivot_in_progress") is not False:
        raise RuntimeError("Pivot integration should clear pivot_in_progress once all routed downstream stages are completed.")
    if restart_inputs.get("pending_downstream_stages") not in ([], None):
        raise RuntimeError("Pivot integration should not leave pending downstream stages after all recorded completions.")
    if published["restart_surface_publication"]["status"] != "published":
        raise RuntimeError("Pivot integration should republish restart surfaces after pivot completion.")


def fixture_builder_integration(fixtures: dict[str, dict[str, Any]], workspace: Path) -> None:
    fixture_root = workspace / "gpttalker-fixtures"
    for slug in sorted(fixtures):
        dest = fixture_root / slug
        contract = build_fixture_family(slug, dest)
        if contract.get("slug") != slug:
            raise RuntimeError(f"Fixture builder should persist the canonical slug for `{slug}`.")
        if not isinstance(contract.get("expected_coverage"), list) or not contract["expected_coverage"]:
            raise RuntimeError(f"Fixture builder should persist expected coverage for `{slug}`.")
        contract_path = dest / ".opencode" / "meta" / "gpttalker-fixture.json"
        if not contract_path.exists():
            raise RuntimeError(f"Fixture builder should emit .opencode/meta/gpttalker-fixture.json for `{slug}`.")
        expected_finding_codes = contract.get("expected_finding_codes")
        if not isinstance(expected_finding_codes, list) or not expected_finding_codes:
            raise RuntimeError(f"Fixture builder should persist expected_finding_codes for `{slug}`.")
        command = [sys.executable, str(AUDIT), str(dest), "--format", "json", "--no-diagnosis-pack"]
        supporting_log = contract.get("supporting_log")
        if isinstance(supporting_log, str) and supporting_log.strip():
            command.extend(["--supporting-log", str(dest / supporting_log)])
        audit_payload = run_json(
            command,
            ROOT,
        )
        if not isinstance(audit_payload.get("findings"), list) or audit_payload.get("finding_count", 0) <= 0:
            raise RuntimeError(f"Fixture `{slug}` should produce actionable audit findings, not a no-op repo.")
        audit_codes = {
            str(item.get("code", "")).strip()
            for item in audit_payload.get("findings", [])
            if isinstance(item, dict) and str(item.get("code", "")).strip()
        }
        missing_codes = [code for code in expected_finding_codes if isinstance(code, str) and code not in audit_codes]
        if missing_codes:
            raise RuntimeError(
                f"Fixture `{slug}` did not trigger its declared invariant finding codes. Missing: {', '.join(missing_codes)}; "
                f"observed: {', '.join(sorted(audit_codes)) or 'none'}"
            )


def main() -> int:
    args = parse_args()
    fixtures = ensure_fixture_index()
    if args.list_fixtures:
        print(json.dumps(sorted(fixtures), indent=2))
        return 0
    with tempfile.TemporaryDirectory(prefix="scafforge-integration-") as workspace_root:
        workspace = Path(workspace_root)
        greenfield_integration(workspace)
        repair_integration(workspace)
        pivot_integration(workspace)
        fixture_builder_integration(fixtures, workspace)
    print("Scafforge integration test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
