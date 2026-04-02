from __future__ import annotations

import argparse
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_repo_process import main as audit_repo_process_main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Standalone entry point for the full Scafforge audit suite. Pass a repo path and optional diagnosis-pack output directory."
    )
    parser.add_argument("repo_root", help="Repository root to audit.")
    parser.add_argument("--supporting-log", action="append", default=[], help="Optional supporting log or transcript path. May be repeated.")
    parser.add_argument("--format", choices=("markdown", "json", "both"), default="both")
    parser.add_argument("--diagnosis-output-dir", help="Optional diagnosis-pack destination.")
    parser.add_argument(
        "--diagnosis-kind",
        choices=("initial_diagnosis", "post_package_revalidation", "post_repair_verification"),
        default="initial_diagnosis",
    )
    parser.add_argument("--fail-on", choices=("never", "warning", "error"), default="never")
    parser.add_argument("--no-diagnosis-pack", action="store_true", help="Skip writing the diagnosis pack.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    argv = [
        "audit_repo_process.py",
        args.repo_root,
        "--format",
        args.format,
        "--diagnosis-kind",
        args.diagnosis_kind,
        "--fail-on",
        args.fail_on,
    ]
    for log_path in args.supporting_log:
        argv.extend(["--supporting-log", log_path])
    if args.diagnosis_output_dir:
        argv.extend(["--diagnosis-output-dir", args.diagnosis_output_dir])
    if args.no_diagnosis_pack:
        argv.append("--no-diagnosis-pack")
    old_argv = sys.argv
    try:
      sys.argv = argv
      return audit_repo_process_main()
    finally:
      sys.argv = old_argv


if __name__ == "__main__":
    raise SystemExit(main())