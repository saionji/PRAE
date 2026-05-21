#!/usr/bin/env python3
"""
check_track_status.py — 检查 track_registry.yaml 的一致性

退出码:
  0  所有检查通过
  1  发现不一致
  2  文件缺失或格式错误

用法:
  python3 tools/check_track_status.py --project-dir <path>
"""
from __future__ import annotations
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _cli import emit_payload
from _output import check_item, error
from _registry import RegistryError, get_current_phase, get_phase_override, get_recorded_phase, load_registry


def evaluate(project_dir: str) -> dict:
    try:
        registry = load_registry(project_dir)
    except RegistryError as exc:
        error(str(exc))

    required_top = ["project", "current_phase", "tracks"]
    for field in required_top:
        if field not in registry:
            error(f"track_registry.yaml 缺少必填字段: {field}")

    tracks = registry.get("tracks", [])
    checks: list[dict] = []

    valid_infra_states = {"EXPLORING", "LOCKED"}
    valid_research_states = {"EXPLORING", "ACTIVE", "KILLED", "MERGED", "GRADUATED"}
    valid_types = {"infrastructure", "research"}

    seen_ids: set[str] = set()

    for t in tracks:
        tid = t.get("id", "<未知>")

        # 唯一性
        dup = tid in seen_ids
        checks.append(check_item(f"{tid}: ID 唯一", not dup, "重复 ID" if dup else ""))
        seen_ids.add(tid)

        # 类型
        ttype = t.get("type", "")
        valid_type = ttype in valid_types
        checks.append(check_item(f"{tid}: type 合法", valid_type,
                                  f"type={ttype}" if not valid_type else ""))

        # 状态
        state = t.get("state", "")
        if ttype == "infrastructure":
            valid_state = state in valid_infra_states
        else:
            valid_state = state in valid_research_states
        checks.append(check_item(f"{tid}: state 合法", valid_state,
                                  f"state={state}" if not valid_state else ""))

        # ID 命名约定
        if ttype == "infrastructure":
            correct_prefix = tid.startswith("infra_")
        else:
            correct_prefix = tid.startswith("research_")
        checks.append(check_item(f"{tid}: ID 前缀正确", correct_prefix,
                                  "应以 infra_ 或 research_ 开头" if not correct_prefix else ""))

        # LOCKED 基础设施必须有 contracts 和 module_spec
        if ttype == "infrastructure" and state == "LOCKED":
            has_contracts = bool(t.get("contracts"))
            has_spec = bool(t.get("module_spec"))
            contracts_exists = has_contracts and os.path.exists(
                os.path.join(project_dir, t["contracts"]))
            spec_exists = has_spec and os.path.exists(
                os.path.join(project_dir, t["module_spec"]))

            checks.append(check_item(f"{tid}: contracts 字段存在", has_contracts))
            checks.append(check_item(f"{tid}: contracts 文件存在", contracts_exists,
                                      f"{t.get('contracts')}" if not contracts_exists else ""))
            checks.append(check_item(f"{tid}: module_spec 字段存在", has_spec))
            checks.append(check_item(f"{tid}: module_spec 文件存在", spec_exists,
                                      f"{t.get('module_spec')}" if not spec_exists else ""))

        # MERGED 轨道必须有 merged_into
        if state == "MERGED":
            has_merged_into = bool(t.get("merged_into"))
            checks.append(check_item(f"{tid}: MERGED 时有 merged_into", has_merged_into))

        # 终态研究轨道必须有 concluded_at
        if ttype == "research" and state in {"KILLED", "MERGED", "GRADUATED"}:
            has_concluded = bool(t.get("concluded_at"))
            checks.append(check_item(f"{tid}: 终态时有 concluded_at", has_concluded,
                                      "KILLED/MERGED/GRADUATED 轨道必须填 concluded_at"))

        # src 目录存在（若字段填写了）
        src = t.get("src", "")
        if src:
            src_path = os.path.join(project_dir, src)
            src_exists = os.path.isdir(src_path)
            checks.append(check_item(f"{tid}: src 目录存在", src_exists,
                                      src_path if not src_exists else ""))

    all_passed = all(c["passed"] for c in checks)
    failed = [c for c in checks if not c["passed"]]
    summary = (
        f"通过 ({len(tracks)} 条轨道，{len(checks)} 项检查)"
        if all_passed
        else f"失败 ({len(failed)} 项不通过)"
    )
    return {
        "passed": all_passed,
        "summary": summary,
        "checks": checks,
        "data": {
            "tracks": len(tracks),
            "current_phase": get_current_phase(registry),
            "recorded_phase": get_recorded_phase(registry),
            "current_phase_override": get_phase_override(registry),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="检查 PRAE track_registry.yaml 一致性")
    parser.add_argument("--project-dir", required=True, help="研究项目根目录")
    args = parser.parse_args()
    emit_payload(evaluate(args.project_dir))


if __name__ == "__main__":
    main()
