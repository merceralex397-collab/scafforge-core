from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


VERIFIER_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts" / "shared_verifier.py"
MODULE_SPEC = spec_from_file_location("scafforge_shared_verifier", VERIFIER_SCRIPT_PATH)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise RuntimeError(f"Unable to load verifier module from {VERIFIER_SCRIPT_PATH}")

VERIFIER_MODULE = module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = VERIFIER_MODULE
MODULE_SPEC.loader.exec_module(VERIFIER_MODULE)

Finding = VERIFIER_MODULE.Finding
audit_repo = VERIFIER_MODULE.audit_repo

__all__ = ["Finding", "audit_repo"]
