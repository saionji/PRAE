#!/usr/bin/env python3
"""
new_track.py — 为已登记轨道创建当前阶段目录和初始 TRACK_LOG.md

退出码:
  0  创建成功或已存在
  1  前置条件不满足（未登记轨道、阶段不匹配等）
  2  文件缺失或格式错误

用法:
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
    """轨道目录创建输入错误。"""


def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=NewTrackError)


def render_track_log(track: dict, registry: dict, current_phase: str) -> str:
    cycle_label = get_cycle_label(registry)

    if track["type"] == "research":
        return render_research_track_log(
            track,
            current_phase,
            cycle_label=cycle_label,
            created_reason="当前阶段初始化",
        )

    return render_infra_track_log(
        track,
        current_phase,
        cycle_label=cycle_label,
        created_reason="当前阶段初始化",
    )


def run(project_dir: Path, track_id: str) -> dict:
    registry = load_registry(str(project_dir))
    current_phase = get_current_phase(registry)
    track = find_track(registry, track_id)

    checks: list[dict] = []
    if track is None:
        return {
            "passed": False,
            "summary": f"轨道创建失败: {track_id} 不在 track_registry.yaml 中，请先 add-track 或重新 init",
            "checks": [check_item("轨道已登记到 track_registry.yaml", False, track_id)],
            "data": {"track_id": track_id, "created": False},
        }

    checks.append(check_item("轨道已登记到 track_registry.yaml", True, track_id))
    checks.append(
        validate_phase_track_match(
            current_phase,
            track,
            action_label="创建轨道目录",
            blocked_phase03_detail="phase_03_conclusion 不允许新建轨道目录，请先 finalize 或 reopen",
            detail=describe_phase_context(registry),
        )
    )
    if not all(item["passed"] for item in checks):
        failure_reason = "；".join(item["name"] for item in checks if not item["passed"])
        return {
            "passed": False,
            "summary": f"轨道创建失败: {failure_reason}",
            "checks": checks,
            "data": {"track_id": track_id, "created": False, "current_phase": current_phase},
        }

    track_dir = project_dir / "prae" / "phases" / current_phase / "tracks" / track_id
    experiments_dir = track_dir / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    checks.append(check_item("phase 目录已创建", True, str(track_dir)))

    src_root = project_dir / track.get("src", f"src/tracks/{track_id}/")
    src_root.mkdir(parents=True, exist_ok=True)
    checks.append(check_item("registry src 目录已存在", True, str(src_root)))

    if track.get("type") == "research":
        exp_src_dir = src_root / "experiments"
        impl_dir = src_root / "impl"
        exp_src_dir.mkdir(parents=True, exist_ok=True)
        impl_dir.mkdir(parents=True, exist_ok=True)
        checks.append(check_item("研究轨道 experiments 目录已存在", True, str(exp_src_dir)))
        checks.append(check_item("研究轨道 impl 目录已存在", True, str(impl_dir)))
    else:
        exp_src_dir = project_dir / "src" / "tracks" / track_id / "experiments"
        exp_src_dir.mkdir(parents=True, exist_ok=True)
        checks.append(check_item("基础设施轨道 experiments 目录已存在", True, str(exp_src_dir)))

    log_path = track_dir / "TRACK_LOG.md"
    if log_path.exists():
        checks.append(check_item("TRACK_LOG.md 已存在（保持不覆盖）", True, str(log_path)))
        summary = f"轨道已就绪: {track_id}（当前阶段目录已存在）"
        created = False
    else:
        log_path.write_text(render_track_log(track, registry, current_phase), encoding="utf-8")
        checks.append(check_item("TRACK_LOG.md 已初始化", True, str(log_path)))
        summary = f"轨道已创建: {track_id}"
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
