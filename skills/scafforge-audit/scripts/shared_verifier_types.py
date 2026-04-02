from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Finding:
    code: str
    severity: str
    problem: str
    root_cause: str
    files: list[str]
    safer_pattern: str
    evidence: list[str]
    provenance: str = "script"
    remediation_action: str | None = None
    remediation_target: str | None = None
    is_user_action: bool = False
