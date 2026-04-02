from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


AUDIT_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts" / "audit_repo_process.py"
MODULE_SPEC = spec_from_file_location("scafforge_audit_repo_process", AUDIT_SCRIPT_PATH)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise RuntimeError(f"Unable to load audit module from {AUDIT_SCRIPT_PATH}")

AUDIT_MODULE = module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = AUDIT_MODULE
MODULE_SPEC.loader.exec_module(AUDIT_MODULE)

audit_repo = AUDIT_MODULE.audit_repo
current_package_commit = AUDIT_MODULE.current_package_commit
emit_diagnosis_pack = AUDIT_MODULE.emit_diagnosis_pack
load_latest_previous_diagnosis = AUDIT_MODULE.load_latest_previous_diagnosis
load_latest_previous_diagnosis_with_supporting_logs = AUDIT_MODULE.load_latest_previous_diagnosis_with_supporting_logs
manifest_supporting_logs = AUDIT_MODULE.manifest_supporting_logs
repair_routed_codes_from_manifest = AUDIT_MODULE.repair_routed_codes_from_manifest
select_diagnosis_destination = AUDIT_MODULE.select_diagnosis_destination
supporting_log_paths = AUDIT_MODULE.supporting_log_paths
main = AUDIT_MODULE.main

__all__ = [
    "audit_repo",
    "current_package_commit",
    "emit_diagnosis_pack",
    "load_latest_previous_diagnosis",
    "load_latest_previous_diagnosis_with_supporting_logs",
    "manifest_supporting_logs",
    "repair_routed_codes_from_manifest",
    "select_diagnosis_destination",
    "supporting_log_paths",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
