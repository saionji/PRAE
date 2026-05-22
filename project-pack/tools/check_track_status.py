#!/usr/bin/env python3
"""
check_track_status.py — Check the consistency of track_registry.yaml

Exit codes:
  0  All checks passed
  1  Inconsistency found
  2  Missing file or format error

Usage:
  python3 tools/check_track_status.py --project-dir <path>
"""
from __future__ import annotations
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _cli import emit_payload
from _output import check_item, error
from _registry import RegistryError, get_current_phase, get_phase_override, get_recorded_phase, load_registry


def evaluate(project_dir: str) -> dict:
    try:
        registry = load_registry(project_dir)
    except RegistryError as exc:
        error(str(exc))

    required_top = ["project", "current_phase", "tracks"]
    for field in required_top:
        if field not in registry:
            error(f"track_registry.yaml is missing required field: {field}")

    tracks = registry.get("tracks", [])
    checks: list[dict] = []

    valid_infra_states = {"EXPLORING", "LOCKED"}
    valid_research_states = {"EXPLORING", "ACTIVE", "KILLED", "MERGED", "GRADUATED"}
    valid_types = {"infrastructure", "research"}

    seen_ids: set[str] = set()

    for t in tracks:
        tid = t.get("id", "<unknown>")

        # Uniqueness
        dup = tid in seen_ids
        checks.append(check_item(f"{tid}: ID is unique", not dup, "duplicate ID" if dup else ""))
        seen_ids.add(tid)

        # Type
        ttype = t.get("type", "")
        valid_type = ttype in valid_types
        checks.append(check_item(f"{tid}: type is valid", valid_type,
                                  f"type={ttype}" if not valid_type else ""))

        # State
        state = t.get("state", "")
        if ttype == "infrastructure":
            valid_state = state in valid_infra_states
        else:
            valid_state = state in valid_research_states
        checks.append(check_item(f"{tid}: state is valid", valid_state,
                                  f"state={state}" if not valid_state else ""))

        # ID naming convention
        if ttype == "infrastructure":
            correct_prefix = tid.startswith("infra_")
        else:
            correct_prefix = tid.startswith("research_")
        checks.append(check_item(f"{tid}: ID prefix is correct", correct_prefix,
                                  "should start with infra_ or research_" if not correct_prefix else ""))

        # A LOCKED infrastructure track must have contracts and module_spec
        if ttype == "infrastructure" and state == "LOCKED":
            has_contracts = bool(t.get("contracts"))
            has_spec = bool(t.get("module_spec"))
            contracts_exists = has_contracts and os.path.exists(
                os.path.join(project_dir, t["contracts"]))
            spec_exists = has_spec and os.path.exists(
                os.path.join(project_dir, t["module_spec"]))

            checks.append(check_item(f"{tid}: contracts field exists", has_contracts))
            checks.append(check_item(f"{tid}: contracts file exists", contracts_exists,
                                      f"{t.get('contracts')}" if not contracts_exists else ""))
            checks.append(check_item(f"{tid}: module_spec field exists", has_spec))
            checks.append(check_item(f"{tid}: module_spec file exists", spec_exists,
                                      f"{t.get('module_spec')}" if not spec_exists else ""))

        # A MERGED track must have merged_into
        if state == "MERGED":
            has_merged_into = bool(t.get("merged_into"))
            checks.append(check_item(f"{tid}: has merged_into when MERGED", has_merged_into))

        # A terminal-state research track must have concluded_at
        if ttype == "research" and state in {"KILLED", "MERGED", "GRADUATED"}:
            has_concluded = bool(t.get("concluded_at"))
            checks.append(check_item(f"{tid}: has concluded_at in terminal state", has_concluded,
                                      "KILLED/MERGED/GRADUATED tracks must fill concluded_at"))

        # src directory exists (if the field is filled)
        src = t.get("src", "")
        if src:
            src_path = os.path.join(project_dir, src)
            src_exists = os.path.isdir(src_path)
            checks.append(check_item(f"{tid}: src directory exists", src_exists,
                                      src_path if not src_exists else ""))

    all_passed = all(c["passed"] for c in checks)
    failed = [c for c in checks if not c["passed"]]
    summary = (
        f"passed ({len(tracks)} tracks, {len(checks)} checks)"
        if all_passed
        else f"failed ({len(failed)} items did not pass)"
    )
    return {
        "passed": all_passed,
        "summary": summary,
        "checks": checks,
        "data": {
            "tracks": len(tracks),
            "current_phase": get_current_phase(registry),
            "recorded_phase": get_recorded_phase(registry),
            "current_phase_override": get_phase_override(registry),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check PRAE track_registry.yaml consistency")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    args = parser.parse_args()
    emit_payload(evaluate(args.project_dir))


if __name__ == "__main__":
    main()
