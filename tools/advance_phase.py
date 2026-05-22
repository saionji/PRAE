#!/usr/bin/env python3
"""
advance_phase.py — advance to the next phase after PHASE_GATE.md gets human approval

Exit codes:
  0  advanced successfully
  1  approval incomplete or advancement conditions not met
  2  file missing, format error, or already at the final phase

Usage:
  python3 tools/advance_phase.py --project-dir <path>
"""
from __future__ import annotations

import argparse
import datetime
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _artifacts import render_research_track_log as _render_research_track_log
from _cli import emit_payload
from _registry import get_cycle_label, get_phase_override, get_recorded_phase, save_registry
from _phase_docs import PHASE_TRANSITIONS, render_phase_brief
from _output import check_item, error
from check_phase_gate import PhaseGateError, evaluate_approval, load_registry
from generate_conclusion import ConclusionError, write_conclusion


def selected_tracks_for_target(target_phase: str, registry: dict) -> list[dict]:
    tracks = registry.get("tracks", [])
    if target_phase == "phase_01_research":
        return [t for t in tracks if t.get("type") == "research"]
    if target_phase == "phase_02_validation":
        return [t for t in tracks if t.get("type") == "research" and t.get("state") == "ACTIVE"]
    if target_phase == "phase_03_conclusion":
        return [t for t in tracks if t.get("type") == "research" and t.get("state") == "GRADUATED"]
    return []


def render_research_track_log(track: dict, target_phase: str, cycle_label: str = "cycle_1") -> str:
    return _render_research_track_log(
        track,
        target_phase,
        cycle_label=cycle_label,
        created_reason="initialized after phase advancement",
    )


def ensure_terminal_metadata(registry: dict, current_phase: str) -> int:
    """Compatibility fallback: backfill concluded_at missing from legacy data. The formal path should be written by update_track_state.py."""
    if current_phase not in {"phase_01_research", "phase_02_validation"}:
        return 0

    today = str(datetime.date.today())
    updated = 0
    for track in registry.get("tracks", []):
        if track.get("type") != "research":
            continue
        if track.get("state") in {"KILLED", "MERGED", "GRADUATED"} and not track.get("concluded_at"):
            track["concluded_at"] = today
            updated += 1
    return updated


def create_phase_brief(project_dir: Path, target_phase: str, registry: dict, selected_tracks: list[dict]) -> tuple[Path, bool]:
    phase_dir = project_dir / "prae" / "phases" / target_phase
    phase_dir.mkdir(parents=True, exist_ok=True)
    brief_path = phase_dir / "PHASE_BRIEF.md"
    created = False
    if not brief_path.exists():
        brief_path.write_text(render_phase_brief(target_phase, registry, selected_tracks), encoding="utf-8")
        created = True
    return brief_path, created


def initialize_target_track_logs(project_dir: Path, current_phase: str, target_phase: str,
                                 selected_tracks: list[dict]) -> tuple[int, int, int]:
    created_logs = 0
    copied_logs = 0
    existing_logs = 0
    phase_tracks_dir = project_dir / "prae" / "phases" / target_phase / "tracks"
    registry = load_registry(str(project_dir))
    cycle_label = get_cycle_label(registry)

    for track in selected_tracks:
        track_dir = phase_tracks_dir / track["id"]
        (track_dir / "experiments").mkdir(parents=True, exist_ok=True)
        log_path = track_dir / "TRACK_LOG.md"
        if log_path.exists():
            existing_logs += 1
            continue

        prev_log = project_dir / "prae" / "phases" / current_phase / "tracks" / track["id"] / "TRACK_LOG.md"
        if prev_log.exists():
            shutil.copy2(prev_log, log_path)
            copied_logs += 1
        else:
            log_path.write_text(
                render_research_track_log(track, target_phase, cycle_label=cycle_label),
                encoding="utf-8",
            )
            created_logs += 1

    return created_logs, copied_logs, existing_logs


def advance_phase(project_dir: Path) -> dict:
    registry = load_registry(str(project_dir))
    override = get_phase_override(registry)
    if override:
        error("current_phase_override detected as active; the normal advance-phase is suspended, please complete the exception handling and remove the override first")

    current_phase = get_recorded_phase(registry, "")
    if current_phase not in PHASE_TRANSITIONS:
        error(f"current phase {current_phase} cannot advance further (may already be at the final phase)")

    try:
        approval = evaluate_approval(str(project_dir), registry)
    except PhaseGateError as exc:
        error(str(exc))

    checks = list(approval["checks"])
    if not approval["passed"]:
        return {
            "passed": False,
            "summary": "advancement failed: PHASE_GATE.md does not yet meet the approval requirements",
            "checks": checks,
            "data": {
                "current_phase": current_phase,
                "target_phase": PHASE_TRANSITIONS[current_phase],
                "advanced": False,
            },
        }

    target_phase = PHASE_TRANSITIONS[current_phase]
    selected_tracks = selected_tracks_for_target(target_phase, registry)

    terminal_updates = ensure_terminal_metadata(registry, current_phase)
    checks.append(check_item("compatibility: backfilled concluded_at for terminal-state tracks that were missing it", True, f"updated={terminal_updates}"))

    registry["current_phase"] = target_phase
    registry["updated"] = str(datetime.date.today())
    registry_path = save_registry(project_dir, registry)
    checks.append(check_item("track_registry.yaml updated current_phase", True, str(registry_path)))

    brief_path, brief_created = create_phase_brief(project_dir, target_phase, registry, selected_tracks)
    checks.append(check_item("target phase PHASE_BRIEF.md ready", True,
                             f"{brief_path} ({'created' if brief_created else 'kept'})"))

    created_logs, copied_logs, existing_logs = initialize_target_track_logs(
        project_dir, current_phase, target_phase, selected_tracks
    )
    checks.append(check_item("target phase TRACK_LOG.md ready", True,
                             f"created={created_logs} copied={copied_logs} existing={existing_logs}"))

    conclusion_path = ""
    if target_phase == "phase_03_conclusion":
        try:
            conclusion_payload = write_conclusion(project_dir)
            conclusion_path = conclusion_payload["data"]["path"]
            checks.append(check_item("CONCLUSION.md generated", True, conclusion_path))
        except ConclusionError as exc:
            checks.append(check_item("CONCLUSION.md generated", False, str(exc)))

    passed = all(c["passed"] for c in checks)
    return {
        "passed": passed,
        "summary": f"advanced to {target_phase}",
        "checks": checks,
        "data": {
            "from_phase": current_phase,
            "target_phase": target_phase,
            "registry_path": str(registry_path),
            "phase_brief_path": str(brief_path),
            "selected_tracks": [track["id"] for track in selected_tracks],
            "created_logs": created_logs,
            "copied_logs": copied_logs,
            "existing_logs": existing_logs,
            "conclusion_path": conclusion_path,
            "advanced": passed,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Advance the PRAE project to the next phase (after human approval)")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    args = parser.parse_args()

    emit_payload(advance_phase(Path(args.project_dir)))


if __name__ == "__main__":
    main()
