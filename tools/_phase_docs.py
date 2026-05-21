"""Shared phase-level document rendering helpers for PRAE tools."""
from __future__ import annotations

import datetime
import re
from pathlib import Path

from _registry import get_cycle_label, get_recorded_phase


PHASE_TRANSITIONS = {
    "phase_00_infra": "phase_01_research",
    "phase_01_research": "phase_02_validation",
    "phase_02_validation": "phase_03_conclusion",
}

PHASE_NAME_TO_NUM = {
    "phase_00_infra": 0,
    "phase_01_research": 1,
    "phase_02_validation": 2,
    "phase_03_conclusion": 3,
}

PHASE_BRIEF_CONFIG = {
    "phase_01_research": {
        "goal": "完成研究轨道的首轮实验与证据积累，识别值得进入验证期的 ACTIVE 路线。",
        "success": [
            "每条在场研究轨道至少完成 1 次实验并记录到 TRACK_LOG.md",
            "至少 1 条研究轨道出现正向信号并进入 ACTIVE",
            "所有仍 EXPLORING 的轨道形成明确去留建议",
        ],
        "target_state": "ACTIVE / KILLED / MERGED",
        "milestone": ("首轮实验完成", "待定", "完成第一轮 EXP 记录并沉淀证据摘要"),
    },
    "phase_02_validation": {
        "goal": "对进入验证期的 ACTIVE 轨道做严格验证，收敛到明确终态并筛出 GRADUATED 候选。",
        "success": [
            "每条在场轨道完成严格验证实验并补齐证据摘要",
            "所有在场轨道形成明确终态建议（GRADUATED / KILLED / MERGED）",
            "至少 1 条轨道满足进入 Phase 3 的 GRADUATED 条件",
        ],
        "target_state": "GRADUATED / KILLED / MERGED",
        "milestone": ("验证结论收敛", "待定", "完成终态建议并准备 PHASE_GATE.md"),
    },
    "phase_03_conclusion": {
        "goal": "汇总项目最终结论，为所有 GRADUATED 轨道登记待 PDAE 路由，并准备项目收尾。",
        "success": [
            "所有 GRADUATED 轨道在 PHASE_BRIEF.md 中登记待 PDAE 路由",
            "项目级 CONCLUSION.md 完成最终结论整理",
            "所有遗留风险、未决事项和后续工程化动作已留痕",
        ],
        "target_state": "待 PDAE 路由",
        "milestone": ("项目结论收口", "待定", "生成 CONCLUSION.md 并安排 PDAE 路由"),
    },
}


def render_phase0_brief(registry: dict, infra_tracks: list[dict]) -> str:
    today = str(datetime.date.today())
    cycle_label = get_cycle_label(registry)

    if infra_tracks:
        track_rows = "\n".join(
            f"| `{track['id']}` | infrastructure | EXPLORING | LOCKED | "
            f"{track.get('description', '待补充')}；LOCKED 标准：{track.get('lock_criteria', '待补充')} |"
            for track in infra_tracks
        )
    else:
        track_rows = "| `—` | infrastructure | — | — | 当前无基础设施轨道 |"

    return "\n".join([
        "# Phase 00_infra 阶段简报",
        "",
        "**阶段**: phase_00_infra",
        f"**研究轮次**: {cycle_label}",
        f"**创建日期**: {today}",
        "**创建者**: AI（分析者角色）",
        "",
        "---",
        "",
        "## 阶段目标",
        "",
        "完成所有基础设施轨道的选型、契约冻结和 PDAE M3 实现，为研究阶段提供稳定底座。",
        "",
        "---",
        "",
        "## 成功标准",
        "",
        "> 满足以下所有条件时，可以由 AI 生成 PHASE_GATE.md 提请人工批准进入下一阶段。",
        "",
        "- [ ] 所有基础设施轨道 state = LOCKED",
        "- [ ] 每条 LOCKED 轨道产出 contracts.yaml 和 MODULE_SPEC.md",
        "- [ ] 每条 LOCKED 轨道在 TRACK_LOG.md 留下 PDAE M3 通过记录",
        "",
        "---",
        "",
        "## 本阶段在场的轨道",
        "",
        "| 轨道 ID | 类型 | 初始状态 | 阶段目标状态 | 备注 |",
        "|---------|------|---------|-------------|------|",
        track_rows,
        "",
        "---",
        "",
        "## 关键时间节点（可选）",
        "",
        "| 里程碑 | 目标日期 | 说明 |",
        "|--------|---------|------|",
        "| 基础设施底座冻结 | 待定 | 完成 contracts.yaml、MODULE_SPEC.md 并通过 Phase 0 Gate |",
        "",
        "---",
        "",
        "## 关联文件",
        "",
        "- `prae/track_registry.yaml` — 轨道状态总表",
        "- `prae/phases/phase_00_infra/PHASE_GATE.md` — 本阶段结束时生成",
        "- `prae/PRAE_INIT.md` — 项目初始化文档",
        "",
    ])


