#!/usr/bin/env python3
"""
graduate_track.py — 记录单条 GRADUATED 轨道的 PDAE 毕业信息

退出码:
  0  记录成功
  1  前置条件不满足
  2  文件缺失或格式错误

用法:
  python3 tools/graduate_track.py --project-dir <path> --track-id <id> --pdae-project-path <path>
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _artifacts import render_research_track_log
from _cli import run_action
from _registry import (
    get_current_phase,
    load_registry as _shared_load_registry,
    require_track,
    save_registry,
)
from _output import check_item
from generate_conclusion import ConclusionError, get_cycle_label, write_conclusion


class GraduateTrackError(RuntimeError):
    """Raised when graduation bookkeeping cannot proceed."""


def load_registry(project_dir: Path) -> dict:
    return _shared_load_registry(project_dir, error_cls=GraduateTrackError)


def ensure_phase3_track_log(project_dir: Path, track: dict) -> Path:
    phase3_log = project_dir / "prae" / "phases" / "phase_03_conclusion" / "tracks" / track["id"] / "TRACK_LOG.md"
    phase3_log.parent.mkdir(parents=True, exist_ok=True)
    (phase3_log.parent / "experiments").mkdir(parents=True, exist_ok=True)
    if phase3_log.exists():
        return phase3_log

    phase2_log = project_dir / "prae" / "phases" / "phase_02_validation" / "tracks" / track["id"] / "TRACK_LOG.md"
    if phase2_log.exists():
        shutil.copy2(phase2_log, phase3_log)
        return phase3_log

    registry = load_registry(project_dir)
    cycle_label = get_cycle_label(registry)
    phase3_log.write_text(
        render_research_track_log(
            track,
            "phase_03_conclusion",
            cycle_label=cycle_label,
            created_reason="结论阶段补建轨道日志",
        ),
        encoding="utf-8",
    )
    return phase3_log


def upsert_pdae_record(log_path: Path, pdae_project_path: str, transfer_status: str) -> None:
    today = str(datetime.date.today())
    section = "\n".join([
        "## PDAE 毕业记录",
        "",
        f"**毕业日期**: {today}",
        f"**PDAE 项目路径**: {pdae_project_path}",
        f"**移交状态**: {transfer_status}",
    ])

    content = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    if "## PDAE 毕业记录" in content:
        updated = re.sub(
            r"\n## PDAE 毕业记录\n.*?(?=\n## |\Z)",
            "\n" + section + "\n",
            content,
            flags=re.DOTALL,
        )
        log_path.write_text(updated, encoding="utf-8")
        return

    if content and not content.endswith("\n"):
        content += "\n"
    content += "\n---\n\n" + section + "\n"
    log_path.write_text(content, encoding="utf-8")


def graduate_track(project_dir: Path, track_id: str, pdae_project_path: str, transfer_status: str) -> dict:
    registry = load_registry(project_dir)
    current_phase = get_current_phase(registry, default="")
    if current_phase != "phase_03_conclusion":
        raise GraduateTrackError(f"当前阶段为 {current_phase}，必须是 phase_03_conclusion")

    pdae_path = Path(pdae_project_path)
    if not pdae_path.exists():
        raise GraduateTrackError(f"PDAE 项目路径不存在: {pdae_path}")

    track = require_track(registry, track_id, error_cls=GraduateTrackError, expected_type="research")
    if track.get("state") != "GRADUATED":
        raise GraduateTrackError(f"轨道 {track_id} 当前 state={track.get('state')}，必须为 GRADUATED")

    log_path = ensure_phase3_track_log(project_dir, track)
    upsert_pdae_record(log_path, str(pdae_path), transfer_status)

    if not track.get("concluded_at"):
        track["concluded_at"] = str(datetime.date.today())
    track["pdae_project"] = str(pdae_path)
    registry["updated"] = str(datetime.date.today())
    registry_path = save_registry(project_dir, registry)

    conclusion_payload = None
    try:
        conclusion_payload = write_conclusion(project_dir)
    except ConclusionError:
        conclusion_payload = None

    checks = [
        check_item("轨道为 GRADUATED 且位于 phase_03_conclusion", True, track_id),
        check_item("PDAE 项目路径存在", True, str(pdae_path)),
        check_item("TRACK_LOG.md 已记录 PDAE 毕业信息", True, str(log_path)),
        check_item("track_registry.yaml 已登记 pdae_project", True, str(registry_path)),
    ]
    if conclusion_payload is not None:
        checks.append(check_item("CONCLUSION.md 已刷新", True, conclusion_payload["data"]["path"]))

    return {
        "passed": True,
        "summary": f"轨道 {track_id} 已登记到 PDAE",
        "checks": checks,
        "data": {
            "track_id": track_id,
            "pdae_project_path": str(pdae_path),
            "track_log_path": str(log_path),
            "registry_path": str(registry_path),
            "conclusion_path": conclusion_payload["data"]["path"] if conclusion_payload else "",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Record PDAE graduation info for a GRADUATED track")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    parser.add_argument("--track-id", required=True, help="Research track ID")
    parser.add_argument("--pdae-project-path", required=True, help="PDAE project path")
    parser.add_argument("--transfer-status", default="M1-M3 complete", help="Handoff status note")
    args = parser.parse_args()

    run_action(
        lambda: graduate_track(
            Path(args.project_dir),
            args.track_id,
            args.pdae_project_path,
            args.transfer_status,
        ),
        GraduateTrackError,
    )


if __name__ == "__main__":
    main()
