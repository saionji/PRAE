"""Shared artifact rendering / mutation helpers for PRAE tools."""
from __future__ import annotations

import datetime
import re
from pathlib import Path


DECISION_LOG_INTRO = "> 记录状态变更：何时变、谁建议、谁批准。格式：日期 + 旧状态 → 新状态 + 原因。"
DECISION_LOG_HEADER = "| 日期 | 变更 | 建议者 | 批准者 | 原因 |"
DECISION_LOG_SEPARATOR = "|------|------|--------|--------|------|"


def today_str() -> str:
    return str(datetime.date.today())


def render_depends_lines(depends_on: list[str] | None) -> str:
    items = depends_on or []
    return "\n".join(f"- `{dep}`" for dep in items) if items else "- 无"


def render_research_track_log(
    track: dict,
    current_phase: str,
    *,
    cycle_label: str,
    created_reason: str,
) -> str:
    today = today_str()
    depends_lines = render_depends_lines(track.get("depends_on"))
    hypothesis = track.get("hypothesis") or "待补充"
    return "\n".join([
        f"# 轨道日志：{track['id']}",
        "",
        f"**轨道 ID**: `{track['id']}`",
        "**类型**: research",
        f"**当前阶段**: {current_phase}",
        f"**研究轮次**: {cycle_label}",
        f"**创建日期**: {today}",
        "",
        "---",
        "",
        "## Hypothesis（仅研究轨道填写）",
        "",
        hypothesis,
        "",
        "**失败判据**（什么情况下 KILL 这条轨道）:",
        "待补充：出现明确证伪信号、收益风险比不达标或无法复现时终止。",
        "",
        "---",
        "",
        "## State",
        "",
        f"**当前状态**: {track.get('state', 'EXPLORING')}",
        "**依赖的轨道**:",
        depends_lines,
        "",
        "---",
        "",
        "## Experiments",
        "",
        "| EXP ID | 日期 | 目的 | 结论 | 链接 |",
        "|--------|------|------|------|------|",
        "| — | — | 尚无实验记录 | — | — |",
        "",
        "---",
        "",
        "## Evidence Summary",
        "",
        "> 每次实验后追加一段，格式：日期 + 关键发现 + 对假设的影响。不删历史。",
        "",
        "- 暂无实验记录。",
        "",
        "---",
        "",
        "## Decision Log",
        "",
        DECISION_LOG_INTRO,
        "",
        DECISION_LOG_HEADER,
        DECISION_LOG_SEPARATOR,
        f"| {today} | 创建（{track.get('state', 'EXPLORING')}) | AI | — | {created_reason} |",
        "",
    ])


def render_infra_track_log(
    track: dict,
    current_phase: str,
    *,
    cycle_label: str,
    created_reason: str,
    description: str | None = None,
    lock_criteria: str | None = None,
) -> str:
    today = today_str()
    description = description or track.get("description") or track.get("goal") or "待补充"
    if lock_criteria is None:
        target_lines = [description]
    else:
        target_lines = [
            f"- 基础设施目标：{description}",
            f"- LOCKED 判断标准：{lock_criteria}",
        ]
    return "\n".join([
        f"# 轨道日志：{track['id']}",
        "",
        f"**轨道 ID**: `{track['id']}`",
        "**类型**: infrastructure",
        f"**当前阶段**: {current_phase}",
        f"**研究轮次**: {cycle_label}",
        f"**创建日期**: {today}",
        "",
        "---",
        "",
        "## 选型目标（仅基础设施轨道填写）",
        "",
        *target_lines,
        "",
        "---",
        "",
        "## State",
        "",
        f"**当前状态**: {track.get('state', 'EXPLORING')}",
        "**依赖的轨道**:",
        "- 无",
        "",
        "---",
        "",
        "## Experiments",
        "",
        "| EXP ID | 日期 | 目的 | 结论 | 链接 |",
        "|--------|------|------|------|------|",
        "| — | — | 尚无选型或验证记录 | — | — |",
        "",
        "---",
        "",
        "## Evidence Summary",
        "",
        "> 每次选型验证或实现推进后追加一段，格式：日期 + 关键发现 + 对 LOCKED 决策的影响。",
        "",
        "- 暂无选型记录。",
        "",
        "---",
        "",
        "## Decision Log",
        "",
        DECISION_LOG_INTRO,
        "",
        DECISION_LOG_HEADER,
        DECISION_LOG_SEPARATOR,
        f"| {today} | 创建（{track.get('state', 'EXPLORING')}) | AI | — | {created_reason} |",
        "",
    ])


def ensure_decision_log_section(content: str) -> str:
    if "## Decision Log" not in content:
        section = "\n".join([
            "## Decision Log",
            "",
            DECISION_LOG_INTRO,
            "",
            DECISION_LOG_HEADER,
            DECISION_LOG_SEPARATOR,
            "",
        ])
        return content.rstrip() + "\n\n---\n\n" + section

    section_start = content.index("## Decision Log")
    next_sep = content.find("\n---", section_start)
    if next_sep == -1:
        next_sep = len(content)

    section = content[section_start:next_sep]
    if DECISION_LOG_INTRO not in section:
        section = section.rstrip() + "\n\n" + DECISION_LOG_INTRO
    if DECISION_LOG_HEADER not in section:
        section = section.rstrip() + "\n\n" + DECISION_LOG_HEADER + "\n" + DECISION_LOG_SEPARATOR
    return content[:section_start] + section + content[next_sep:]


def upsert_decision_log_row(
    content: str,
    row: str,
    *,
    row_pattern: re.Pattern[str] | None = None,
) -> str:
    content = ensure_decision_log_section(content)
    section_start = content.index("## Decision Log")
    next_sep = content.find("\n---", section_start)
    if next_sep == -1:
        next_sep = len(content)

    section = content[section_start:next_sep]
    if row_pattern and row_pattern.search(section):
        section = row_pattern.sub(row, section, count=1)
    else:
        section = section.rstrip() + "\n" + row + "\n"
    return content[:section_start] + section + content[next_sep:]


def render_exp_markdown(template: str, exp_num: str, track_id: str, title: str) -> str:
    content = template
    replacements = {
        "{{NNN}}": exp_num,
        "{{实验标题}}": title,
        "{{track_id}}": track_id,
        "{{YYYY-MM-DD}}": today_str(),
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    return re.sub(
        r"^\*\*状态\*\*:.*$",
        "**状态**: 进行中",
        content,
        count=1,
        flags=re.MULTILINE,
    )


def render_exp_python(exp_id: str, title: str, track_id: str, exp_md_path: Path) -> str:
    return "\n".join([
        '"""',
        f"{exp_id}: {title}",
        f"轨道: {track_id}",
        f"记录: {exp_md_path.as_posix()}",
        "",
        "约束:",
        "- 只使用 contracts.yaml 声明的公开接口",
        "- 此文件不能被其他代码 import",
        "- 修改逻辑时创建新的 EXP_NNN.py，不在本文件上改",
        "- 先满足 EXP_NNN.md 的 Preflight Check，再考虑额外抽象",
        '"""',
        "",
        "def main():",
        f"    # TODO 1: 先完成 {exp_id}.md 的 Method / Preflight Check / Expected Signal",
        "    # TODO 2: 先实现最小可运行路径，产出 Preflight 里承诺的输出",
        "    # TODO 3: 跑通后再决定是否需要更复杂的实验逻辑",
        "    pass",
        "",
        'if __name__ == "__main__":',
        "    main()",
        "",
    ])
