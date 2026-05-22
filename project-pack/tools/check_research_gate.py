#!/usr/bin/env python3
"""
check_research_gate.py — 验证研究轨道的五条 Research Gate 规则

退出码:
  0  所有规则通过
  1  违反规则 1-5 中任一项
  2  轨道不存在或文件缺失

用法:
  python3 tools/check_research_gate.py --track-id <id> --project-dir <path>
"""
from __future__ import annotations
import argparse
import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _gate_utils import gate_payload, summarize_violations
from _registry import (
    get_cycle_label,
    get_current_phase,
    load_registry as _shared_load_registry,
    require_track,
)
from check_contracts import run_check
from _output import check_item

SMOKE_TIMEOUT_SECONDS = 30
EXP_REQUIRED_SECTIONS = [
    "## Goal",
    "## Method",
    "## Preflight Check",
    "## Expected Signal",
    "## Result",
    "## Conclusion",
]
PREFLIGHT_REQUIRED_MARKERS = [
    "最小冒烟检查",
    "输出契约",
]


class ResearchGateError(RuntimeError):
    """Research Gate 配置或输入错误。"""


def find_current_phase(project_dir: str, registry: dict) -> str:
    return get_current_phase(registry)


def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=ResearchGateError)

def build_context(project_dir: str, track_id: str, current_phase: str) -> dict:
    exp_md_dir = Path(project_dir) / "prae" / "phases" / current_phase / "tracks" / track_id / "experiments"
    md_files = sorted(
        f.name for f in exp_md_dir.iterdir()
        if exp_md_dir.is_dir() and f.is_file() and f.name.startswith("EXP_") and f.suffix == ".md"
    ) if exp_md_dir.is_dir() else []

    latest_md_name = md_files[-1] if md_files else None
    latest_exp_id = Path(latest_md_name).stem if latest_md_name else ""
    latest_md_path = exp_md_dir / latest_md_name if latest_md_name else None
    latest_py_path = Path(project_dir) / "src" / "tracks" / track_id / "experiments" / f"{latest_exp_id}.py" if latest_exp_id else None

    return {
        "project_dir": project_dir,
        "track_id": track_id,
        "current_phase": current_phase,
        "exp_md_dir": exp_md_dir,
        "md_files": md_files,
        "latest_exp_id": latest_exp_id,
        "latest_md_path": latest_md_path,
        "latest_py_path": latest_py_path,
    }


def _preview_output(stdout: str, stderr: str, limit: int = 120) -> str:
    chunks = [part.strip() for part in (stdout, stderr) if part.strip()]
    if not chunks:
        return ""
    text = " | ".join(" ".join(chunk.split()) for chunk in chunks)
    return text if len(text) <= limit else text[: limit - 3] + "..."