def _build_track_note(track: dict, target_phase: str) -> str:
    notes: list[str] = []
    hypothesis = track.get("hypothesis")
    if hypothesis:
        notes.append(f"假设={hypothesis}")
    depends_on = track.get("depends_on") or []
    if depends_on:
        notes.append(f"depends_on={', '.join(depends_on)}")
    if track.get("evidence_summary"):
        notes.append(str(track["evidence_summary"]))
    if target_phase == "phase_03_conclusion":
        notes.append("待 PDAE 路由")
    return "；".join(notes) if notes else "—"


def render_phase_brief(target_phase: str, registry: dict, selected_tracks: list[dict]) -> str:
    today = str(datetime.date.today())
    config = PHASE_BRIEF_CONFIG[target_phase]
    cycle_label = get_cycle_label(registry)
    success_lines = "\n".join(f"- [ ] {item}" for item in config["success"])
    milestone_name, milestone_date, milestone_desc = config["milestone"]

    if selected_tracks:
        track_rows = [
            f"| `{track['id']}` | {track.get('type', 'unknown')} | {track.get('state', 'unknown')} | "
            f"{config['target_state']} | {_build_track_note(track, target_phase)} |"
            for track in selected_tracks
        ]
        track_table = "\n".join(track_rows)
    else:
        track_table = "| `—` | research | — | — | 当前阶段无在场轨道 |"

    return "\n".join([
        f"# Phase {target_phase.replace('phase_', '')} 阶段简报",
        "",
        f"**阶段**: {target_phase}",
        f"**研究轮次**: {cycle_label}",
        f"**创建日期**: {today}",
        "**创建者**: AI（分析者角色）",
        "",
        "---",
        "",
        "## 阶段目标",
        "",
        config["goal"],
        "",
        "---",
        "",
        "## 成功标准",
        "",
        "> 满足以下所有条件时，可以由 AI 生成 PHASE_GATE.md 提请人工批准进入下一阶段。",
        "",
        success_lines,
        "",
        "---",
        "",
        "## 本阶段在场的轨道",
        "",
        "| 轨道 ID | 类型 | 初始状态 | 阶段目标状态 | 备注 |",
        "|---------|------|---------|-------------|------|",
        track_table,
        "",
        "---",
        "",
        "## 关键时间节点（可选）",
        "",
        "| 里程碑 | 目标日期 | 说明 |",
        "|--------|---------|------|",
        f"| {milestone_name} | {milestone_date} | {milestone_desc} |",
        "",
        "---",
        "",
        "## 关联文件",
        "",
        "- `prae/track_registry.yaml` — 轨道状态总表",
        f"- `prae/phases/{target_phase}/PHASE_GATE.md` — 本阶段结束时生成",
        "- `prae/PRAE_INIT.md` — 项目初始化文档",
        "",
    ])


