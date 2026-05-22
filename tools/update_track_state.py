#!/usr/bin/env python3
"""
update_track_state.py — 研究轨道状态变更的正式工具

退出码:
  0  状态更新成功
  1  状态迁移条件未满足
  2  文件缺失、格式错误或参数错误

用法:
  python3 tools/update_track_state.py \
    --project-dir <path> \
    --track-id <research_track_id> \
    --to-state <ACTIVE|KILLED|MERGED|GRADUATED> \
    --approver <name> \
    --reason <reason> \
    [--advisor AI] \
    [--approved-at YYYY-MM-DD] \
    [--exp-id EXP_001] \
    [--merged-into <target_track_id>] \
    [--summary <one-line-summary>]
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _artifacts import render_depends_lines, upsert_decision_log_row
from _cli import run_action
from _registry import (
    describe_phase_context,
    get_current_phase,
    load_registry as _shared_load_registry,
    require_track,
    save_registry,
)
from _output import check_item
from check_research_gate import (
    ResearchGateError,
    evaluate_research_gate,
)


ALLOWED_TRANSITIONS = {
    "EXPLORING": {"ACTIVE"},
    "ACTIVE": {"KILLED", "MERGED", "GRADUATED"},
}
TERMINAL_STATES = {"KILLED", "MERGED", "GRADUATED"}
EXECUTABLE_PHASES = {"phase_01_research", "phase_02_validation"}


class TrackStateError(RuntimeError):
    """状态变更输入错误。"""


def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=TrackStateError)


def parse_approved_at(value: str | None) -> str:
    if not value:
        return str(datetime.date.today())
    try:
        return str(datetime.date.fromisoformat(value))
    except ValueError as exc:
        raise TrackStateError(f"approved_at 格式错误: {value}（期望 YYYY-MM-DD）") from exc


def sanitize_table_cell(value: str) -> str:
    return " ".join(value.replace("|", "/").split())


def track_log_path(project_dir: Path, current_phase: str, track_id: str) -> Path:
    return project_dir / "prae" / "phases" / current_phase / "tracks" / track_id / "TRACK_LOG.md"


def exp_md_path(project_dir: Path, current_phase: str, track_id: str, exp_id: str) -> Path:
    return (
        project_dir
        / "prae"
        / "phases"
        / current_phase
        / "tracks"
        / track_id
        / "experiments"
        / f"{exp_id}.md"
    )


def ensure_state_section(content: str, track: dict, new_state: str) -> str:
    state_line = f"**当前状态**: {new_state}"
    if re.search(r"\*\*当前状态\*\*: .+", content):
        return re.sub(r"\*\*当前状态\*\*: .+", state_line, content, count=1)

    depends_lines = render_depends_lines(track.get("depends_on"))
    state_block = "\n".join([
        "## State",
        "",
        state_line,
        "**依赖的轨道**:",
        depends_lines,
        "",
        "---",
        "",
    ])

    if "## State" in content:
        return re.sub(r"## State\n+", state_block, content, count=1)
    if "## Experiments" in content:
        return content.replace("## Experiments", state_block + "## Experiments", 1)
    return content.rstrip() + "\n\n---\n\n" + state_block


def update_track_log(project_dir: Path, current_phase: str, track: dict, new_state: str, row: str) -> Path:
    log_path = track_log_path(project_dir, current_phase, track["id"])
    if not log_path.exists():
        raise TrackStateError(f"未找到 TRACK_LOG.md: {log_path}")

    content = log_path.read_text(encoding="utf-8")
    content = ensure_state_section(content, track, new_state)
    content = upsert_decision_log_row(content, row)
    log_path.write_text(content, encoding="utf-8")
    return log_path


def validate_dependencies_locked(registry: dict, track: dict) -> dict:
    depends_on = track.get("depends_on") or []
    if not depends_on:
        return check_item("依赖的基础设施轨道已 LOCKED", True, "无 depends_on 依赖")

    infra_by_id = {item["id"]: item for item in registry.get("tracks", [])}
    failures: list[str] = []
    for dep_id in depends_on:
        dep = infra_by_id.get(dep_id)
        if dep is None:
            failures.append(f"{dep_id}: 未在 track_registry.yaml 中声明")
            continue
        if dep.get("type") != "infrastructure":
            failures.append(f"{dep_id}: type={dep.get('type')}（应为 infrastructure）")
            continue
        if dep.get("state") != "LOCKED":
            failures.append(f"{dep_id}: state={dep.get('state')}（应为 LOCKED）")

    return check_item(
        "依赖的基础设施轨道已 LOCKED",
        not failures,
        "; ".join(failures[:3]) + ("..." if len(failures) > 3 else ""),
    )


def validate_merged_target(registry: dict, track_id: str, merged_into: str | None) -> dict:
    if not merged_into:
        return check_item("MERGED 时提供 merged_into", False, "缺少 --merged-into <target_track_id>")

    if merged_into == track_id:
        return check_item("MERGED 目标轨道合法", False, "merged_into 不能指向自己")

    target = next((t for t in registry.get("tracks", []) if t.get("id") == merged_into), None)
    if target is None:
        return check_item("MERGED 目标轨道合法", False, f"{merged_into} 不存在")
    if target.get("type") != "research":
        return check_item("MERGED 目标轨道合法", False, f"{merged_into} type={target.get('type')}")
    return check_item("MERGED 目标轨道合法", True, merged_into)


def validate_exp_reference(project_dir: Path, current_phase: str, track_id: str, exp_id: str | None) -> dict:
    if not exp_id:
        return check_item("EXP 引用检查（未提供 exp_id，跳过）", True, "未提供 --exp-id")

    exp_path = exp_md_path(project_dir, current_phase, track_id, exp_id)
    return check_item("EXP 引用存在", exp_path.exists(), str(exp_path))


def evaluate_transition(
    project_dir: Path,
    track_id: str,
    to_state: str,
    approver: str,
    reason: str,
    advisor: str = "AI",
    approved_at: str | None = None,
    exp_id: str | None = None,
    merged_into: str | None = None,
    summary: str | None = None,
) -> dict:
    registry = load_registry(str(project_dir))
    track = require_track(
        registry,
        track_id,
        error_cls=TrackStateError,
        expected_type="research",
    )
    current_phase = get_current_phase(registry)
    approved_at = parse_approved_at(approved_at)
    today = str(datetime.date.today())

    old_state = track.get("state", "")
    checks: list[dict] = []
    checks.append(check_item(
        "当前阶段允许更新研究轨道状态",
        current_phase in EXECUTABLE_PHASES,
        describe_phase_context(registry),
    ))
    checks.append(check_item(
        "状态迁移合法",
        to_state in ALLOWED_TRANSITIONS.get(old_state, set()),
        f"{old_state} → {to_state}",
    ))
    checks.append(validate_exp_reference(project_dir, current_phase, track_id, exp_id))

    if to_state == "ACTIVE":
        checks.append(validate_dependencies_locked(registry, track))

    if to_state == "MERGED":
        checks.append(validate_merged_target(registry, track_id, merged_into))

    research_gate = evaluate_research_gate(str(project_dir), track_id)
    checks.extend(
        check_item(f"Research Gate / {item['name']}", item["passed"], item.get("detail", ""))
        for item in research_gate["checks"]
    )

    passed = all(item["passed"] for item in checks)
    if not passed:
        return {
            "passed": False,
            "summary": f"研究轨道状态更新失败: {track_id} 不能从 {old_state} 迁移到 {to_state}",
            "checks": checks,
            "data": {
                "track_id": track_id,
                "current_phase": current_phase,
                "old_state": old_state,
                "new_state": to_state,
                "updated": False,
            },
        }

    reason_text = sanitize_table_cell(reason)
    if exp_id:
        reason_text = sanitize_table_cell(f"{exp_id}: {reason_text}")
    row = (
        f"| {approved_at} | {old_state} → {to_state} | {sanitize_table_cell(advisor)} | "
        f"{sanitize_table_cell(approver)} | {reason_text} |"
    )

    track["state"] = to_state
    if summary:
        track["evidence_summary"] = summary
    if to_state in TERMINAL_STATES:
        track["concluded_at"] = approved_at
    else:
        track["concluded_at"] = None
    if to_state == "MERGED":
        track["merged_into"] = merged_into
    else:
        track["merged_into"] = None

    registry["updated"] = today
    registry_path = save_registry(project_dir, registry)
    log_path = update_track_log(project_dir, current_phase, track, to_state, row)

    checks.append(check_item("track_registry.yaml 已更新", True, str(registry_path)))
    checks.append(check_item("TRACK_LOG.md 已记录状态变更", True, str(log_path)))

    return {
        "passed": True,
        "summary": f"研究轨道状态已更新: {track_id} {old_state} → {to_state}",
        "checks": checks,
        "data": {
            "track_id": track_id,
            "current_phase": current_phase,
            "old_state": old_state,
            "new_state": to_state,
            "approved_at": approved_at,
            "updated": True,
            "registry_path": str(registry_path),
            "track_log_path": str(log_path),
            "merged_into": merged_into,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Update a research track's state and append the Decision Log")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    parser.add_argument("--track-id", required=True, help="Research track ID")
    parser.add_argument(
        "--to-state",
        required=True,
        choices=["ACTIVE", "KILLED", "MERGED", "GRADUATED"],
        help="Target state",
    )
    parser.add_argument("--approver", required=True, help="Human approver")
    parser.add_argument("--reason", required=True, help="Reason for the state change")
    parser.add_argument("--advisor", default="AI", help="Advisor (default: AI)")
    parser.add_argument("--approved-at", help="Approval date (YYYY-MM-DD; default: today)")
    parser.add_argument("--exp-id", help="Associated experiment ID, e.g. EXP_001")
    parser.add_argument("--merged-into", help="Target track ID when the state is MERGED")
    parser.add_argument("--summary", help="Optional: one-line summary written back to evidence_summary")
    args = parser.parse_args()

    run_action(
        lambda: evaluate_transition(
            project_dir=Path(args.project_dir),
            track_id=args.track_id,
            to_state=args.to_state,
            approver=args.approver,
            reason=args.reason,
            advisor=args.advisor,
            approved_at=args.approved_at,
            exp_id=args.exp_id,
            merged_into=args.merged_into,
            summary=args.summary,
        ),
        TrackStateError,
        ResearchGateError,
    )


if __name__ == "__main__":
    main()
