#!/usr/bin/env python3
"""
init_project.py — 初始化新 PRAE 研究项目的目录结构和 track_registry.yaml

退出码:
  0  初始化成功
  1  初始化失败（文件已存在冲突等）
  2  参数或文件缺失错误

用法:
  python3 tools/init_project.py --name <project_name> --output-dir <path>
"""
from __future__ import annotations
import argparse
import datetime
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from _artifacts import render_infra_track_log as _render_infra_track_log
from _registry import get_cycle_label
from _phase_docs import render_phase0_brief
from _output import check_item, error, result


def should_render(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        return "{{" in path.read_text(encoding="utf-8")
    except OSError:
        return True


def parse_prae_init(prae_init_path: str) -> dict:
    """从 PRAE_INIT.md 解析基础设施轨道和研究轨道列表。"""
    with open(prae_init_path, encoding="utf-8") as f:
        content = f.read()

    infra_tracks: list[dict] = []
    research_tracks: list[dict] = []
    phase0_criteria: dict[str, str] = {}

    phase0_section = re.search(
        r"## Phase 0 成功标准\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if phase0_section:
        for line in phase0_section.group(1).splitlines():
            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) < 2:
                continue
            track_id = parts[0].strip("`")
            if not track_id.startswith("infra_"):
                continue
            phase0_criteria[track_id] = parts[1]

    # 解析基础设施轨道表格
    infra_section = re.search(
        r"## 组件分类 → 基础设施轨道\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if infra_section:
        for line in infra_section.group(1).splitlines():
            m = re.match(r"\|\s*`?(infra_\S+?)`?\s*\|(.+?)\|", line)
            if m:
                infra_tracks.append({
                    "id": m.group(1).strip(),
                    "description": m.group(2).strip(),
                    "lock_criteria": phase0_criteria.get(m.group(1).strip(), "(no description yet)"),
                })

    # 解析研究轨道表格
    research_section = re.search(
        r"## 组件分类 → 研究轨道\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if research_section:
        for line in research_section.group(1).splitlines():
            m = re.match(r"\|\s*`?(research_\S+?)`?\s*\|(.+?)\|(.+?)\|", line)
            if m:
                depends_raw = m.group(3).strip().strip("`").replace(" ", "")
                # F-008 fix: split on Western OR Chinese comma OR 顿号 so authors writing
                # `infra_X`、`infra_Y` (idiomatic Chinese) get parsed the same as `infra_X, infra_Y`.
                depends_list = [d.strip() for d in re.split(r"[,，、]", depends_raw) if d.strip() and d.strip() != "—"]
                research_tracks.append({
                    "id": m.group(1).strip(),
                    "hypothesis": m.group(2).strip(),
                    "depends_on": depends_list,
                })

    return {"infra": infra_tracks, "research": research_tracks}


def build_registry(project_name: str, tracks_data: dict) -> dict:
    """构建 track_registry.yaml 的内容。"""
    today = str(datetime.date.today())
    tracks = []

    for t in tracks_data["infra"]:
        tracks.append({
            "id": t["id"],
            "type": "infrastructure",
            "state": "EXPLORING",
            "src": f"src/{t['id']}/",
            "module_spec": None,
            "contracts": None,
            "locked_at": None,
        })

    for t in tracks_data["research"]:
        tracks.append({
            "id": t["id"],
            "type": "research",
            "state": "EXPLORING",
            "src": f"src/tracks/{t['id']}/",
            "hypothesis": t["hypothesis"],
            "depends_on": t["depends_on"] or [],
            "experiments": 0,
            "evidence_summary": None,
            "concluded_at": None,
            "merged_into": None,
        })

    return {
        "project": project_name,
        "current_cycle": 1,
        "current_phase": "phase_00_infra",
        "updated": today,
        "tracks": tracks,
    }


def render_infra_track_log(track: dict, registry: dict) -> str:
    cycle_label = get_cycle_label(registry)
    return _render_infra_track_log(
        track,
        "phase_00_infra",
        cycle_label=cycle_label,
        created_reason="项目启动",
        description=track.get("description") or "(no description yet)",
        lock_criteria=track.get("lock_criteria") or "(no description yet)",
    )


def init_project(project_name: str, output_dir: str) -> None:
    output_path = Path(output_dir)
    prae_dir = output_path / "prae"
    prae_init = prae_dir / "PRAE_INIT.md"
    templates_src = output_path / "prae" / "templates"

    checks: list[dict] = []

    # 1. 检查模板目录（依赖 prae bootstrap 先部署）
    has_templates = templates_src.is_dir()
    checks.append(check_item("prae/templates/ 存在", has_templates,
                              "请先运行 prae bootstrap 部署模板（或 python3 tools/prae_bootstrap.py）"))
    if not has_templates:
        result(False, checks, "初始化失败：prae/templates/ 不存在，请先运行 prae bootstrap")
        return

    # 2. 检查 PRAE_INIT.md
    has_init = prae_init.exists()
    checks.append(check_item("prae/PRAE_INIT.md 存在", has_init, str(prae_init)))
    if not has_init:
        result(False, checks, "初始化失败：PRAE_INIT.md 不存在，请填写后再运行")
        return

    # 2. 解析轨道列表
    try:
        tracks_data = parse_prae_init(str(prae_init))
    except Exception as e:
        error(f"解析 PRAE_INIT.md 失败: {e}")

    has_infra = len(tracks_data["infra"]) >= 1
    checks.append(check_item("PRAE_INIT.md 有基础设施轨道", has_infra,
                               "未解析到 infra_ 开头的轨道，请检查表格格式"))

    # 3. 初始化 track_registry.yaml
    registry_path = prae_dir / "track_registry.yaml"
    registry = build_registry(project_name, tracks_data)
    prae_dir.mkdir(parents=True, exist_ok=True)
    with open(registry_path, "w", encoding="utf-8") as f:
        yaml.dump(registry, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    checks.append(check_item("track_registry.yaml 已创建", True))

    # 4. 创建 Phase 0 目录
    phase0_dir = prae_dir / "phases" / "phase_00_infra"
    phase0_dir.mkdir(parents=True, exist_ok=True)
    checks.append(check_item("prae/phases/phase_00_infra/ 已创建", True))

    # 5. 渲染 PHASE_BRIEF.md
    phase_brief_dst = phase0_dir / "PHASE_BRIEF.md"
    if should_render(phase_brief_dst):
        phase_brief_dst.write_text(render_phase0_brief(registry, tracks_data["infra"]), encoding="utf-8")
    checks.append(check_item("PHASE_BRIEF.md 已创建", phase_brief_dst.exists()))

    # 6. 为每条基础设施轨道创建目录和 TRACK_LOG.md
    for t in tracks_data["infra"]:
        tid = t["id"]
        track_dir = phase0_dir / "tracks" / tid
        exp_dir = track_dir / "experiments"
        exp_dir.mkdir(parents=True, exist_ok=True)
        src_dir = output_path / "src" / tid
        src_dir.mkdir(parents=True, exist_ok=True)

        log_dst = track_dir / "TRACK_LOG.md"
        if should_render(log_dst):
            log_dst.write_text(render_infra_track_log(t, registry), encoding="utf-8")
        checks.append(check_item(f"{tid}: 目录和 TRACK_LOG.md 已创建", log_dst.exists()))

    # 7. 创建 src/shared/ 和 src/tracks/
    (output_path / "src" / "shared").mkdir(parents=True, exist_ok=True)
    (output_path / "src" / "tracks").mkdir(parents=True, exist_ok=True)
    checks.append(check_item("src/shared/ 和 src/tracks/ 已创建", True))

    # 8. 为每条研究轨道创建 src/ 子目录
    for t in tracks_data["research"]:
        tid = t["id"]
        src_track = output_path / "src" / "tracks" / tid
        (src_track / "experiments").mkdir(parents=True, exist_ok=True)
        (src_track / "impl").mkdir(parents=True, exist_ok=True)
    if tracks_data["research"]:
        checks.append(check_item("src/tracks/{research_tracks}/ 已创建", True))

    all_passed = all(c["passed"] for c in checks)
    result(all_passed, checks,
           f"初始化{'成功' if all_passed else '部分失败'}：{project_name}",
           data={
               "project": project_name,
               "infra_tracks": len(tracks_data["infra"]),
               "research_tracks": len(tracks_data["research"]),
               "current_phase": "phase_00_infra",
           })


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a PRAE research project structure")
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument("--output-dir", required=True, help="Target directory (typically the research project root)")
    args = parser.parse_args()
    init_project(args.name, args.output_dir)


if __name__ == "__main__":
    main()
