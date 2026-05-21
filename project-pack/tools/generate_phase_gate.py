#!/usr/bin/env python3
"""
generate_phase_gate.py — 基于当前项目状态生成 PHASE_GATE.md 草稿

退出码:
  0  PHASE_GATE.md 生成成功（无论当前是否推荐推进）
  2  文件缺失或格式错误

用法:
  python3 tools/generate_phase_gate.py --project-dir <path>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _phase_docs import (
    PHASE_NAME_TO_NUM,
    PHASE_TRANSITIONS,
    extract_approval_section,
    render_phase_gate_content,
)
from _registry import (
    get_phase_override,
    get_recorded_phase,
    load_registry as _shared_load_registry,
)
from _output import check_item, error
from check_phase_gate import (
    PHASE_REQUIRED_CHECKLIST_ITEMS,
    _evaluate_phase_0_to_1,
    _evaluate_phase_1_to_2,
    _evaluate_phase_2_to_3,
)


def load_registry(project_dir: Path) -> dict:
    try:
        return _shared_load_registry(project_dir)
    except Exception as exc:
        error(str(exc))


def evaluate_phase(project_dir: Path, registry: dict) -> tuple[str, str, int, int, dict]:
    override = get_phase_override(registry)
    if override:
        error("检测到 current_phase_override 正在生效；常规 PHASE_GATE 生成已暂停，请先完成例外处理并移除 override")

    current_phase = get_recorded_phase(registry, "")
    if current_phase not in PHASE_TRANSITIONS:
        error(f"当前阶段 {current_phase} 不支持生成 PHASE_GATE.md（可能已在最终阶段）")
    target_phase = PHASE_TRANSITIONS[current_phase]
    from_phase_num = PHASE_NAME_TO_NUM[current_phase]
    to_phase_num = PHASE_NAME_TO_NUM[target_phase]

    if from_phase_num == 0:
        evaluation = _evaluate_phase_0_to_1(str(project_dir), registry)
    elif from_phase_num == 1:
        evaluation = _evaluate_phase_1_to_2(str(project_dir), registry)
    elif from_phase_num == 2:
        evaluation = _evaluate_phase_2_to_3(str(project_dir), registry)
    else:
        error(f"不支持的阶段编号: {from_phase_num}")

    return current_phase, target_phase, from_phase_num, to_phase_num, evaluation


def render_phase_gate(project_dir: Path) -> dict:
    registry = load_registry(project_dir)
    current_phase, target_phase, from_phase_num, to_phase_num, evaluation = evaluate_phase(project_dir, registry)

    gate_path = project_dir / "prae" / "phases" / current_phase / "PHASE_GATE.md"
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    approval_section = None
    if gate_path.exists():
        approval_section = extract_approval_section(gate_path.read_text(encoding="utf-8"))

    content = render_phase_gate_content(
        project_dir,
        registry,
        current_phase=current_phase,
        target_phase=target_phase,
        from_phase_num=from_phase_num,
        to_phase_num=to_phase_num,
        evaluation=evaluation,
        required_items=PHASE_REQUIRED_CHECKLIST_ITEMS,
        approval_section=approval_section,
    )
    gate_path.write_text(content, encoding="utf-8")

    gate_passed = all(evaluation["gate_conditions"].values())
    return {
        "summary": f"PHASE_GATE.md 已生成（{'推荐推进' if gate_passed else '暂不推进'}）",
        "checks": [
            check_item("PHASE_GATE.md 已写入", True, str(gate_path)),
            check_item("阶段门控已评估", True, evaluation["summary"]),
        ],
        "data": {
            "path": str(gate_path),
            "current_phase": current_phase,
            "target_phase": target_phase,
            "gate_passed": gate_passed,
            "recommendation": "推进" if gate_passed else "暂不推进",
            "failed_conditions": [
                item for item, passed in evaluation["gate_conditions"].items() if not passed
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="生成当前阶段的 PHASE_GATE.md")
    parser.add_argument("--project-dir", required=True, help="研究项目根目录")
    args = parser.parse_args()

    payload = render_phase_gate(Path(args.project_dir))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
