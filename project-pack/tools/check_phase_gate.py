#!/usr/bin/env python3
"""
check_phase_gate.py — 验证 PRAE 阶段门控条件

退出码:
  0  所有门控条件通过（或已批准）
  1  门控条件未满足
  2  文件缺失或格式错误

用法:
  python3 tools/check_phase_gate.py --project-dir <path> [--phase 0|1|2|3]
  python3 tools/check_phase_gate.py --project-dir <path> --check-approved
"""
from __future__ import annotations
import argparse
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _gate_utils import collapse_text, gate_payload, summarize_violations
from _phase_docs import PHASE_NAME_TO_NUM
from _registry import (
    get_cycle_label,
    get_phase_override,
    get_recorded_phase,
    load_registry as _shared_load_registry,
)
from check_contracts import run_check
from check_research_gate import ResearchGateError, evaluate_research_gate
from _output import check_item


class PhaseGateError(RuntimeError):
    """Raised when phase gate artifacts are missing or malformed."""


PHASE_DIRS = {phase_num: phase_name for phase_name, phase_num in PHASE_NAME_TO_NUM.items()}
PHASE_GATE_SECTIONS = [
    "## 1. 当前阶段状态",
    "## 2. 门控条件逐项检查",
    "## 3. 证据摘要",
    "## 4. 风险与未决项",
    "## 5. 建议",
    "## 6. 待人工批准",
]
PHASE_REQUIRED_CHECKLIST_ITEMS = {
    0: [
        "所有 type=infrastructure 的轨道 state = LOCKED",
        "每条 LOCKED 轨道都有 contracts.yaml",
        "每条 LOCKED 轨道都有 MODULE_SPEC.md",
        "每条 LOCKED 轨道都通过 PDAE M3 门控（记录在 TRACK_LOG.md）",
        "check_contracts.py 对所有基础设施契约通过",
    ],
    1: [
        "≥1 条研究轨道 state = ACTIVE（有正向信号）",
        "所有仍 EXPLORING 的研究轨道有明确去留建议（继续 / KILL / 合并）",
        "每条 ACTIVE 轨道通过 Research Gate 检查",
    ],
    2: [
        "所有原 ACTIVE 研究轨道有明确终态建议",
        "至少一条轨道判定 GRADUATED（否则考虑整体 KILL 项目）",
        "所有 GRADUATED 候选通过 Research Gate 和 Contracts Gate",
        "所有 GRADUATED 候选有 TRACK_LOG.md 的最终结论段落",
    ],
}


def load_registry(project_dir: str) -> dict:
    try:
        return _shared_load_registry(project_dir, error_cls=PhaseGateError)
    except Exception as exc:
        raise PhaseGateError(str(exc)) from exc


def _normalize_checklist_text(text: str) -> str:
    normalized = text.replace("`", "")
    normalized = normalized.replace("（", "(").replace("）", ")")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()

