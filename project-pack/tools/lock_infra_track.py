#!/usr/bin/env python3
"""
lock_infra_track.py — Formally advance an infrastructure track from EXPLORING to LOCKED

Exit codes:
  0  Lock succeeded
  1  Lock conditions not met
  2  Missing file, format error, or argument error

Usage:
  python3 tools/lock_infra_track.py \
    --project-dir <path> \
    --track-id <infra_track_id> \
    --approver <name> \
    --reason <reason> \
    [--contracts src/infra_xxx/contracts.yaml] \
    [--module-spec src/infra_xxx/MODULE_SPEC.md] \
    [--advisor AI] \
    [--locked-at YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _artifacts import upsert_decision_log_row
from _cli import run_action
from _gate_utils import summarize_violations
from _registry import (
    describe_phase_context,
    get_current_phase,
    load_registry as _shared_load_registry,
    require_track,
    save_registry,
)
from _output import check_item
from check_contracts import run_check
from update_track_state import (
    ensure_state_section,
    parse_approved_at,
    sanitize_table_cell,
    track_log_path,
)


class InfraLockError(RuntimeError):
    """Infrastructure lock input error."""

def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=InfraLockError)


def normalize_rel_path(path_str: str) -> str:
    return Path(path_str).as_posix()


def infer_artifact_path(track: dict, track_id: str, filename: str) -> str:
    src_dir = track.get("src") or f"src/{track_id}/"
    return normalize_rel_path(str(Path(src_dir) / filename))


def lock_infra_track(
    project_dir: Path,
    track_id: str,
    approver: str,
    reason: str,
    contracts: str | None = None,
    module_spec: str | None = None,
    advisor: str = "AI",
    locked_at: str | None = None,
) -> dict:
    registry = load_registry(str(project_dir))
    track = require_track(registry, track_id, error_cls=InfraLockError, expected_type="infrastructure")
    current_phase = get_current_phase(registry)
    locked_at = parse_approved_at(locked_at)
    old_state = track.get("state", "")
    checks: list[dict] = []

    checks.append(check_item(
        "Current phase permits locking an infrastructure track",
        current_phase == "phase_00_infra",
        describe_phase_context(registry),
    ))
    checks.append(check_item(
        "Infrastructure track state transition is valid",
        old_state == "EXPLORING",
        f"{old_state} → LOCKED",
    ))

    contracts_rel = normalize_rel_path(
        contracts
        or track.get("contracts")
        or infer_artifact_path(track, track_id, "contracts.yaml")
    )
    module_spec_rel = normalize_rel_path(
        module_spec
        or track.get("module_spec")
        or infer_artifact_path(track, track_id, "MODULE_SPEC.md")
    )
    contracts_path = project_dir / contracts_rel if contracts_rel else None
    module_spec_path = project_dir / module_spec_rel if module_spec_rel else None
    log_path = track_log_path(project_dir, current_phase, track_id)

    checks.append(check_item("contracts path determined", bool(contracts_rel), str(contracts_rel or "")))
    checks.append(check_item("MODULE_SPEC path determined", bool(module_spec_rel), str(module_spec_rel or "")))
    checks.append(check_item("contracts file exists", bool(contracts_path and contracts_path.exists()), str(contracts_path or "")))
    checks.append(check_item("MODULE_SPEC file exists", bool(module_spec_path and module_spec_path.exists()), str(module_spec_path or "")))
    checks.append(check_item("TRACK_LOG.md exists", log_path.exists(), str(log_path)))

    contracts_passed = False
    if contracts_path and contracts_path.exists():
        violations = run_check(contracts_path, [project_dir / "src"])
        contracts_passed = not (violations.has_immutable() or violations.has_critical())
        detail = (
            f"{contracts_rel} passed"
            if contracts_passed
            else summarize_violations(track_id, violations)
        )
        checks.append(check_item("Contracts Gate passed", contracts_passed, detail))
    else:
        checks.append(check_item("Contracts Gate passed", False, "contracts file does not exist, cannot check"))

    passed = all(item["passed"] for item in checks)
    if not passed:
        return {
            "passed": False,
            "summary": f"Infrastructure track lock failed: {track_id} cannot transition from {old_state} to LOCKED",
            "checks": checks,
            "data": {
                "track_id": track_id,
                "current_phase": current_phase,
                "old_state": old_state,
                "new_state": "LOCKED",
                "locked": False,
            },
        }

    track["state"] = "LOCKED"
    track["locked_at"] = locked_at
    track["contracts"] = contracts_rel
    track["module_spec"] = module_spec_rel
    registry["updated"] = str(datetime.date.today())
    registry_path = save_registry(project_dir, registry)

    log_content = log_path.read_text(encoding="utf-8")
    log_content = ensure_state_section(log_content, track, "LOCKED")
    row = (
        f"| {locked_at} | EXPLORING → LOCKED | {sanitize_table_cell(advisor)} | "
        f"{sanitize_table_cell(approver)} | {sanitize_table_cell(reason)} |"
    )
    log_content = upsert_decision_log_row(log_content, row)
    log_path.write_text(log_content, encoding="utf-8")

    checks.append(check_item("track_registry.yaml updated to LOCKED", True, str(registry_path)))
    checks.append(check_item("TRACK_LOG.md recorded the LOCKED decision", True, str(log_path)))

    return {
        "passed": True,
        "summary": f"Infrastructure track locked: {track_id}",
        "checks": checks,
        "data": {
            "track_id": track_id,
            "current_phase": current_phase,
            "old_state": old_state,
            "new_state": "LOCKED",
            "locked": True,
            "locked_at": locked_at,
            "contracts": contracts_rel,
            "module_spec": module_spec_rel,
            "registry_path": str(registry_path),
            "track_log_path": str(log_path),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Formally advance an infrastructure track to LOCKED")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    parser.add_argument("--track-id", required=True, help="Infrastructure track ID")
    parser.add_argument("--approver", required=True, help="Human approver")
    parser.add_argument("--reason", required=True, help="Lock reason, e.g. 'PDAE M3 passed'")
    parser.add_argument("--contracts", help="Relative path to contracts.yaml (default: from registry, else src/{track_id}/contracts.yaml)")
    parser.add_argument("--module-spec", help="Relative path to MODULE_SPEC.md (default: from registry, else src/{track_id}/MODULE_SPEC.md)")
    parser.add_argument("--advisor", default="AI", help="Advisor (default: AI)")
    parser.add_argument("--locked-at", "--approved-at", dest="locked_at",
                        help="Lock date (YYYY-MM-DD; default: today)")
    args = parser.parse_args()

    run_action(
        lambda: lock_infra_track(
            project_dir=Path(args.project_dir),
            track_id=args.track_id,
            approver=args.approver,
            reason=args.reason,
            contracts=args.contracts,
            module_spec=args.module_spec,
            advisor=args.advisor,
            locked_at=args.locked_at,
        ),
        InfraLockError,
    )


if __name__ == "__main__":
    main()