def _relevant_tracks(registry: dict, from_phase_num: int) -> list[dict]:
    if from_phase_num == 0:
        return [t for t in registry.get("tracks", []) if t.get("type") == "infrastructure"]
    return [t for t in registry.get("tracks", []) if t.get("type") == "research"]


def _build_current_state_section(registry: dict) -> str:
    recorded_phase = get_recorded_phase(registry, "unknown")
    lines = [
        "## 1. 当前阶段状态",
        "",
        f"> 来源：`prae/track_registry.yaml`（current_phase: {recorded_phase}）",
        "",
        "| 轨道 ID | 类型 | 当前 state | 备注 |",
        "|---------|------|-----------|------|",
    ]
    for track in registry.get("tracks", []):
        note_parts: list[str] = []
        if track.get("type") == "infrastructure" and track.get("locked_at"):
            note_parts.append(f"locked_at={track['locked_at']}")
        if track.get("type") == "research" and track.get("experiments") is not None:
            note_parts.append(f"experiments={track.get('experiments', 0)}")
        if track.get("evidence_summary"):
            note_parts.append(str(track["evidence_summary"]))
        note = "；".join(note_parts) if note_parts else "—"
        lines.append(
            f"| `{track['id']}` | {track.get('type', 'unknown')} | {track.get('state', 'unknown')} | {note} |"
        )
    return "\n".join(lines)


def _build_checklist_section(from_phase_num: int, gate_conditions: dict[str, bool], required_items: dict[int, list[str]]) -> str:
    lines = [
        "## 2. 门控条件逐项检查",
        "",
    ]
    for item in required_items[from_phase_num]:
        mark = "x" if gate_conditions.get(item, False) else " "
        lines.append(f"- [{mark}] {item}")
    return "\n".join(lines)


def _find_latest_experiment_link(project_dir: Path, current_phase: str, track_id: str) -> str:
    exp_dir = project_dir / "prae" / "phases" / current_phase / "tracks" / track_id / "experiments"
    if not exp_dir.is_dir():
        return ""
    md_files = sorted(
        p.name for p in exp_dir.iterdir() if p.is_file() and p.name.startswith("EXP_") and p.suffix == ".md"
    )
    if not md_files:
        return ""
    latest = md_files[-1]
    return f"；关键实验见 [{latest}](tracks/{track_id}/experiments/{latest})"


def _build_evidence_section(project_dir: Path, registry: dict, from_phase_num: int) -> str:
    current_phase = registry.get("current_phase", "")
    lines = [
        "## 3. 证据摘要",
        "",
        "> 每条关键证据 1-2 句，链接到 EXP_NNN.md 或 TRACK_LOG.md。",
        "",
    ]
    for track in _relevant_tracks(registry, from_phase_num):
        track_id = track["id"]
        summary = track.get("evidence_summary") or f"当前 state={track.get('state', 'unknown')}"
        latest_exp = _find_latest_experiment_link(project_dir, current_phase, track_id)
        lines.append(
            f"- **`{track_id}`**：{summary}。详见 [TRACK_LOG.md](tracks/{track_id}/TRACK_LOG.md){latest_exp}。"
        )
    if len(lines) == 4:
        lines.append("- 暂无可引用轨道证据。")
    return "\n".join(lines)


def _build_risks_section(evaluation: dict, from_phase_num: int, required_items: dict[int, list[str]]) -> str:
    unmet_conditions = [
        item for item in required_items[from_phase_num]
        if not evaluation["gate_conditions"].get(item, False)
    ]
    lines = [
        "## 4. 风险与未决项",
        "",
        "> 可能影响下一阶段的风险或尚未解决的疑问。",
        "",
    ]
    if not unmet_conditions:
        lines.append("- 无已知阻塞风险。")
        return "\n".join(lines)

    for item in unmet_conditions:
        lines.append(f"- `{item}` 未满足，当前不建议推进。")
    return "\n".join(lines)


