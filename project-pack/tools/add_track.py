#!/usr/bin/env python3
"""
add_track.py — 正式向 track_registry.yaml 注册新轨道

退出码:
  0  注册成功
  1  注册条件未满足
  2  文件缺失、格式错误或参数错误

用法:
  python3 tools/add_track.py \
    --project-dir <path> \
    --track-id <track_id> \
    --type <research|infrastructure> \
    [--hypothesis <text>] \
    [--depends-on infra_a infra_b ...] \
    [--description <text>] \
    [--src <path>]
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _output import check_item
from _registry import get_current_phase, load_registry as _shared_load_registry, save_registry


class AddTrackError(RuntimeError):
    """轨道注册输入错误。"""


def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=AddTrackError)


def validate_track_id(track_id: str, track_type: str) -> None:
    prefixes = {
        "research": "research_",
        "infrastructure": "infra_",
    }
    prefix = prefixes[track_type]
    if not track_id.startswith(prefix):
        raise AddTrackError(f"track_id={track_id} 与 type={track_type} 不匹配（应以 {prefix} 开头）")


def ensure_unique_track_id(registry: dict, track_id: str) -> None:
    if any(track.get("id") == track_id for track in registry.get("tracks", [])):
        raise AddTrackError(f"轨道 {track_id} 已存在于 track_registry.yaml 中")


def default_src(track_id: str, track_type: str) -> str:
    if track_type == "research":
        return f"src/tracks/{track_id}/"
    return f"src/{track_id}/"


def build_track_entry(args: argparse.Namespace) -> dict:
    src = args.src or default_src(args.track_id, args.type)

    if args.type == "research":
        if not args.hypothesis:
            raise AddTrackError("research 轨道必须提供 --hypothesis")
        return {
            "id": args.track_id,
            "type": "research",
            "state": "EXPLORING",
            "src": src,
            "hypothesis": args.hypothesis,
            "depends_on": args.depends_on or [],
            "experiments": 0,
            "evidence_summary": None,
            "concluded_at": None,
            "merged_into": None,
        }

    return {
        "id": args.track_id,
        "type": "infrastructure",
        "state": "EXPLORING",
        "src": src,
        "description": args.description or "待补充",
        "module_spec": None,
        "contracts": None,
        "locked_at": None,
    }


def add_track(project_dir: Path, args: argparse.Namespace) -> dict:
    registry = load_registry(str(project_dir))
    validate_track_id(args.track_id, args.type)
    ensure_unique_track_id(registry, args.track_id)

    entry = build_track_entry(args)
    registry.setdefault("tracks", []).append(entry)
    registry["updated"] = str(datetime.date.today())

    registry_path = save_registry(project_dir, registry)

    checks = [
        check_item("track_id 与类型匹配", True, f"{args.track_id} / {args.type}"),
        check_item("轨道 ID 尚未占用", True, args.track_id),
        check_item("track_registry.yaml 已追加新轨道", True, str(registry_path)),
    ]

    return {
        "passed": True,
        "summary": f"已注册新轨道: {args.track_id}",
        "checks": checks,
        "data": {
            "track_id": args.track_id,
            "type": args.type,
            "state": "EXPLORING",
            "src": entry["src"],
            "current_phase": get_current_phase(registry),
            "registered": True,
            "registry_path": str(registry_path),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="向 track_registry.yaml 正式注册新轨道")
    parser.add_argument("--project-dir", required=True, help="研究项目根目录")
    parser.add_argument("--track-id", required=True, help="轨道 ID")
    parser.add_argument("--type", required=True, choices=["research", "infrastructure"], help="轨道类型")
    parser.add_argument("--hypothesis", help="research 轨道的一句话假设")
    parser.add_argument("--depends-on", nargs="*", default=[], help="research 轨道依赖的基础设施轨道 ID 列表")
    parser.add_argument("--description", help="infrastructure 轨道的一句话描述")
    parser.add_argument("--src", help="可选：覆盖默认 src 路径")
    args = parser.parse_args()

    run_action(lambda: add_track(Path(args.project_dir), args), AddTrackError)


if __name__ == "__main__":
    main()
