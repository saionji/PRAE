#!/usr/bin/env python3
"""
record_result.py — Formally sync experiment results into TRACK_LOG.md and track_registry.yaml

Exit codes:
  0  Recorded successfully
  1  Recording conditions not met
  2  File missing or malformed

Usage:
  python3 tools/record_result.py \
    --project-dir <path> \
    --track-id <track_id> \
    --exp-id <EXP_001>
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _artifacts import upsert_decision_log_row
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
from update_track_state import sanitize_table_cell


class RecordResultError(RuntimeError):
    """Input error for experiment result recording."""


def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=RecordResultError)


def extract_goal(content: str) -> str:
    match = re.search(r"## Goal\n+(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not match:
        return "(see experiment record)"
    lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    if not lines:
        return "(see experiment record)"
    return lines[0]


def extract_conclusion(content: str) -> str:
    match = re.search(r"\*\*Conclusion\*\*[:：]\s*(.+)", content)
    if match:
        return match.group(1).strip()

    section = re.search(r"## Conclusion\n+(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not section:
        return "(see experiment record)"
    lines = [line.strip() for line in section.group(1).splitlines() if line.strip()]
    return lines[0] if lines else "(see experiment record)"


def ensure_exp_completed(content: str) -> list[str]:
    issues: list[str] = []
    if "{{paste key experiment output}}" in content:
        issues.append("Result section not filled in")
    if "supports / falsifies / partially supports the hypothesis" in content:
        issues.append("Conclusion section not clarified")
    if "## Result" not in content:
        issues.append("Missing ## Result")
    if "## Conclusion" not in content:
        issues.append("Missing ## Conclusion")
    return issues


def extract_state_suggestion(content: str) -> str | None:
    match = re.search(r"Recommended state change[:：]\s*(.+)", content)
    return match.group(1).strip() if match else None


def upsert_experiment_row(content: str, exp_id: str, row: str) -> str:
    row_pattern = re.compile(rf"^\|\s*{re.escape(exp_id)}\s*\|.*$", re.MULTILINE)
    if row_pattern.search(content):
        return row_pattern.sub(row, content, count=1)

    placeholder_pattern = re.compile(r"^\|\s*—\s*\|\s*—\s*\|.*$", re.MULTILINE)
    if placeholder_pattern.search(content):
        return placeholder_pattern.sub(row, content, count=1)

    table_match = re.search(r"(## Experiments\n.*?\n\|[-|]+\|\n)", content, re.DOTALL)
    if not table_match:
        raise RecordResultError("TRACK_LOG.md is missing the Experiments table")
    insert_at = table_match.end(1)
    return content[:insert_at] + row + "\n" + content[insert_at:]


def upsert_evidence_summary(content: str, exp_id: str, summary_line: str) -> str:
    section_match = re.search(r"(## Evidence Summary\n.*?)(\n---|\Z)", content, re.DOTALL)
    if not section_match:
        raise RecordResultError("TRACK_LOG.md is missing the Evidence Summary section")

    section_body = section_match.group(1)
    line_pattern = re.compile(rf"^- \*\*.*?{re.escape(exp_id)}\*\*.*$", re.MULTILINE)
    if line_pattern.search(section_body):
        new_body = line_pattern.sub(summary_line, section_body, count=1)
    else:
        new_body = section_body
        new_body = re.sub(r"^- No (?:experiment|selection) records yet\.\s*$", "", new_body, flags=re.MULTILINE).rstrip()
        new_body = new_body + "\n" + summary_line + "\n"

    return content[:section_match.start(1)] + new_body + content[section_match.end(1):]


def record_result(project_dir: Path, track_id: str, exp_id: str) -> dict:
    registry = load_registry(str(project_dir))
    track = find_track(registry, track_id)
    if track is None:
        raise RecordResultError(f"Track {track_id} is not in track_registry.yaml")
    current_phase = get_current_phase(registry)

    exp_md = (
        project_dir / "prae" / "phases" / current_phase / "tracks" / track_id / "experiments" / f"{exp_id}.md"
    )
    log_path = project_dir / "prae" / "phases" / current_phase / "tracks" / track_id / "TRACK_LOG.md"

    checks: list[dict] = [
        check_item("Experiment record exists", exp_md.exists(), str(exp_md)),
        check_item("TRACK_LOG.md exists", log_path.exists(), str(log_path)),
    ]
    if not exp_md.exists() or not log_path.exists():
        return {
            "passed": False,
            "summary": f"Experiment result recording failed: required file missing ({track_id} / {exp_id})",
            "checks": checks,
            "data": {"track_id": track_id, "exp_id": exp_id, "recorded": False},
        }

    exp_content = exp_md.read_text(encoding="utf-8")
    checks.append(
        validate_phase_track_match(
            current_phase,
            track,
            action_label="record experiment result",
            blocked_phase03_detail="phase_03_conclusion does not allow further experiment recording; finalize or reopen first",
            detail=describe_phase_context(registry),
        )
    )
    issues = ensure_exp_completed(exp_content)
    checks.append(check_item(
        "EXP_NNN.md has completed Result / Conclusion",
        not issues,
        "; ".join(issues),
    ))
    if issues or not all(item["passed"] for item in checks):
        failure_reason = "; ".join(
            item["name"] for item in checks if not item["passed"]
        ) or f"{exp_id} is not yet fully filled in"
        return {
            "passed": False,
            "summary": f"Experiment result recording failed: {failure_reason}",
            "checks": checks,
            "data": {"track_id": track_id, "exp_id": exp_id, "recorded": False},
        }

    goal = extract_goal(exp_content)
    conclusion = extract_conclusion(exp_content)
    suggestion = extract_state_suggestion(exp_content)
    today = str(datetime.date.today())

    log_content = log_path.read_text(encoding="utf-8")
    row = f"| {exp_id} | {today} | {goal[:50]} | {conclusion} | [{exp_id}.md](experiments/{exp_id}.md) |"
    summary_line = f"- **{today} {exp_id}**: {goal[:60]}. Conclusion: {conclusion}."

    log_content = upsert_experiment_row(log_content, exp_id, row)
    log_content = upsert_evidence_summary(log_content, exp_id, summary_line)
    if suggestion:
        decision_row = (
            f"| {today} | Recommend {sanitize_table_cell(suggestion)} | AI | Pending approval | "
            f"{sanitize_table_cell(f'{exp_id} result recorded, pending human approval')} |"
        )
        log_content = upsert_decision_log_row(
            log_content,
            decision_row,
            row_pattern=re.compile(rf"^\|.*{re.escape(exp_id)}.*$", re.MULTILINE),
        )
        checks.append(check_item("Decision Log recorded pending-approval recommendation", True, suggestion))
    else:
        checks.append(check_item("Decision Log recorded pending-approval recommendation", True, "No state-change recommendation this time"))
    log_path.write_text(log_content, encoding="utf-8")
    checks.append(check_item("TRACK_LOG.md synced experiment result", True, str(log_path)))

    if track.get("type") == "research":
        track["evidence_summary"] = f"{exp_id}: {conclusion}"
        checks.append(check_item("Research track evidence_summary updated", True, track["evidence_summary"]))
    else:
        checks.append(check_item("Infrastructure track does not need evidence_summary update", True, track.get("type", "unknown")))

    registry["updated"] = today
    registry_path = save_registry(project_dir, registry)
    checks.append(check_item("track_registry.yaml updated", True, str(registry_path)))

    return {
        "passed": True,
        "summary": f"Experiment result recorded: {track_id} / {exp_id}",
        "checks": checks,
        "data": {
            "track_id": track_id,
            "exp_id": exp_id,
            "current_phase": current_phase,
            "recorded": True,
            "track_log_path": str(log_path),
            "registry_path": str(registry_path),
            "conclusion": conclusion,
            "state_suggestion": suggestion,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync experiment results into TRACK_LOG.md and track_registry.yaml")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    parser.add_argument("--track-id", required=True, help="Track ID")
    parser.add_argument("--exp-id", required=True, help="Experiment ID, e.g. EXP_001")
    args = parser.parse_args()

    run_action(lambda: record_result(Path(args.project_dir), args.track_id, args.exp_id), RecordResultError)


if __name__ == "__main__":
    main()