def _extract_checklist_statuses(content: str) -> dict[str, bool]:
    checklist_section = re.search(r"## 2\. 门控条件逐项检查\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not checklist_section:
        return {}

    statuses: dict[str, bool] = {}
    for line in checklist_section.group(1).splitlines():
        match = re.match(r"\s*-\s*\[([xX ])\]\s*(.+?)\s*$", line)
        if not match:
            continue
        statuses[_normalize_checklist_text(match.group(2))] = match.group(1).lower() == "x"
    return statuses


def _validate_phase_gate_document(gate_path: str, expected_from_phase: int | None,
                                  registry: dict | None = None) -> tuple[list[dict], str]:
    with open(gate_path, encoding="utf-8") as f:
        content = f.read()

    checks: list[dict] = []
    if registry is not None:
        expected_cycle = get_cycle_label(registry)
        cycle_ok = re.search(rf"\*\*研究轮次\*\*:\s*{re.escape(expected_cycle)}", content) is not None
        checks.append(check_item("PHASE_GATE 研究轮次正确", cycle_ok, expected_cycle))

    if expected_from_phase is not None and expected_from_phase in {0, 1, 2}:
        expected_title = f"# Phase {expected_from_phase} → Phase {expected_from_phase + 1} 门控分析"
        checks.append(check_item("PHASE_GATE 标题正确", expected_title in content, expected_title))

        expected_target = PHASE_DIRS[expected_from_phase + 1]
        target_ok = re.search(rf"\*\*目标阶段\*\*:\s*{re.escape(expected_target)}", content) is not None
        checks.append(check_item("PHASE_GATE 目标阶段正确", target_ok, expected_target))
    else:
        title_ok = re.search(r"^# Phase \d+ → Phase \d+ 门控分析$", content, re.MULTILINE) is not None
        checks.append(check_item("PHASE_GATE 标题格式正确", title_ok))

    generated_date_ok = re.search(r"\*\*生成日期\*\*:\s*\d{4}-\d{2}-\d{2}", content) is not None
    checks.append(check_item("PHASE_GATE 有生成日期", generated_date_ok))

    generated_by_ok = re.search(r"\*\*生成者\*\*:\s*AI", content) is not None
    checks.append(check_item("PHASE_GATE 有生成者", generated_by_ok))

    for section in PHASE_GATE_SECTIONS:
        checks.append(check_item(f"PHASE_GATE 包含章节: {section}", section in content, section))

    checklist_section = re.search(r"## 2\. 门控条件逐项检查\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    has_checkbox = bool(checklist_section and re.search(r"^- \[[xX ]\]\s+", checklist_section.group(1), re.MULTILINE))
    checks.append(check_item("PHASE_GATE 含勾选清单", has_checkbox, "第 2 节至少要有一个 [ ] / [x] 条目"))
    if expected_from_phase in PHASE_REQUIRED_CHECKLIST_ITEMS and checklist_section:
        normalized_section = _normalize_checklist_text(checklist_section.group(1))
        for item in PHASE_REQUIRED_CHECKLIST_ITEMS[expected_from_phase]:
            normalized_item = _normalize_checklist_text(item)
            checks.append(check_item(
                f"PHASE_GATE 包含必需门控项: {normalized_item}",
                normalized_item in normalized_section,
                item,
            ))

    recommendation_ok = re.search(r"\*\*推荐动作\*\*:\s*(推进|暂不推进)", content) is not None
    checks.append(check_item("PHASE_GATE 有推荐动作", recommendation_ok))

    reason_ok = re.search(r"\*\*理由\*\*:\s*\S+", content) is not None
    checks.append(check_item("PHASE_GATE 有理由", reason_ok))

    for field in ("APPROVED", "APPROVER", "APPROVED_AT", "COMMENT"):
        field_ok = re.search(rf"^{field}:\s*.*$", content, re.MULTILINE) is not None
        checks.append(check_item(f"PHASE_GATE 包含字段: {field}", field_ok, field))

    return checks, content


def _run_contract_gate(project_dir: str, track: dict) -> dict:
    track_id = track["id"]
    contracts_rel = track.get("contracts", "")
    if not contracts_rel:
        return check_item(f"{track_id}: check_contracts 通过", False, "contracts 字段未填写")

    src_dir = Path(project_dir) / "src"
    if not src_dir.is_dir():
        return check_item(f"{track_id}: check_contracts 通过", False, f"src 目录不存在: {src_dir}")

    contracts_path = Path(project_dir) / contracts_rel
    if not contracts_path.exists():
        return check_item(f"{track_id}: check_contracts 通过", False, str(contracts_path))

    try:
        with open(contracts_path, encoding="utf-8") as f:
            contract_data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as exc:
        return check_item(f"{track_id}: check_contracts 通过", False, f"contracts 解析失败: {exc}")
    if contract_data is not None and not isinstance(contract_data, dict):
        return check_item(f"{track_id}: check_contracts 通过", False, "contracts 顶层必须是 mapping")

    violations = run_check(contracts_path, [src_dir])
    if violations.has_immutable() or violations.has_critical():
        return check_item(f"{track_id}: check_contracts 通过", False,
                          summarize_violations(track_id, violations))

    detail = "无阻塞性契约违规"
    if violations.has_need_review():
        detail = summarize_violations(track_id, violations)
    return check_item(f"{track_id}: check_contracts 通过", True, detail)


def _run_research_gate(project_dir: str, track_id: str) -> dict:
    try:
        evaluation = evaluate_research_gate(project_dir, track_id)
    except ResearchGateError as exc:
        return check_item(f"{track_id}: Research Gate 通过", False, collapse_text(str(exc)))

    failed_checks = [c["name"] for c in evaluation["checks"] if not c.get("passed")]
    detail = evaluation["summary"]
    if failed_checks:
        detail += f"; 未通过: {', '.join(failed_checks[:3])}"
        if len(failed_checks) > 3:
            detail += "..."
    latest_exp_id = evaluation.get("data", {}).get("latest_exp_id")
    if latest_exp_id:
        detail += f"; latest_exp={latest_exp_id}"

    return check_item(f"{track_id}: Research Gate 通过", evaluation["passed"], detail)


def _evaluate_phase_0_to_1(project_dir: str, registry: dict) -> dict:
    checks: list[dict] = []
    infra_tracks = [t for t in registry.get("tracks", []) if t.get("type") == "infrastructure"]
    gate_conditions = {item: False for item in PHASE_REQUIRED_CHECKLIST_ITEMS[0]}

    if not infra_tracks:
        checks.append(check_item("至少有一条基础设施轨道", False, "track_registry.yaml 中没有 infrastructure 类型轨道"))
        return {"checks": checks, "gate_conditions": gate_conditions, "summary": "无基础设施轨道"}

    state_results: list[bool] = []
    contracts_results: list[bool] = []
    spec_results: list[bool] = []
    pdae_results: list[bool] = []
    contract_gate_results: list[bool] = []

    for t in infra_tracks:
        tid = t["id"]
        state = t.get("state", "")

        locked = state == "LOCKED"
        state_results.append(locked)
        checks.append(check_item(f"{tid}: state=LOCKED", locked, f"state={state}"))

        contracts_path = t.get("contracts", "")
        contracts_exists = bool(contracts_path) and os.path.exists(os.path.join(project_dir, contracts_path))
        contracts_results.append(contracts_exists)
        checks.append(check_item(f"{tid}: contracts.yaml 存在", contracts_exists, contracts_path or "字段未填写"))

        spec_path = t.get("module_spec", "")
        spec_exists = bool(spec_path) and os.path.exists(os.path.join(project_dir, spec_path))
        spec_results.append(spec_exists)
        checks.append(check_item(f"{tid}: MODULE_SPEC.md 存在", spec_exists, spec_path or "字段未填写"))

        contract_gate_check = _run_contract_gate(project_dir, t)
        contract_gate_results.append(contract_gate_check["passed"])
        checks.append(contract_gate_check)

        track_log = os.path.join(project_dir, "prae", "phases", "phase_00_infra", "tracks", tid, "TRACK_LOG.md")
        log_exists = os.path.exists(track_log)
        checks.append(check_item(f"{tid}: TRACK_LOG.md 存在", log_exists))

        has_pdae_record = False
        if log_exists:
            with open(track_log, encoding="utf-8") as f:
                log_content = f.read()
            has_pdae_record = "PDAE" in log_content or "M3" in log_content or "LOCKED" in log_content
        pdae_results.append(has_pdae_record)
        checks.append(check_item(
            f"{tid}: TRACK_LOG 有 PDAE/LOCKED 记录",
            has_pdae_record,
            "TRACK_LOG.md 中未找到 PDAE 或 M3 或 LOCKED 相关记录",
        ))

    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[0][0]] = all(state_results)
    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[0][1]] = all(contracts_results)
    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[0][2]] = all(spec_results)
    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[0][3]] = all(pdae_results)
    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[0][4]] = all(contract_gate_results)

    for item in PHASE_REQUIRED_CHECKLIST_ITEMS[0]:
        checks.append(check_item(f"门控条件: {item}", gate_conditions[item]))

    payload = gate_payload("Phase 0→1 门控", checks)
    payload["gate_conditions"] = gate_conditions
    return payload


