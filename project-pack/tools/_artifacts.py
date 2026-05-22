"""Shared artifact rendering / mutation helpers for PRAE tools."""
from __future__ import annotations

import datetime
import re
from pathlib import Path


DECISION_LOG_INTRO = "> Record state changes: when it changed, who recommended it, who approved it. Format: date + old state → new state + reason."
DECISION_LOG_HEADER = "| Date | Change | Recommended by | Approved by | Reason |"
DECISION_LOG_SEPARATOR = "|------|------|--------|--------|------|"


def today_str() -> str:
    return str(datetime.date.today())


def render_depends_lines(depends_on: list[str] | None) -> str:
    items = depends_on or []
    return "\n".join(f"- `{dep}`" for dep in items) if items else "- None"


def render_research_track_log(
    track: dict,
    current_phase: str,
    *,
    cycle_label: str,
    created_reason: str,
) -> str:
    today = today_str()
    depends_lines = render_depends_lines(track.get("depends_on"))
    hypothesis = track.get("hypothesis") or "To be filled in"
    return "\n".join([
        f"# Track Log: {track['id']}",
        "",
        f"**Track ID**: `{track['id']}`",
        "**Type**: research",
        f"**Current Phase**: {current_phase}",
        f"**Research Cycle**: {cycle_label}",
        f"**Created**: {today}",
        "",
        "---",
        "",
        "## Hypothesis (research tracks only)",
        "",
        hypothesis,
        "",
        "**Failure Criterion** (under what conditions to KILL this track):",
        "To be filled in: terminate when a clear falsifying signal appears, the reward-to-risk ratio is unacceptable, or results cannot be reproduced.",
        "",
        "---",
        "",
        "## State",
        "",
        f"**Current State**: {track.get('state', 'EXPLORING')}",
        "**Depends On**:",
        depends_lines,
        "",
        "---",
        "",
        "## Experiments",
        "",
        "| EXP ID | Date | Purpose | Conclusion | Link |",
        "|--------|------|------|------|------|",
        "| — | — | No experiment records yet | — | — |",
        "",
        "---",
        "",
        "## Evidence Summary",
        "",
        "> Append a paragraph after each experiment, format: date + key findings + impact on the hypothesis. Do not delete history.",
        "",
        "- No experiment records yet.",
        "",
        "---",
        "",
        "## Decision Log",
        "",
        DECISION_LOG_INTRO,
        "",
        DECISION_LOG_HEADER,
        DECISION_LOG_SEPARATOR,
        f"| {today} | Created ({track.get('state', 'EXPLORING')}) | AI | — | {created_reason} |",
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
    description = description or track.get("description") or track.get("goal") or "To be filled in"
    if lock_criteria is None:
        target_lines = [description]
    else:
        target_lines = [
            f"- Infrastructure goal: {description}",
            f"- LOCKED criteria: {lock_criteria}",
        ]
    return "\n".join([
        f"# Track Log: {track['id']}",
        "",
        f"**Track ID**: `{track['id']}`",
        "**Type**: infrastructure",
        f"**Current Phase**: {current_phase}",
        f"**Research Cycle**: {cycle_label}",
        f"**Created**: {today}",
        "",
        "---",
        "",
        "## Selection Goal (infrastructure tracks only)",
        "",
        *target_lines,
        "",
        "---",
        "",
        "## State",
        "",
        f"**Current State**: {track.get('state', 'EXPLORING')}",
        "**Depends On**:",
        "- None",
        "",
        "---",
        "",
        "## Experiments",
        "",
        "| EXP ID | Date | Purpose | Conclusion | Link |",
        "|--------|------|------|------|------|",
        "| — | — | No selection or validation records yet | — | — |",
        "",
        "---",
        "",
        "## Evidence Summary",
        "",
        "> Append a paragraph after each selection validation or implementation milestone, format: date + key findings + impact on the LOCKED decision.",
        "",
        "- No selection records yet.",
        "",
        "---",
        "",
        "## Decision Log",
        "",
        DECISION_LOG_INTRO,
        "",
        DECISION_LOG_HEADER,
        DECISION_LOG_SEPARATOR,
        f"| {today} | Created ({track.get('state', 'EXPLORING')}) | AI | — | {created_reason} |",
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
        "{{experiment_title}}": title,
        "{{track_id}}": track_id,
        "{{YYYY-MM-DD}}": today_str(),
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    return re.sub(
        r"^\*\*State\*\*:.*$",
        "**State**: In Progress",
        content,
        count=1,
        flags=re.MULTILINE,
    )


def render_exp_python(exp_id: str, title: str, track_id: str, exp_md_path: Path) -> str:
    return "\n".join([
        '"""',
        f"{exp_id}: {title}",
        f"Track: {track_id}",
        f"Record: {exp_md_path.as_posix()}",
        "",
        "Constraints:",
        "- Only use the public interfaces declared in contracts.yaml",
        "- This file must not be imported by other code",
        "- When changing logic, create a new EXP_NNN.py; do not edit this file",
        "- First satisfy the Preflight Check in EXP_NNN.md, then consider additional abstraction",
        '"""',
        "",
        "def main():",
        f"    # TODO 1: First complete the Method / Preflight Check / Expected Signal in {exp_id}.md",
        "    # TODO 2: First implement the minimal runnable path, producing the output promised in Preflight",
        "    # TODO 3: Once it runs end-to-end, decide whether more complex experiment logic is needed",
        "    pass",
        "",
        'if __name__ == "__main__":',
        "    main()",
        "",
    ])
