#!/usr/bin/env python3
"""
check_conclusion.py — validate the Phase 3 CONCLUSION.md

Exit codes:
  0  check passed
  1  check failed
  2  file missing or format error

Usage:
  python3 tools/check_conclusion.py --project-dir <path> [--check-approved]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _conclusion_docs import (
    CONCLUSION_SECTIONS,
    FINAL_DECISION_FIELDS,
    VALID_DECISIONS,
    extract_final_decision_body,
    parse_final_decision_fields,
)
from _gate_utils import gate_payload
from _registry import get_cycle_label, get_recorded_phase
from _output import check_item
from generate_conclusion import (
    ConclusionError,
    load_registry,
)


def _validate_structure(content: str, registry: dict) -> list[dict]:
    checks: list[dict] = []
    project_name = registry.get("project", "unknown-project")
    cycle_label = get_cycle_label(registry)

    checks.append(check_item("CONCLUSION title correct", f"# CONCLUSION — {project_name}" in content, project_name))
    cycle_ok = re.search(rf"\*\*Research Cycle\*\*:\s*{re.escape(cycle_label)}", content) is not None
    checks.append(check_item("CONCLUSION research cycle correct", cycle_ok, cycle_label))
    for section in CONCLUSION_SECTIONS:
        checks.append(check_item(f"CONCLUSION contains section: {section}", section in content, section))

    final_section = extract_final_decision_body(content)
    field_labels = {
        "APPROVED": "APPROVED",
        "DECISION": "DECISION",
        "APPROVER": "APPROVER",
        "APPROVED_AT": "APPROVED_AT",
        "COMMENT": "COMMENT",
    }
    for field in FINAL_DECISION_FIELDS:
        present = re.search(rf"^{field}:[ \t]*.*$", final_section, re.MULTILINE) is not None
        checks.append(check_item(f"CONCLUSION contains {field_labels[field]} field", present))

    outcomes_section = re.search(r"## Disposition of Each Track\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    outcomes_text = outcomes_section.group(1) if outcomes_section else ""
    for track in registry.get("tracks", []):
        checks.append(check_item(
            f"Disposition of Each Track contains {track['id']}",
            f"`{track['id']}`" in outcomes_text,
            track["id"],
        ))

    graduated_section = re.search(r"## PDAE Project Links for Graduated Tracks\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    graduated_text = graduated_section.group(1) if graduated_section else ""
    for track in registry.get("tracks", []):
        if track.get("type") == "research" and track.get("state") == "GRADUATED":
            checks.append(check_item(
                f"PDAE project links contain {track['id']}",
                f"`{track['id']}`" in graduated_text,
                track["id"],
            ))

    return checks


def evaluate_conclusion(project_dir: str) -> dict:
    registry = load_registry(Path(project_dir))
    current_phase = get_recorded_phase(registry, "")
    if current_phase != "phase_03_conclusion":
        raise ConclusionError(f"Current phase is {current_phase}; only the CONCLUSION.md of phase_03_conclusion can be checked")

    conclusion_path = Path(project_dir) / "prae" / "phases" / "phase_03_conclusion" / "CONCLUSION.md"
    if not conclusion_path.exists():
        raise ConclusionError(f"CONCLUSION.md does not exist: {conclusion_path}")

    content = conclusion_path.read_text(encoding="utf-8")
    checks = _validate_structure(content, registry)

    final_section = extract_final_decision_body(content)
    final_fields = parse_final_decision_fields(final_section)
    approved = final_fields["APPROVED"] or "not found"
    decision = final_fields["DECISION"]
    approver = final_fields["APPROVER"]
    approved_at = final_fields["APPROVED_AT"]
    comment = final_fields["COMMENT"]

    checks.append(check_item("APPROVED field valid", approved in {"yes", "no", "pending"}, f"current value={approved}"))
    checks.append(check_item(
        "DECISION field valid or empty",
        decision in VALID_DECISIONS or decision == "",
        decision or "empty",
    ))
    checks.append(check_item(
        "APPROVED_AT format correct or empty",
        approved_at == "" or re.fullmatch(r"\d{4}-\d{2}-\d{2}", approved_at) is not None,
        approved_at or "empty",
    ))
    if approved == "yes":
        checks.append(check_item("Final decision valid", decision in VALID_DECISIONS, decision or "no decision found"))
        checks.append(check_item("Approver filled in", bool(approver), approver or "approver is empty"))
        checks.append(check_item(
            "Date format correct",
            re.fullmatch(r"\d{4}-\d{2}-\d{2}", approved_at) is not None,
            approved_at or "date is empty",
        ))

        graduated_tracks = [
            t for t in registry.get("tracks", [])
            if t.get("type") == "research" and t.get("state") == "GRADUATED"
        ]
        graduated_with_pdae = [t for t in graduated_tracks if t.get("pdae_project")]

        if decision == "GRADUATED_TO_PDAE":
            checks.append(check_item("At least 1 GRADUATED track exists", len(graduated_tracks) >= 1))
            checks.append(check_item("At least 1 GRADUATED track has a registered PDAE project", len(graduated_with_pdae) >= 1))
        elif decision == "ARCHIVED":
            checks.append(check_item(
                "No PDAE project registered when ARCHIVED",
                len(graduated_with_pdae) == 0,
                ",".join(t["id"] for t in graduated_with_pdae) if graduated_with_pdae else "",
            ))

    return gate_payload(
        "CONCLUSION check",
        checks,
        data={
            "path": str(conclusion_path),
            "approved": approved,
            "decision": decision,
            "approver": approver,
            "approved_at": approved_at,
            "comment": comment,
        },
    )


def check_conclusion(project_dir: str, check_approved: bool) -> dict:
    evaluation = evaluate_conclusion(project_dir)
    checks = list(evaluation["checks"])
    passed = evaluation["passed"]
    if check_approved:
        approved_yes = evaluation["data"]["approved"] == "yes"
        checks.append(check_item("APPROVED: yes", approved_yes, f"current value={evaluation['data']['approved']}"))
        passed = passed and approved_yes

    return {
        "passed": passed,
        "summary": evaluation["summary"],
        "checks": checks,
        "data": evaluation["data"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the Phase 3 CONCLUSION.md")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    parser.add_argument("--check-approved", action="store_true", help="Require CONCLUSION.md to be APPROVED: yes")
    args = parser.parse_args()
    run_action(
        lambda: check_conclusion(args.project_dir, args.check_approved),
        ConclusionError,
    )


if __name__ == "__main__":
    main()