def _evaluate_phase_1_to_2(project_dir: str, registry: dict) -> dict:
    checks: list[dict] = []
    research_tracks = [t for t in registry.get("tracks", []) if t.get("type") == "research"]
    gate_conditions = {item: False for item in PHASE_REQUIRED_CHECKLIST_ITEMS[1]}

    has_active = any(t.get("state") == "ACTIVE" for t in research_tracks)
    checks.append(check_item("至少 1 条研究轨道 state=ACTIVE", has_active,
                              "所有研究轨道仍为 EXPLORING" if not has_active else ""))

    exploring_decisions: list[bool] = []
    active_research_gate: list[bool] = []

    for t in research_tracks:
        tid = t["id"]
        state = t.get("state", "")

        if state == "EXPLORING":
            track_log = os.path.join(project_dir, "prae", "phases", "phase_01_research", "tracks", tid, "TRACK_LOG.md")
            log_exists = os.path.exists(track_log)
            if log_exists:
                with open(track_log, encoding="utf-8") as f:
                    log_content = f.read()
                has_decision = "Decision Log" in log_content and len(
                    [l for l in log_content.splitlines() if "KILL" in l or "继续" in l or "MERGE" in l]
                ) > 0
                exploring_decisions.append(has_decision)
                checks.append(check_item(
                    f"{tid}: EXPLORING 轨道有去留建议",
                    has_decision,
                    "TRACK_LOG.md Decision Log 中未找到 KILL/继续/MERGE 建议",
                ))
            else:
                exploring_decisions.append(False)
                checks.append(check_item(f"{tid}: TRACK_LOG.md 存在", False, track_log))

        if state == "ACTIVE":
            exp_count = t.get("experiments", 0)
            checks.append(check_item(f"{tid}: 有至少 1 次实验", exp_count >= 1, f"experiments={exp_count}"))
            research_gate_check = _run_research_gate(project_dir, tid)
            active_research_gate.append(research_gate_check["passed"])
            checks.append(research_gate_check)

    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[1][0]] = has_active
    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[1][1]] = bool(exploring_decisions) and all(exploring_decisions) if any(
        t.get("state") == "EXPLORING" for t in research_tracks
    ) else True
    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[1][2]] = has_active and bool(active_research_gate) and all(active_research_gate)

    for item in PHASE_REQUIRED_CHECKLIST_ITEMS[1]:
        checks.append(check_item(f"门控条件: {item}", gate_conditions[item]))

    payload = gate_payload("Phase 1→2 门控", checks)
    payload["gate_conditions"] = gate_conditions
    return payload


