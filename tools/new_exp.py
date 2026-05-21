#!/usr/bin/env python3
"""
new_exp.py — 为已物化轨道创建新的 EXP_NNN.md / EXP_NNN.py

退出码:
  0  创建成功
  1  前置条件不满足（阶段不匹配、轨道目录不存在等）
  2  文件缺失或格式错误

用法:
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
    """实验创建输入错误。"""


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
            "summary": f"实验创建失败: {track_id} 不在 track_registry.yaml 中，请先 add-track 或重新 init",
            "checks": [check_item("轨道已登记到 track_registry.yaml", False, track_id)],
            "data": {"track_id": track_id, "created": False},
        }

    checks.append(check_item("轨道已登记到 track_registry.yaml", True, track_id))
    checks.append(
        validate_phase_track_match(
            current_phase,
            track,
            action_label="创建实验",
            blocked_phase03_detail="phase_03_conclusion 不允许创建新实验，请先 finalize 或 reopen",
            detail=describe_phase_context(registry),
        )
    )

    track_dir = project_dir / "prae" / "phases" / current_phase / "tracks" / track_id
    exp_dir = track_dir / "experiments"
    track_dir_ok = track_dir.is_dir()
    checks.append(check_item("当前阶段轨道目录已创建", track_dir_ok, str(track_dir)))

    if not all(item["passed"] for item in checks):
        failure_reason = "；".join(item["name"] for item in checks if not item["passed"])
        return {
            "passed": False,
            "summary": f"实验创建失败: {failure_reason}",
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
        raise NewExperimentError(f"未找到模板文件: {template_path}")

    template = template_path.read_text(encoding="utf-8")
    exp_md_path.write_text(render_exp_markdown(template, exp_num, track_id, title), encoding="utf-8")
    exp_py_path.write_text(render_exp_python(exp_id, title, track_id, exp_md_path.relative_to(project_dir)), encoding="utf-8")
    checks.append(check_item("EXP_NNN.md 已创建", True, str(exp_md_path)))
    checks.append(check_item("EXP_NNN.py 已创建", True, str(exp_py_path)))

    track["experiments"] = track.get("experiments", 0) + 1
    registry["updated"] = str(datetime.date.today())
    registry_path = save_registry(project_dir, registry)
    checks.append(check_item("track_registry.yaml 已更新 experiments 计数", True, str(track["experiments"])))

    return {
        "passed": True,
        "summary": f"实验已创建: {track_id} / {exp_id}",
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
    parser = argparse.ArgumentParser(description="为已物化轨道创建新的 EXP_NNN.md / EXP_NNN.py")
    parser.add_argument("--project-dir", required=True, help="研究项目根目录")
    parser.add_argument("--track-id", required=True, help="轨道 ID")
    parser.add_argument("--title", default="实验", help="实验标题")
    args = parser.parse_args()

    run_action(
        lambda: run(Path(args.project_dir), args.track_id, args.title),
        NewExperimentError,
    )


if __name__ == "__main__":
    main()
