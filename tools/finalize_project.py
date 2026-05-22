#!/usr/bin/env python3
"""
finalize_project.py — record the project's final-state decision based on an approved CONCLUSION.md

Exit codes:
  0  recorded successfully
  1  final decision does not yet meet the conditions for execution
  2  file missing or format error

Usage:
  python3 tools/finalize_project.py --project-dir <path>
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _registry import save_registry
from _output import check_item
from check_conclusion import evaluate_conclusion
from generate_conclusion import ConclusionError, load_registry


def finalize_project(project_dir: Path) -> dict:
    evaluation = evaluate_conclusion(str(project_dir))
    checks = list(evaluation["checks"])

    approved_yes = evaluation["data"]["approved"] == "yes"
    checks.append(check_item("CONCLUSION is APPROVED: yes", approved_yes, f"current value={evaluation['data']['approved']}"))
    terminal_decision = evaluation["data"]["decision"] in {"ARCHIVED", "GRADUATED_TO_PDAE"}
    checks.append(check_item(
        "DECISION is terminal (ARCHIVED / GRADUATED_TO_PDAE)",
        terminal_decision,
        f"current value={evaluation['data']['decision']}; for CONTINUE use reopen_project.py instead",
    ))

    if not evaluation["passed"] or not approved_yes or not terminal_decision:
        return {
            "passed": False,
            "summary": "Project finalization failed: CONCLUSION.md does not yet meet the terminal-decision requirements",
            "checks": checks,
            "data": {"finalized": False, **evaluation["data"]},
        }

    registry = load_registry(project_dir)
    decision = evaluation["data"]["decision"]
    approver = evaluation["data"]["approver"]
    approved_at = evaluation["data"]["approved_at"]

    registry["project_decision"] = decision
    registry["project_approver"] = approver
    registry["project_decided_at"] = approved_at
    registry["project_finalized_at"] = str(datetime.date.today())
    registry["updated"] = str(datetime.date.today())
    if decision == "ARCHIVED":
        registry["archived_at"] = approved_at
    elif "archived_at" in registry:
        registry.pop("archived_at")

    registry_path = save_registry(project_dir, registry)
    checks.append(check_item("track_registry.yaml recorded the project's final-state decision", True, str(registry_path)))

    return {
        "passed": True,
        "summary": f"Project final-state decision recorded: {decision}",
        "checks": checks,
        "data": {
            **evaluation["data"],
            "registry_path": str(registry_path),
            "finalized": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Record the project's final-state decision from CONCLUSION.md")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    args = parser.parse_args()

    run_action(lambda: finalize_project(Path(args.project_dir)), ConclusionError)


if __name__ == "__main__":
    main()