def _evaluate_phase_2_to_3(project_dir: str, registry: dict) -> dict:
    checks: list[dict] = []
    research_tracks = [t for t in registry.get("tracks", []) if t.get("type") == "research"]
    gate_conditions = {item: False for item in PHASE_REQUIRED_CHECKLIST_ITEMS[2]}

    active_tracks = [t for t in research_tracks if t.get("state") == "ACTIVE"]
    graduated_tracks = [t for t in research_tracks if t.get("state") == "GRADUATED"]

    has_graduated = len(graduated_tracks) >= 1
    checks.append(check_item("至少 1 条轨道判定 GRADUATED", has_graduated,
                              "没有 GRADUATED 轨道，考虑是否整体终止项目"))

    no_active_remaining = len(active_tracks) == 0
    checks.append(check_item("所有研究轨道已有终态（无 ACTIVE 剩余）", no_active_remaining,
                              f"仍有 {len(active_tracks)} 条轨道处于 ACTIVE: "
                              f"{', '.join(t['id'] for t in active_tracks)}" if active_tracks else ""))

    graduated_research_gate: list[bool] = []
    graduated_final_logs: list[bool] = []
    for t in graduated_tracks:
        tid = t["id"]
        track_log_path = os.path.join(project_dir, "prae", "phases", "phase_02_validation", "tracks", tid, "TRACK_LOG.md")
        if not os.path.exists(track_log_path):
            graduated_final_logs.append(False)
            checks.append(check_item(f"{tid}: TRACK_LOG.md 存在", False, track_log_path))
            continue

        with open(track_log_path, encoding="utf-8") as f:
            log_content = f.read()
        has_final = "GRADUATED" in log_content
        graduated_final_logs.append(has_final)
        checks.append(check_item(f"{tid}: TRACK_LOG 有最终结论段落", has_final))

        research_gate_check = _run_research_gate(project_dir, tid)
        graduated_research_gate.append(research_gate_check["passed"])
        checks.append(research_gate_check)

    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[2][0]] = no_active_remaining
    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[2][1]] = has_graduated
    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[2][2]] = has_graduated and bool(graduated_research_gate) and all(graduated_research_gate)
    gate_conditions[PHASE_REQUIRED_CHECKLIST_ITEMS[2][3]] = has_graduated and bool(graduated_final_logs) and all(graduated_final_logs)

    for item in PHASE_REQUIRED_CHECKLIST_ITEMS[2]:
        checks.append(check_item(f"门控条件: {item}", gate_conditions[item]))

    payload = gate_payload("Phase 2→3 门控", checks)
    payload["gate_conditions"] = gate_conditions
    return payload


