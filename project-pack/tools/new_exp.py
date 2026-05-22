#!/usr/bin/env python3
"""
new_exp.py — Create a new EXP_NNN.md / EXP_NNN.py for a materialized track

Exit codes:
  0  Created successfully
  1  Preconditions not met (phase mismatch, track directory missing, etc.)
  2  File missing or malformed

Usage:
  python3 tools/new_exp.py --project-dir <path> --track-id <track_id> [--title <title>]
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _artifacts import render_exp_markdown, render_exp_python
from _cli import run_action
from _registry import (
    describe_phase_context,
    find_track,
    get_current_phase,
    load_registry as _shared_load_registry,
    save_registry,
    validate_phase_track_match,
)
from _output import check_item


class NewExperimentError(RuntimeError):
    """Input error for experiment creation."""


def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=NewExperimentError)


def find_next_exp_id(exp_dir: Path) -> tuple[str, str]:
    max_num = 0
    pattern = re.compile(r"^EXP_(\d{3})\.md$")
    for path in exp_dir.glob("EXP_*.md"):
        match = pattern.match(path.name)
        if match:
            max_num = max(max_num, int(match.group(1)))
    next_num = max_num + 1
    return f"EXP_{next_num:03d}", f"{next_num:03d}"


def run(project_dir: Path, track_id: str, title: str) -> dict:
    registry = load_registry(str(project_dir))
    current_phase = get_current_phase(registry)
    track = find_track(registry, track_id)

    checks: list[dict] = []
    if track is None:
        return {
            "passed": False,
            "summary": f"Experiment creation failed: {track_id} is not in track_registry.yaml; run add-track or re-init first",
            "checks": [check_item("Track registered in track_registry.yaml", False, track_id)],
            "data": {"track_id": track_id, "created": False},
        }

    checks.append(check_item("Track registered in track_registry.yaml", True, track_id))
    checks.append(
        validate_phase_track_match(
            current_phase,
            track,
            action_label="create experiment",
            blocked_phase03_detail="phase_03_conclusion does not allow creating new experiments; finalize or reopen first",
            detail=describe_phase_context(registry),
        )
    )

    track_dir = project_dir / "prae" / "phases" / current_phase / "tracks" / track_id
    exp_dir = track_dir / "experiments"
    track_dir_ok = track_dir.is_dir()
    checks.append(check_item("Current-phase track directory created", track_dir_ok, str(track_dir)))

    if not all(item["passed"] for item in checks):
        failure_reason = "; ".join(item["name"] for item in checks if not item["passed"])
        return {
            "passed": False,
            "summary": f"Experiment creation failed: {failure_reason}",
            "checks": checks,
            "data": {"track_id": track_id, "created": False, "current_phase": current_phase},
        }

    exp_dir.mkdir(parents=True, exist_ok=True)
    exp_id, exp_num = find_next_exp_id(exp_dir)
    exp_md_path = exp_dir / f"{exp_id}.md"
    exp_py_path = project_dir / "src" / "tracks" / track_id / "experiments" / f"{exp_id}.py"
    exp_py_path.parent.mkdir(parents=True, exist_ok=True)

    template_path = project_dir / "prae" / "templates" / "EXP_NNN.template.md"
    if not template_path.exists():
        raise NewExperimentError(f"Template file not found: {template_path}")

    template = template_path.read_text(encoding="utf-8")
    exp_md_path.write_text(render_exp_markdown(template, exp_num, track_id, title), encoding="utf-8")
    exp_py_path.write_text(render_exp_python(exp_id, title, track_id, exp_md_path.relative_to(project_dir)), encoding="utf-8")
    checks.append(check_item("EXP_NNN.md created", True, str(exp_md_path)))
    checks.append(check_item("EXP_NNN.py created", True, str(exp_py_path)))

    track["experiments"] = track.get("experiments", 0) + 1
    registry["updated"] = str(datetime.date.today())
    registry_path = save_registry(project_dir, registry)
    checks.append(check_item("track_registry.yaml experiments count updated", True, str(track["experiments"])))

    return {
        "passed": True,
        "summary": f"Experiment created: {track_id} / {exp_id}",
        "checks": checks,
        "data": {
            "track_id": track_id,
            "exp_id": exp_id,
            "title": title,
            "current_phase": current_phase,
            "exp_md_path": str(exp_md_path),
            "exp_py_path": str(exp_py_path),
            "created": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a new EXP_NNN.md / EXP_NNN.py for a materialized track")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    parser.add_argument("--track-id", required=True, help="Track ID")
    parser.add_argument("--title", default="Experiment", help="Experiment title")
    args = parser.parse_args()

    run_action(
        lambda: run(Path(args.project_dir), args.track_id, args.title),
        NewExperimentError,
    )


if __name__ == "__main__":
    main()
