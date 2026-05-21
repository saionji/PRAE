#!/usr/bin/env python3
"""
check_conclusion.py — 验证 Phase 3 的 CONCLUSION.md

退出码:
  0  检查通过
  1  检查不通过
  2  文件缺失或格式错误

用法:
  python3 tools/check_conclusion.py --project-dir <path> [--check-approved]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _conclusion_docs import (
    CONCLUSION_SECTIONS,
    FINAL_DECISION_FIELDS,
    VALID_DECISIONS,
    extract_final_decision_body,
    parse_final_decision_fields,
)
from _gate_utils import gate_payload
from _registry import get_cycle_label, get_recorded_phase
from _output import check_item
from generate_conclusion import (
    ConclusionError,
    load_registry,
)


def _validate_structure(content: str, registry: dict) -> list[dict]:
    checks: list[dict] = []
    project_name = registry.get("project", "unknown-project")
    cycle_label = get_cycle_label(registry)

    checks.append(check_item("CONCLUSION 标题正确", f"# CONCLUSION — {project_name}" in content, project_name))
    cycle_ok = re.search(rf"\*\*研究轮次\*\*:\s*{re.escape(cycle_label)}", content) is not None
    checks.append(check_item("CONCLUSION 研究轮次正确", cycle_ok, cycle_label))
    for section in CONCLUSION_SECTIONS:
        checks.append(check_item(f"CONCLUSION 包含章节: {section}", section in content, section))

    final_section = extract_final_decision_body(content)
    field_labels = {
        "APPROVED": "APPROVED",
        "DECISION": "DECISION",
        "APPROVER": "APPROVER",
        "APPROVED_AT": "APPROVED_AT",
        "COMMENT": "COMMENT",
    }
    for field in FINAL_DECISION_FIELDS:
        present = re.search(rf"^{field}:[ \t]*.*$", final_section, re.MULTILINE) is not None
        checks.append(check_item(f"CONCLUSION 包含 {field_labels[field]} 字段", present))

    outcomes_section = re.search(r"## 各轨道去向\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    outcomes_text = outcomes_section.group(1) if outcomes_section else ""
    for track in registry.get("tracks", []):
        checks.append(check_item(
            f"各轨道去向包含 {track['id']}",
            f"`{track['id']}`" in outcomes_text,
            track["id"],
        ))

    graduated_section = re.search(r"## 毕业轨道的 PDAE 项目链接\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    graduated_text = graduated_section.group(1) if graduated_section else ""
    for track in registry.get("tracks", []):
        if track.get("type") == "research" and track.get("state") == "GRADUATED":
            checks.append(check_item(
                f"PDAE 项目链接包含 {track['id']}",
                f"`{track['id']}`" in graduated_text,
                track["id"],
            ))

    return checks


def evaluate_conclusion(project_dir: str) -> dict:
    registry = load_registry(Path(project_dir))
    current_phase = get_recorded_phase(registry, "")
    if current_phase != "phase_03_conclusion":
        raise ConclusionError(f"当前阶段为 {current_phase}，只能检查 phase_03_conclusion 的 CONCLUSION.md")

    conclusion_path = Path(project_dir) / "prae" / "phases" / "phase_03_conclusion" / "CONCLUSION.md"
    if not conclusion_path.exists():
        raise ConclusionError(f"CONCLUSION.md 不存在: {conclusion_path}")

    content = conclusion_path.read_text(encoding="utf-8")
    checks = _validate_structure(content, registry)

    final_section = extract_final_decision_body(content)
    final_fields = parse_final_decision_fields(final_section)
    approved = final_fields["APPROVED"] or "未找到"
    decision = final_fields["DECISION"]
    approver = final_fields["APPROVER"]
    approved_at = final_fields["APPROVED_AT"]
    comment = final_fields["COMMENT"]

    checks.append(check_item("APPROVED 字段合法", approved in {"yes", "no", "pending"}, f"当前值={approved}"))
    checks.append(check_item(
        "DECISION 字段合法或留空",
        decision in VALID_DECISIONS or decision == "",
        decision or "空",
    ))
    checks.append(check_item(
        "APPROVED_AT 格式正确或留空",
        approved_at == "" or re.fullmatch(r"\d{4}-\d{2}-\d{2}", approved_at) is not None,
        approved_at or "空",
    ))
    if approved == "yes":
        checks.append(check_item("最终决定合法", decision in VALID_DECISIONS, decision or "未找到决定"))
        checks.append(check_item("批准人已填写", bool(approver), approver or "批准人为空"))
        checks.append(check_item(
            "日期格式正确",
            re.fullmatch(r"\d{4}-\d{2}-\d{2}", approved_at) is not None,
            approved_at or "日期为空",
        ))

        graduated_tracks = [
            t for t in registry.get("tracks", [])
            if t.get("type") == "research" and t.get("state") == "GRADUATED"
        ]
        graduated_with_pdae = [t for t in graduated_tracks if t.get("pdae_project")]

        if decision == "GRADUATED_TO_PDAE":
            checks.append(check_item("至少 1 条 GRADUATED 轨道存在", len(graduated_tracks) >= 1))
            checks.append(check_item("至少 1 条 GRADUATED 轨道已登记 PDAE 项目", len(graduated_with_pdae) >= 1))
        elif decision == "ARCHIVED":
            checks.append(check_item(
                "ARCHIVED 时没有 PDAE 项目登记",
                len(graduated_with_pdae) == 0,
                ",".join(t["id"] for t in graduated_with_pdae) if graduated_with_pdae else "",
            ))

    return gate_payload(
        "CONCLUSION 检查",
        checks,
        data={
            "path": str(conclusion_path),
            "approved": approved,
            "decision": decision,
            "approver": approver,
            "approved_at": approved_at,
            "comment": comment,
        },
    )


def check_conclusion(project_dir: str, check_approved: bool) -> dict:
    evaluation = evaluate_conclusion(project_dir)
    checks = list(evaluation["checks"])
    passed = evaluation["passed"]
    if check_approved:
        approved_yes = evaluation["data"]["approved"] == "yes"
        checks.append(check_item("APPROVED: yes", approved_yes, f"当前值={evaluation['data']['approved']}"))
        passed = passed and approved_yes

    return {
        "passed": passed,
        "summary": evaluation["summary"],
        "checks": checks,
        "data": evaluation["data"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="检查 Phase 3 的 CONCLUSION.md")
    parser.add_argument("--project-dir", required=True, help="研究项目根目录")
    parser.add_argument("--check-approved", action="store_true", help="要求 CONCLUSION.md 已 APPROVED: yes")
    args = parser.parse_args()
    run_action(
        lambda: check_conclusion(args.project_dir, args.check_approved),
        ConclusionError,
    )


if __name__ == "__main__":
    main()