def rule1_track_log(project_dir: str, track_id: str, current_phase: str, context: dict, cycle_label: str) -> dict:
    """规则 1：TRACK_LOG.md 有本次实验记录（至少一条完整条目）。"""
    log_path = os.path.join(project_dir, "prae", "phases", current_phase,
                             "tracks", track_id, "TRACK_LOG.md")
    if not os.path.exists(log_path):
        return check_item("规则1: TRACK_LOG.md 存在", False, log_path)

    with open(log_path, encoding="utf-8") as f:
        content = f.read()

    expected_cycle_line = f"**研究轮次**: {cycle_label}"
    if expected_cycle_line not in content:
        return check_item(
            "规则1: TRACK_LOG.md 研究轮次匹配",
            False,
            f"缺少或错误，期望 {expected_cycle_line}",
        )

    # 检查 Experiments 表格有数据行（不只是表头）
    exp_section = re.search(r"## Experiments\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    has_data_row = False
    if exp_section:
        lines = exp_section.group(1).strip().splitlines()
        # 数据行：含 | EXP_ 的行
        data_rows = [l for l in lines if "EXP_" in l and l.strip().startswith("|")]
        has_data_row = len(data_rows) >= 1

    if not has_data_row:
        return check_item("规则1: TRACK_LOG.md 有完整实验条目", False,
                          "Experiments 表格中没有数据行（或未找到含 EXP_ 的行）")

    latest_exp_id = context.get("latest_exp_id", "")
    if latest_exp_id and latest_exp_id not in content:
        return check_item("规则1: TRACK_LOG.md 记录最新实验", False,
                          f"未在 TRACK_LOG.md 中找到最新实验 {latest_exp_id}")

    detail = (
        f"研究轮次={cycle_label}; 最新实验={latest_exp_id}"
        if latest_exp_id else f"研究轮次={cycle_label}; 尚未发现 EXP_NNN.md，已验证 TRACK_LOG 行"
    )
    return check_item("规则1: TRACK_LOG.md 有完整实验条目", True, detail)


def rule2_smoke_test(project_dir: str, track_id: str, context: dict) -> dict:
    """规则 2：experiments/ 下至少一个 EXP_NNN.py 存在且最近脚本能跑通。"""
    exp_code_dir = os.path.join(project_dir, "src", "tracks", track_id, "experiments")
    if not os.path.isdir(exp_code_dir):
        return check_item("规则2: experiments/ 目录存在", False, exp_code_dir)

    py_files = [f for f in os.listdir(exp_code_dir) if f.startswith("EXP_") and f.endswith(".py")]
    has_exp_py = len(py_files) >= 1
    if not has_exp_py:
        return check_item("规则2: experiments/ 下有 EXP_NNN.py", False,
                          f"src/tracks/{track_id}/experiments/ 中没有 EXP_*.py 文件")

    latest_exp_id = context.get("latest_exp_id", "")
    if latest_exp_id:
        latest_py = f"{latest_exp_id}.py"
        script_path = os.path.join(exp_code_dir, latest_py)
        if not os.path.exists(script_path):
            return check_item("规则2: 最新实验有对应 EXP_NNN.py", False,
                              f"{latest_exp_id}.md 存在，但缺少对应脚本 {latest_py}")
    else:
        latest_py = sorted(py_files)[-1]
        script_path = os.path.join(exp_code_dir, latest_py)

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = project_dir if not existing_pythonpath else project_dir + os.pathsep + existing_pythonpath

    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=SMOKE_TIMEOUT_SECONDS,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return check_item("规则2: 最近实验脚本可运行", False,
                          f"{latest_py} 运行超时（>{SMOKE_TIMEOUT_SECONDS}s）")

    preview = _preview_output(proc.stdout, proc.stderr)
    detail = f"{latest_py} exit={proc.returncode}"
    if preview:
        detail += f"; output={preview}"
    return check_item("规则2: 最近实验脚本可运行", proc.returncode == 0, detail)


def rule3_params_recorded(project_dir: str, track_id: str, current_phase: str) -> dict:
    """规则 3：最新 EXP_NNN.md 结构完整，且先定义最小检查与复现参数。"""
    exp_md_dir = os.path.join(project_dir, "prae", "phases", current_phase,
                               "tracks", track_id, "experiments")
    if not os.path.isdir(exp_md_dir):
        return check_item("规则3: experiments/ 记录目录存在", False, exp_md_dir)

    md_files = sorted([f for f in os.listdir(exp_md_dir) if f.startswith("EXP_") and f.endswith(".md")])
    if not md_files:
        return check_item("规则3: 有 EXP_NNN.md 记录", False, "没有实验记录文件")

    latest_md = os.path.join(exp_md_dir, md_files[-1])
    with open(latest_md, encoding="utf-8") as f:
        content = f.read()

    missing_sections = [section for section in EXP_REQUIRED_SECTIONS if section not in content]
    if missing_sections:
        return check_item("规则3: EXP_NNN.md 结构完整", False,
                          f"缺少章节: {', '.join(missing_sections)}")

    method_section = re.search(r"## Method\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not method_section:
        return check_item("规则3: Method 节存在", False, f"{md_files[-1]}")

    method_text = method_section.group(1)
    # 检查关键词
    has_seed = re.search(r"seed|随机种子|无随机性", method_text, re.IGNORECASE) is not None
    has_time = re.search(r"\d{4}-\d{2}-\d{2}|时间窗|time", method_text, re.IGNORECASE) is not None
    has_data = re.search(r"数据源|data|infra_", method_text, re.IGNORECASE) is not None
    has_control = re.search(r"对照组|无对照组|baseline|control", method_text, re.IGNORECASE) is not None

    passed = has_seed and has_time and has_data and has_control
    missing = []
    if not has_seed:
        missing.append("随机种子")
    if not has_time:
        missing.append("时间范围")
    if not has_data:
        missing.append("数据源")
    if not has_control:
        missing.append("对照组")

    if not passed:
        return check_item(
            "规则3: Method 节有种子/时间范围/数据源/对照组",
            False,
            f"缺少: {', '.join(missing)}",
        )

    preflight_section = re.search(r"## Preflight Check\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not preflight_section:
        return check_item("规则3: Preflight Check 节存在", False, f"{md_files[-1]}")

    preflight_text = preflight_section.group(1)
    missing_markers = [
        marker for marker in PREFLIGHT_REQUIRED_MARKERS
        if marker not in preflight_text
    ]
    if missing_markers:
        return check_item(
            "规则3: Preflight Check 定义最小冒烟检查和输出契约",
            False,
            f"缺少: {', '.join(missing_markers)}",
        )

    return check_item(
        "规则3: Method/Preflight 已定义复现参数和最小检查",
        True,
        "Method 与 Preflight Check 结构完整",
    )


def rule4_contracts(project_dir: str, registry: dict) -> dict:
    """规则 4：对所有 LOCKED 基础设施实际运行 Contracts Gate。"""
    infra_tracks = [t for t in registry.get("tracks", []) if t.get("type") == "infrastructure"]
    if not infra_tracks:
        return check_item("规则4: 有基础设施契约可检查", False, "没有基础设施轨道，无法运行契约检查")

    locked = [t for t in infra_tracks if t.get("state") == "LOCKED" and t.get("contracts")]
    if not locked:
        return check_item("规则4: 契约检查（无 LOCKED 基础设施，跳过）", True,
                           "暂无 LOCKED 基础设施契约，无需检查（Phase 0 期间正常）")

    src_dir = Path(project_dir) / "src"
    if not src_dir.is_dir():
        return check_item("规则4: Contracts Gate 通过", False, f"src 目录不存在: {src_dir}")
    failures: list[str] = []
    warnings: list[str] = []

    for track in locked:
        track_id = track["id"]
        contracts_rel = track.get("contracts", "")
        contracts_path = Path(project_dir) / contracts_rel

        if not contracts_path.exists():
            failures.append(f"{track_id}: contracts 文件不存在 ({contracts_rel})")
            continue

        try:
            with open(contracts_path, encoding="utf-8") as f:
                contract_data = yaml.safe_load(f)
        except (OSError, yaml.YAMLError) as exc:
            failures.append(f"{track_id}: contracts 解析失败 ({exc})")
            continue
        if contract_data is not None and not isinstance(contract_data, dict):
            failures.append(f"{track_id}: contracts 顶层必须是 mapping")
            continue

        violations = run_check(contracts_path, [src_dir])
        if violations.has_immutable() or violations.has_critical():
            failures.append(summarize_violations(track_id, violations))
        elif violations.has_need_review():
            warnings.append(summarize_violations(track_id, violations))

    if failures:
        detail = "; ".join(failures[:3]) + ("..." if len(failures) > 3 else "")
        return check_item("规则4: Contracts Gate 通过", False, detail)

    detail = f"已检查 {len(locked)} 条 LOCKED 基础设施契约"
    if warnings:
        detail += f"; NEED_REVIEW: {'; '.join(warnings[:2])}"
        if len(warnings) > 2:
            detail += "..."
    return check_item("规则4: Contracts Gate 通过", True, detail)


def rule5_no_import_experiments(project_dir: str, track_id: str) -> dict:
    """规则 5：experiments/ 下的脚本不被其他代码 import（扫描整个 src/）。"""
    src_track_dir = os.path.join(project_dir, "src", "tracks", track_id)
    if not os.path.isdir(src_track_dir):
        return check_item("规则5: src/tracks/ 目录存在", False, src_track_dir)

    violations: list[str] = []
    exp_dir = os.path.join(src_track_dir, "experiments")

    # 找出 experiments/ 下的所有 py 模块名
    exp_modules: set[str] = set()
    if os.path.isdir(exp_dir):
        for f in os.listdir(exp_dir):
            if f.endswith(".py") and not f.startswith("__"):
                exp_modules.add(f[:-3])  # 去掉 .py

    if not exp_modules:
        return check_item("规则5: experiments/ 有 py 文件（可检查 import）", False,
                           "没有实验脚本，无法检查 import（请先创建实验）")

    # 扫描整个 src/（跨轨道也检查），跳过该轨道自身的 experiments/
    src_dir = os.path.join(project_dir, "src")
    scan_root = src_dir if os.path.isdir(src_dir) else src_track_dir

    for root, dirs, files in os.walk(scan_root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        # 跳过被检查轨道自身的 experiments/ 目录（它本身当然有这些模块）
        if os.path.abspath(root) == os.path.abspath(exp_dir):
            dirs[:] = []
            continue

        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = []
                    if isinstance(node, ast.ImportFrom) and node.module:
                        names.append(node.module)
                    elif isinstance(node, ast.Import):
                        names.extend(alias.name for alias in node.names)

                    for name in names:
                        parts = name.split(".")
                        if "experiments" in parts:
                            violations.append(f"{fpath}: import {name}")

    passed = len(violations) == 0
    return check_item("规则5: 没有代码 import experiments/", passed,
                       "; ".join(violations[:3]) + ("..." if len(violations) > 3 else ""))


def evaluate_research_gate(project_dir: str, track_id: str) -> dict:
    registry = load_registry(project_dir)
    track = require_track(
        registry,
        track_id,
        error_cls=ResearchGateError,
        expected_type="research",
    )
    current_phase = find_current_phase(project_dir, registry)
    context = build_context(project_dir, track_id, current_phase)
    cycle_label = get_cycle_label(registry)

    checks = [
        rule1_track_log(project_dir, track_id, current_phase, context, cycle_label),
        rule2_smoke_test(project_dir, track_id, context),
        rule3_params_recorded(project_dir, track_id, current_phase),
        rule4_contracts(project_dir, registry),
        rule5_no_import_experiments(project_dir, track_id),
    ]

    return gate_payload(
        "Research Gate",
        checks,
        data={
            "track_id": track_id,
            "state": track.get("state"),
            "current_phase": current_phase,
            "cycle_label": cycle_label,
            "latest_exp_id": context.get("latest_exp_id"),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Research Gate rules for a research track")
    parser.add_argument("--track-id", required=True, help="Track ID (e.g. research_strategy_momentum)")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    args = parser.parse_args()
    run_action(
        lambda: evaluate_research_gate(args.project_dir, args.track_id),
        ResearchGateError,
    )


if __name__ == "__main__":
    main()
