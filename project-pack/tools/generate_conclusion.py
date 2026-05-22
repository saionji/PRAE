#!/usr/bin/env python3
"""
generate_conclusion.py — generate or refresh the Phase 3 CONCLUSION.md

Exit codes:
  0  CONCLUSION.md generated successfully
  2  file missing, format error, or not currently in Phase 3

Usage:
  python3 tools/generate_conclusion.py --project-dir <path>
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _conclusion_docs import (
    default_final_decision_section,
    extract_final_decision_section,
    render_conclusion_document,
)
from _gate_utils import collapse_text
from _registry import get_cycle_label, get_recorded_phase, load_registry as _shared_load_registry
from _output import check_item, error, result


class ConclusionError(RuntimeError):
    """Raised when conclusion generation preconditions are not met."""


def load_registry(project_dir: Path) -> dict:
    return _shared_load_registry(project_dir, error_cls=ConclusionError)

def find_track_log(project_dir: Path, track: dict) -> Path | None:
    track_id = track["id"]
    if track.get("type") == "infrastructure":
        candidate = project_dir / "prae" / "phases" / "phase_00_infra" / "tracks" / track_id / "TRACK_LOG.md"
        return candidate if candidate.exists() else None

    for phase_name in ("phase_03_conclusion", "phase_02_validation", "phase_01_research"):
        candidate = project_dir / "prae" / "phases" / phase_name / "tracks" / track_id / "TRACK_LOG.md"
        if candidate.exists():
            return candidate

    history_root = project_dir / "prae" / "history"
    if history_root.is_dir():
        cycle_dirs: list[tuple[int, Path]] = []
        for item in history_root.iterdir():
            if not item.is_dir():
                continue
            match = re.fullmatch(r"cycle_(\d+)", item.name)
            if not match:
                continue
            cycle_dirs.append((int(match.group(1)), item))
        for _, cycle_dir in sorted(cycle_dirs, reverse=True):
            for phase_name in ("phase_03_conclusion", "phase_02_validation", "phase_01_research"):
                candidate = cycle_dir / "phases" / phase_name / "tracks" / track_id / "TRACK_LOG.md"
                if candidate.exists():
                    return candidate
    return None


def extract_section(content: str, title: str) -> str:
    match = re.search(rf"{re.escape(title)}\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not match:
        return ""
    return match.group(1).strip()


def summarize_track(project_dir: Path, track: dict) -> str:
    if track.get("evidence_summary"):
        return collapse_text(str(track["evidence_summary"]))

    log_path = find_track_log(project_dir, track)
    if log_path and log_path.exists():
        content = log_path.read_text(encoding="utf-8")
        for title in ("## Final Conclusion", "## Evidence Summary", "## Selection Goal"):
            section = extract_section(content, title)
            if section:
                for line in section.splitlines():
                    cleaned = line.strip().lstrip("-").strip()
                    if cleaned:
                        return collapse_text(cleaned)

    state = track.get("state", "unknown")
    if track.get("type") == "infrastructure":
        return "The infrastructure track has completed its foundational record and can stably provide capabilities to research tracks."
    if state == "GRADUATED":
        return "The validation-phase conclusion supports promoting this track to PDAE engineering."
    if state == "MERGED":
        merged_into = track.get("merged_into") or "to be filled in"
        return f"This track has been merged into {merged_into} and is no longer advanced independently."
    if state == "KILLED":
        return "Evidence insufficient or hypothesis disproved; the track has been terminated."
    return f"Current state is {state}."


def build_project_conclusion(registry: dict) -> str:
    research_tracks = [t for t in registry.get("tracks", []) if t.get("type") == "research"]
    graduated = [t for t in research_tracks if t.get("state") == "GRADUATED"]
    killed = [t for t in research_tracks if t.get("state") == "KILLED"]
    merged = [t for t in research_tracks if t.get("state") == "MERGED"]

    if graduated:
        return (
            f"This project has completed research convergence, identifying {len(graduated)} engineerable tracks; "
            f"{len(killed)} tracks were terminated and {len(merged)} tracks were merged into other directions."
        )
    return (
        "This project has completed research wrap-up, but currently has no GRADUATED track ready for direct engineering; "
        "absent new evidence, a human should assess whether to archive it."
    )


def build_track_outcomes(project_dir: Path, registry: dict) -> str:
    rows: list[str] = []
    for track in registry.get("tracks", []):
        note_parts: list[str] = []
        if track.get("merged_into"):
            note_parts.append(f"merged_into={track['merged_into']}")
        if track.get("pdae_project"):
            note_parts.append(f"PDAE={track['pdae_project']}")
        note = "; ".join(note_parts) if note_parts else "—"
        rows.append(
            f"| `{track['id']}` | {track.get('state', 'unknown')} | {summarize_track(project_dir, track)} | {note} |"
        )
    return "\n".join(rows)


def build_pdae_links(registry: dict) -> str:
    graduated = [t for t in registry.get("tracks", []) if t.get("type") == "research" and t.get("state") == "GRADUATED"]
    if not graduated:
        return "| `—` | `no GRADUATED track currently` |"

    rows = []
    for track in graduated:
        path = track.get("pdae_project") or "to be filled in"
        rows.append(f"| `{track['id']}` | `{path}` |")
    return "\n".join(rows)


def build_unresolved_issues(registry: dict) -> str:
    issues: list[str] = []
    graduated = [t for t in registry.get("tracks", []) if t.get("type") == "research" and t.get("state") == "GRADUATED"]
    for track in graduated:
        if not track.get("pdae_project"):
            issues.append(f"- `{track['id']}` is GRADUATED but has no registered PDAE project path yet.")

    non_terminal = [
        t["id"] for t in registry.get("tracks", [])
        if t.get("type") == "research" and t.get("state") not in {"KILLED", "MERGED", "GRADUATED"}
    ]
    if non_terminal:
        issues.append(f"- Some research tracks have not reached a terminal state: {', '.join(non_terminal)}.")

    if not issues:
        issues.append("- No significant open issues.")
    return "\n".join(issues)


def render_conclusion(project_dir: Path, registry: dict, final_decision_section: str) -> str:
    return render_conclusion_document(
        project_name=registry.get("project", "unknown-project"),
        cycle_label=get_cycle_label(registry),
        project_conclusion=build_project_conclusion(registry),
        track_outcomes_rows=build_track_outcomes(project_dir, registry),
        pdae_links_rows=build_pdae_links(registry),
        unresolved_issues=build_unresolved_issues(registry),
        final_decision_section=final_decision_section,
    )


def write_conclusion(project_dir: Path) -> dict:
    registry = load_registry(project_dir)
    current_phase = get_recorded_phase(registry, "")
    if current_phase != "phase_03_conclusion":
        raise ConclusionError(f"Current phase is {current_phase}; only phase_03_conclusion can generate CONCLUSION.md")

    conclusion_path = project_dir / "prae" / "phases" / "phase_03_conclusion" / "CONCLUSION.md"
    conclusion_path.parent.mkdir(parents=True, exist_ok=True)

    final_decision_section = default_final_decision_section()
    if conclusion_path.exists():
        final_decision_section = extract_final_decision_section(conclusion_path.read_text(encoding="utf-8"))

    content = render_conclusion(project_dir, registry, final_decision_section)
    conclusion_path.write_text(content, encoding="utf-8")

    graduated = [t["id"] for t in registry.get("tracks", []) if t.get("type") == "research" and t.get("state") == "GRADUATED"]
    with_pdae = [
        t["id"] for t in registry.get("tracks", [])
        if t.get("type") == "research" and t.get("state") == "GRADUATED" and t.get("pdae_project")
    ]
    return {
        "summary": "CONCLUSION.md generated",
        "checks": [
            check_item("CONCLUSION.md written", True, str(conclusion_path)),
            check_item("Current phase is phase_03_conclusion", True),
        ],
        "data": {
            "path": str(conclusion_path),
            "graduated_tracks": graduated,
            "graduated_with_pdae": with_pdae,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or refresh the Phase 3 CONCLUSION.md")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    args = parser.parse_args()

    try:
        payload = write_conclusion(Path(args.project_dir))
    except ConclusionError as exc:
        error(str(exc))

    result(True, payload["checks"], payload["summary"], data=payload["data"])


if __name__ == "__main__":
    main()
