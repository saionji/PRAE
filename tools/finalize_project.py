#!/usr/bin/env python3
"""
finalize_project.py — 根据已批准的 CONCLUSION.md 记录项目终态决定

退出码:
  0  记录成功
  1  最终决定尚未满足执行条件
  2  文件缺失或格式错误

用法:
  python3 tools/finalize_project.py --project-dir <path>
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _registry import save_registry
from _output import check_item
from check_conclusion import evaluate_conclusion
from generate_conclusion import ConclusionError, load_registry


def finalize_project(project_dir: Path) -> dict:
    evaluation = evaluate_conclusion(str(project_dir))
    checks = list(evaluation["checks"])

    approved_yes = evaluation["data"]["approved"] == "yes"
    checks.append(check_item("CONCLUSION 已 APPROVED: yes", approved_yes, f"当前值={evaluation['data']['approved']}"))
    terminal_decision = evaluation["data"]["decision"] in {"ARCHIVED", "GRADUATED_TO_PDAE"}
    checks.append(check_item(
        "DECISION 为终态（ARCHIVED / GRADUATED_TO_PDAE）",
        terminal_decision,
        f"当前值={evaluation['data']['decision']}；CONTINUE 请改用 reopen_project.py",
    ))

    if not evaluation["passed"] or not approved_yes or not terminal_decision:
        return {
            "passed": False,
            "summary": "项目收尾失败：CONCLUSION.md 尚未满足终态决定要求",
            "checks": checks,
            "data": {"finalized": False, **evaluation["data"]},
        }

    registry = load_registry(project_dir)
    decision = evaluation["data"]["decision"]
    approver = evaluation["data"]["approver"]
    approved_at = evaluation["data"]["approved_at"]

    registry["project_decision"] = decision
    registry["project_approver"] = approver
    registry["project_decided_at"] = approved_at
    registry["project_finalized_at"] = str(datetime.date.today())
    registry["updated"] = str(datetime.date.today())
    if decision == "ARCHIVED":
        registry["archived_at"] = approved_at
    elif "archived_at" in registry:
        registry.pop("archived_at")

    registry_path = save_registry(project_dir, registry)
    checks.append(check_item("track_registry.yaml 已记录项目终态决定", True, str(registry_path)))

    return {
        "passed": True,
        "summary": f"项目终态决定已记录: {decision}",
        "checks": checks,
        "data": {
            **evaluation["data"],
            "registry_path": str(registry_path),
            "finalized": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="根据 CONCLUSION.md 记录项目终态决定")
    parser.add_argument("--project-dir", required=True, help="研究项目根目录")
    args = parser.parse_args()

    run_action(lambda: finalize_project(Path(args.project_dir)), ConclusionError)


if __name__ == "__main__":
    main()
