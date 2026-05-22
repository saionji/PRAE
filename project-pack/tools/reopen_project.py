#!/usr/bin/env python3
"""
reopen_project.py — reopen the project to Phase 1 based on an approved CONTINUE decision

Exit codes:
  0  reopened successfully
  1  the CONTINUE decision does not yet meet the execution conditions
  2  file missing or format error

Usage:
  python3 tools/reopen_project.py --project-dir <path>
"""
from __future__ import annotations

import argparse
import datetime
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _registry import get_recorded_phase, save_registry
from _output import check_item
from _phase_docs import render_phase_brief
from check_conclusion import evaluate_conclusion
from generate_conclusion import ConclusionError, load_registry


REOPEN_TARGET_PHASE = "phase_01_research"
ARCHIVE_PHASE_DIRS = [
    "phase_01_research",
    "phase_02_validation",
    "phase_03_conclusion",
]


def get_current_cycle(registry: dict) -> int:
    try:
        cycle = int(registry.get("current_cycle", 1))
    except (TypeError, ValueError):
        return 1
    return cycle if cycle >= 1 else 1


def archive_cycle_phases(project_dir: Path, cycle_num: int) -> list[Path]:
    archived_paths: list[Path] = []
    history_root = project_dir / "prae" / "history" / f"cycle_{cycle_num}" / "phases"
    history_root.mkdir(parents=True, exist_ok=True)
    phases_root = project_dir / "prae" / "phases"

    for phase_name in ARCHIVE_PHASE_DIRS:
        src = phases_root / phase_name
        if not src.exists():
            continue
        dst = history_root / phase_name
        shutil.move(str(src), str(dst))
        archived_paths.append(dst)
    return archived_paths


def write_reopen_phase_brief(project_dir: Path, registry: dict) -> Path:
    phase_dir = project_dir / "prae" / "phases" / REOPEN_TARGET_PHASE
    phase_dir.mkdir(parents=True, exist_ok=True)
    brief_path = phase_dir / "PHASE_BRIEF.md"
    brief_path.write_text(render_phase_brief(REOPEN_TARGET_PHASE, registry, []), encoding="utf-8")
    return brief_path


def reopen_project(project_dir: Path) -> dict:
    evaluation = evaluate_conclusion(str(project_dir))
    checks = list(evaluation["checks"])

    approved_yes = evaluation["data"]["approved"] == "yes"
    decision_continue = evaluation["data"]["decision"] == "CONTINUE"
    checks.append(check_item("CONCLUSION is APPROVED: yes", approved_yes, f"current value={evaluation['data']['approved']}"))
    checks.append(check_item("DECISION: CONTINUE", decision_continue, f"current value={evaluation['data']['decision']}"))

    if not evaluation["passed"] or not approved_yes or not decision_continue:
        return {
            "passed": False,
            "summary": "project reopen failed: CONCLUSION.md does not yet meet the CONTINUE execution conditions",
            "checks": checks,
            "data": {"reopened": False, **evaluation["data"]},
        }

    registry = load_registry(project_dir)
    current_phase = get_recorded_phase(registry, "")
    checks.append(check_item("current phase is phase_03_conclusion", current_phase == "phase_03_conclusion", current_phase))
    if current_phase != "phase_03_conclusion":
        return {
            "passed": False,
            "summary": f"project reopen failed: current phase is {current_phase}",
            "checks": checks,
            "data": {"reopened": False, **evaluation["data"]},
        }

    current_cycle = get_current_cycle(registry)
    archived_dirs = archive_cycle_phases(project_dir, current_cycle)
    for phase_name in ARCHIVE_PHASE_DIRS:
        archived = next((path for path in archived_dirs if path.name == phase_name), None)
        detail = str(archived) if archived else "source directory does not exist, skipped"
        checks.append(check_item(f"archive {phase_name}", True, detail))

    today = str(datetime.date.today())
    registry["current_cycle"] = current_cycle + 1
    registry["current_phase"] = REOPEN_TARGET_PHASE
    registry["project_decision"] = "CONTINUE"
    registry["project_approver"] = evaluation["data"]["approver"]
    registry["project_decided_at"] = evaluation["data"]["approved_at"]
    registry["project_reopened_at"] = today
    registry["updated"] = today
    registry.pop("project_finalized_at", None)
    registry.pop("archived_at", None)

    registry_path = save_registry(project_dir, registry)
    checks.append(check_item("track_registry.yaml switched back to phase_01_research", True, str(registry_path)))
    checks.append(check_item("current_cycle incremented", True, f"{current_cycle} -> {registry['current_cycle']}"))

    brief_path = write_reopen_phase_brief(project_dir, registry)
    checks.append(check_item("new Phase 1 PHASE_BRIEF.md generated", True, str(brief_path)))

    return {
        "passed": True,
        "summary": "project reopened to Phase 1 based on the CONTINUE decision",
        "checks": checks,
        "data": {
            **evaluation["data"],
            "registry_path": str(registry_path),
            "phase_brief_path": str(brief_path),
            "archived_paths": [str(path) for path in archived_dirs],
            "target_phase": REOPEN_TARGET_PHASE,
            "from_cycle": current_cycle,
            "to_cycle": registry["current_cycle"],
            "reopened": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Reopen a PRAE project from a CONTINUE decision in CONCLUSION.md")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    args = parser.parse_args()

    run_action(lambda: reopen_project(Path(args.project_dir)), ConclusionError)


if __name__ == "__main__":
    main()
