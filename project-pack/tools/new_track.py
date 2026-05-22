#!/usr/bin/env python3
"""
new_track.py — Create the current-phase directory and initial TRACK_LOG.md for a registered track

Exit codes:
  0  Created successfully or already exists
  1  Preconditions not met (track not registered, phase mismatch, etc.)
  2  File missing or malformed

Usage:
  python3 tools/new_track.py --project-dir <path> --track-id <track_id>
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _artifacts import render_infra_track_log, render_research_track_log
from _cli import run_action
from _registry import (
    describe_phase_context,
    find_track,
    get_current_phase,
    get_cycle_label,
    load_registry as _shared_load_registry,
    validate_phase_track_match,
)
from _output import check_item


class NewTrackError(RuntimeError):
    """Input error for track directory creation."""


def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=NewTrackError)


def render_track_log(track: dict, registry: dict, current_phase: str) -> str:
    cycle_label = get_cycle_label(registry)

    if track["type"] == "research":
        return render_research_track_log(
            track,
            current_phase,
            cycle_label=cycle_label,
            created_reason="Current-phase initialization",
        )

    return render_infra_track_log(
        track,
        current_phase,
        cycle_label=cycle_label,
        created_reason="Current-phase initialization",
    )


def run(project_dir: Path, track_id: str) -> dict:
    registry = load_registry(str(project_dir))
    current_phase = get_current_phase(registry)
    track = find_track(registry, track_id)

    checks: list[dict] = []
    if track is None:
        return {
            "passed": False,
            "summary": f"Track creation failed: {track_id} is not in track_registry.yaml; run add-track or re-init first",
            "checks": [check_item("Track registered in track_registry.yaml", False, track_id)],
            "data": {"track_id": track_id, "created": False},
        }

    checks.append(check_item("Track registered in track_registry.yaml", True, track_id))
    checks.append(
        validate_phase_track_match(
            current_phase,
            track,
            action_label="create track directory",
            blocked_phase03_detail="phase_03_conclusion does not allow creating new track directories; finalize or reopen first",
            detail=describe_phase_context(registry),
        )
    )
    if not all(item["passed"] for item in checks):
        failure_reason = "; ".join(item["name"] for item in checks if not item["passed"])
        return {
            "passed": False,
            "summary": f"Track creation failed: {failure_reason}",
            "checks": checks,
            "data": {"track_id": track_id, "created": False, "current_phase": current_phase},
        }

    track_dir = project_dir / "prae" / "phases" / current_phase / "tracks" / track_id
    experiments_dir = track_dir / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    checks.append(check_item("phase directory created", True, str(track_dir)))

    src_root = project_dir / track.get("src", f"src/tracks/{track_id}/")
    src_root.mkdir(parents=True, exist_ok=True)
    checks.append(check_item("registry src directory exists", True, str(src_root)))

    if track.get("type") == "research":
        exp_src_dir = src_root / "experiments"
        impl_dir = src_root / "impl"
        exp_src_dir.mkdir(parents=True, exist_ok=True)
        impl_dir.mkdir(parents=True, exist_ok=True)
        checks.append(check_item("Research track experiments directory exists", True, str(exp_src_dir)))
        checks.append(check_item("Research track impl directory exists", True, str(impl_dir)))
    else:
        exp_src_dir = project_dir / "src" / "tracks" / track_id / "experiments"
        exp_src_dir.mkdir(parents=True, exist_ok=True)
        checks.append(check_item("Infrastructure track experiments directory exists", True, str(exp_src_dir)))

    log_path = track_dir / "TRACK_LOG.md"
    if log_path.exists():
        checks.append(check_item("TRACK_LOG.md already exists (kept, not overwritten)", True, str(log_path)))
        summary = f"Track ready: {track_id} (current-phase directory already exists)"
        created = False
    else:
        log_path.write_text(render_track_log(track, registry, current_phase), encoding="utf-8")
        checks.append(check_item("TRACK_LOG.md initialized", True, str(log_path)))
        summary = f"Track created: {track_id}"
        created = True

    return {
        "passed": True,
        "summary": summary,
        "checks": checks,
        "data": {
            "track_id": track_id,
            "type": track.get("type"),
            "current_phase": current_phase,
            "track_dir": str(track_dir),
            "track_log_path": str(log_path),
            "created": created,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the current-phase directory and TRACK_LOG.md for a registered track")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    parser.add_argument("--track-id", required=True, help="Track ID")
    args = parser.parse_args()

    run_action(lambda: run(Path(args.project_dir), args.track_id), NewTrackError)


if __name__ == "__main__":
    main()