def _build_recommendation_section(evaluation: dict, from_phase_num: int, required_items: dict[int, list[str]]) -> str:
    gate_passed = all(evaluation["gate_conditions"].values())
    action = "推进" if gate_passed else "暂不推进"
    unmet_count = sum(
        1 for item in required_items[from_phase_num]
        if not evaluation["gate_conditions"].get(item, False)
    )
    if gate_passed:
        reason = "所有阶段门控条件已满足，PHASE_GATE.md 已完成留痕，可提交人工批准。"
    else:
        reason = f"仍有 {unmet_count} 项门控条件未满足；请先解决第 2 节和第 4 节中的阻塞项。"
    return "\n".join([
        "## 5. 建议",
        "",
        f"**推荐动作**: {action}",
        "",
        f"**理由**: {reason}",
    ])


PHASE_GATE_APPROVAL_DEFAULTS = {
    "APPROVED": "pending",
    "APPROVER": "",
    "APPROVED_AT": "",
    "COMMENT": "",
}
PHASE_GATE_APPROVAL_FIELDS = tuple(PHASE_GATE_APPROVAL_DEFAULTS.keys())


def _single_line(value: str) -> str:
    return str(value).splitlines()[0].strip() if str(value).splitlines() else ""


def render_approval_section(fields: dict[str, str]) -> str:
    return "\n".join([
        "## 6. 待人工批准",
        "",
        f"APPROVED: {_single_line(fields.get('APPROVED', PHASE_GATE_APPROVAL_DEFAULTS['APPROVED'])) or PHASE_GATE_APPROVAL_DEFAULTS['APPROVED']}",
        f"APPROVER: {_single_line(fields.get('APPROVER', ''))}",
        f"APPROVED_AT: {_single_line(fields.get('APPROVED_AT', ''))}",
        f"COMMENT: {_single_line(fields.get('COMMENT', ''))}",
    ])


def default_approval_section() -> str:
    return render_approval_section(PHASE_GATE_APPROVAL_DEFAULTS)


def extract_approval_section(existing_content: str) -> str:
    match = re.search(r"## 6\. 待人工批准\n(.*)\Z", existing_content, re.DOTALL)
    if not match:
        return default_approval_section()

    body = match.group(1).strip("\n")
    fields = dict(PHASE_GATE_APPROVAL_DEFAULTS)
    for field in PHASE_GATE_APPROVAL_FIELDS:
        field_match = re.search(rf"^{field}:[ \t]*(.*)$", body, re.MULTILINE)
        if field_match:
            fields[field] = _single_line(field_match.group(1))
    return render_approval_section(fields)


def render_phase_gate_content(
    project_dir: Path,
    registry: dict,
    *,
    current_phase: str,
    target_phase: str,
    from_phase_num: int,
    to_phase_num: int,
    evaluation: dict,
    required_items: dict[int, list[str]],
    approval_section: str | None = None,
) -> str:
    sections = [
        f"# Phase {from_phase_num} → Phase {to_phase_num} 门控分析",
        "",
        f"**研究轮次**: {get_cycle_label(registry)}",
        f"**生成日期**: {datetime.date.today()}",
        "**生成者**: AI（分析者角色）",
        f"**目标阶段**: {target_phase}",
        "",
        "---",
        "",
        _build_current_state_section(registry),
        "",
        "---",
        "",
        _build_checklist_section(from_phase_num, evaluation["gate_conditions"], required_items),
        "",
        "---",
        "",
        _build_evidence_section(project_dir, registry, from_phase_num),
        "",
        "---",
        "",
        _build_risks_section(evaluation, from_phase_num, required_items),
        "",
        "---",
        "",
        _build_recommendation_section(evaluation, from_phase_num, required_items),
        "",
        "---",
        "",
        approval_section or default_approval_section(),
        "",
    ]
    return "\n".join(sections)