def evaluate_approval(project_dir: str, registry: dict) -> dict:
    override = get_phase_override(registry)
    if override:
        raise PhaseGateError(
            "检测到 current_phase_override 正在生效；常规 PHASE_GATE / advance-phase 已暂停，请先完成例外处理并移除 override"
        )

    current = get_recorded_phase(registry, "")
    gate_path = os.path.join(project_dir, "prae", "phases", current, "PHASE_GATE.md")
    if not os.path.exists(gate_path):
        raise PhaseGateError(f"PHASE_GATE.md 不存在: {gate_path}")

    expected_from_phase = PHASE_NAME_TO_NUM.get(current)
    checks, content = _validate_phase_gate_document(gate_path, expected_from_phase, registry)

    m = re.search(r"^APPROVED:\s*(yes|no|pending)\s*$", content, re.MULTILINE)
    approved_val = m.group(1) if m else "未找到"
    approved_yes = approved_val == "yes"
    checks.append(check_item("APPROVED: yes", approved_yes, f"当前值={approved_val}"))

    approver_match = re.search(r"^APPROVER:\s*(.*)$", content, re.MULTILINE)
    approver = approver_match.group(1).strip() if approver_match else ""
    checks.append(check_item("APPROVER 已填写", bool(approver) if approved_yes else True,
                             approver or "APPROVER 为空"))

    approved_at_match = re.search(r"^APPROVED_AT:\s*(.*)$", content, re.MULTILINE)
    approved_at = approved_at_match.group(1).strip() if approved_at_match else ""
    date_ok = re.fullmatch(r"\d{4}-\d{2}-\d{2}", approved_at) is not None
    checks.append(check_item("APPROVED_AT 格式正确", date_ok if approved_yes else True,
                             approved_at or "APPROVED_AT 为空"))

    if approved_yes and expected_from_phase in {0, 1, 2}:
        if expected_from_phase == 0:
            evaluation = _evaluate_phase_0_to_1(project_dir, registry)
        elif expected_from_phase == 1:
            evaluation = _evaluate_phase_1_to_2(project_dir, registry)
        else:
            evaluation = _evaluate_phase_2_to_3(project_dir, registry)

        actual_conditions = evaluation["gate_conditions"]
        checklist_statuses = _extract_checklist_statuses(content)
        all_actual_pass = all(actual_conditions.values())
        checks.append(check_item("APPROVED 时实际门控条件全部通过", all_actual_pass, evaluation["summary"]))

        for item in PHASE_REQUIRED_CHECKLIST_ITEMS[expected_from_phase]:
            normalized_item = _normalize_checklist_text(item)
            recorded = checklist_statuses.get(normalized_item)
            actual = actual_conditions[item]
            if recorded is None:
                continue
            checks.append(check_item(
                f"PHASE_GATE 勾选状态匹配: {normalized_item}",
                recorded == actual,
                f"文档={'[x]' if recorded else '[ ]'} 实际={'[x]' if actual else '[ ]'}",
            ))

    passed = all(c["passed"] for c in checks)
    return {
        "passed": passed,
        "summary": f"批准状态: {approved_val}",
        "checks": checks,
        "data": {
            "current_phase": current,
            "gate_path": gate_path,
            "approved": approved_val,
            "approver": approver,
            "approved_at": approved_at,
        },
    }


def evaluate_phase_gate(project_dir: str, phase_num: int | None, check_approved: bool) -> dict:
    registry = load_registry(project_dir)
    override = get_phase_override(registry)
    if override:
        raise PhaseGateError(
            "检测到 current_phase_override 正在生效；常规 Phase Gate 检查已暂停，请先完成例外处理并移除 override"
        )

    current = get_recorded_phase(registry, "")

    if check_approved:
        return evaluate_approval(project_dir, registry)

    effective_phase = phase_num
    if effective_phase is None:
        effective_phase = PHASE_NAME_TO_NUM.get(current, -1)
        if effective_phase == -1:
            raise PhaseGateError(f"无法从 current_phase={current} 推断阶段编号，请用 --phase 指定")

    if effective_phase == 0:
        return _evaluate_phase_0_to_1(project_dir, registry)
    if effective_phase == 1:
        return _evaluate_phase_1_to_2(project_dir, registry)
    if effective_phase == 2:
        return _evaluate_phase_2_to_3(project_dir, registry)
    raise PhaseGateError(f"不支持的阶段编号: {effective_phase}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check PRAE phase-gate conditions")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    parser.add_argument("--phase", type=int, choices=[0, 1, 2], default=None,
                        help="Which phase-advance gate to check (0=Phase0->1, 1=Phase1->2, 2=Phase2->3)")
    parser.add_argument("--check-approved", action="store_true",
                        help="Check whether the current phase's PHASE_GATE.md is APPROVED: yes")
    args = parser.parse_args()
    run_action(
        lambda: evaluate_phase_gate(args.project_dir, args.phase, args.check_approved),
        PhaseGateError,
    )


if __name__ == "__main__":
    main()
