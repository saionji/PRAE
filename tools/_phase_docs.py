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
        "goal": "Complete the first round of experiments and evidence accumulation for research tracks, and identify ACTIVE routes worth entering the validation period.",
        "success": [
            "Each research track present completes at least 1 experiment and records it to TRACK_LOG.md",
            "At least 1 research track shows a positive signal and enters ACTIVE",
            "All tracks still EXPLORING have a clear keep-or-drop recommendation",
        ],
        "target_state": "ACTIVE / KILLED / MERGED",
        "milestone": ("First experiment round completed", "TBD", "Complete the first round of EXP records and consolidate the evidence summary"),
    },
    "phase_02_validation": {
        "goal": "Rigorously validate the ACTIVE tracks that entered the validation period, converge to a clear terminal state, and select GRADUATED candidates.",
        "success": [
            "Each track present completes rigorous validation experiments and fills in the evidence summary",
            "All tracks present have a clear terminal-state recommendation (GRADUATED / KILLED / MERGED)",
            "At least 1 track meets the GRADUATED conditions for entering Phase 3",
        ],
        "target_state": "GRADUATED / KILLED / MERGED",
        "milestone": ("Validation conclusion converged", "TBD", "Complete the terminal-state recommendation and prepare PHASE_GATE.md"),
    },
    "phase_03_conclusion": {
        "goal": "Summarize the project's final conclusion, register all GRADUATED tracks for pending PDAE routing, and prepare to wrap up the project.",
        "success": [
            "All GRADUATED tracks are registered for pending PDAE routing in PHASE_BRIEF.md",
            "The project-level CONCLUSION.md completes the final conclusion writeup",
            "All remaining risks, open items, and follow-up engineering actions are recorded",
        ],
        "target_state": "Pending PDAE routing",
        "milestone": ("Project conclusion closed out", "TBD", "Generate CONCLUSION.md and arrange PDAE routing"),
    },
}


def render_phase0_brief(registry: dict, infra_tracks: list[dict]) -> str:
    today = str(datetime.date.today())
    cycle_label = get_cycle_label(registry)

    if infra_tracks:
        track_rows = "\n".join(
            f"| `{track['id']}` | infrastructure | EXPLORING | LOCKED | "
            f"{track.get('description', 'To be filled in')}; LOCKED criteria: {track.get('lock_criteria', 'To be filled in')} |"
            for track in infra_tracks
        )
    else:
        track_rows = "| `—` | infrastructure | — | — | No infrastructure tracks at present |"

    return "\n".join([
        "# Phase 00_infra Brief",
        "",
        "**Phase**: phase_00_infra",
        f"**Research Cycle**: {cycle_label}",
        f"**Created**: {today}",
        "**Creator**: AI (Analyst role)",
        "",
        "---",
        "",
        "## Phase Goal",
        "",
        "Complete the selection, contract freeze, and PDAE M3 implementation for all infrastructure tracks, providing a stable foundation for the research phase.",
        "",
        "---",
        "",
        "## Success Criteria",
        "",
        "> When all of the following conditions are met, AI may generate PHASE_GATE.md to request human approval to advance to the next phase.",
        "",
        "- [ ] All infrastructure tracks state = LOCKED",
        "- [ ] Each LOCKED track produces contracts.yaml and MODULE_SPEC.md",
        "- [ ] Each LOCKED track leaves a PDAE M3 pass record in TRACK_LOG.md",
        "",
        "---",
        "",
        "## Tracks Present in This Phase",
        "",
        "| Track ID | Type | Initial State | Phase Target State | Notes |",
        "|---------|------|---------|-------------|------|",
        track_rows,
        "",
        "---",
        "",
        "## Key Time Milestones (Optional)",
        "",
        "| Milestone | Target Date | Description |",
        "|--------|---------|------|",
        "| Infrastructure foundation frozen | TBD | Complete contracts.yaml, MODULE_SPEC.md and pass the Phase 0 Gate |",
        "",
        "---",
        "",
        "## Related Files",
        "",
        "- `prae/track_registry.yaml` — track state master table",
        "- `prae/phases/phase_00_infra/PHASE_GATE.md` — generated at the end of this phase",
        "- `prae/PRAE_INIT.md` — project initialization document",
        "",
    ])


def _build_track_note(track: dict, target_phase: str) -> str:
    notes: list[str] = []
    hypothesis = track.get("hypothesis")
    if hypothesis:
        notes.append(f"hypothesis={hypothesis}")
    depends_on = track.get("depends_on") or []
    if depends_on:
        notes.append(f"depends_on={', '.join(depends_on)}")
    if track.get("evidence_summary"):
        notes.append(str(track["evidence_summary"]))
    if target_phase == "phase_03_conclusion":
        notes.append("Pending PDAE routing")
    return "; ".join(notes) if notes else "—"


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
        track_table = "| `—` | research | — | — | No tracks present in this phase |"

    return "\n".join([
        f"# Phase {target_phase.replace('phase_', '')} Brief",
        "",
        f"**Phase**: {target_phase}",
        f"**Research Cycle**: {cycle_label}",
        f"**Created**: {today}",
        "**Creator**: AI (Analyst role)",
        "",
        "---",
        "",
        "## Phase Goal",
        "",
        config["goal"],
        "",
        "---",
        "",
        "## Success Criteria",
        "",
        "> When all of the following conditions are met, AI may generate PHASE_GATE.md to request human approval to advance to the next phase.",
        "",
        success_lines,
        "",
        "---",
        "",
        "## Tracks Present in This Phase",
        "",
        "| Track ID | Type | Initial State | Phase Target State | Notes |",
        "|---------|------|---------|-------------|------|",
        track_table,
        "",
        "---",
        "",
        "## Key Time Milestones (Optional)",
        "",
        "| Milestone | Target Date | Description |",
        "|--------|---------|------|",
        f"| {milestone_name} | {milestone_date} | {milestone_desc} |",
        "",
        "---",
        "",
        "## Related Files",
        "",
        "- `prae/track_registry.yaml` — track state master table",
        f"- `prae/phases/{target_phase}/PHASE_GATE.md` — generated at the end of this phase",
        "- `prae/PRAE_INIT.md` — project initialization document",
        "",
    ])


def _relevant_tracks(registry: dict, from_phase_num: int) -> list[dict]:
    if from_phase_num == 0:
        return [t for t in registry.get("tracks", []) if t.get("type") == "infrastructure"]
    return [t for t in registry.get("tracks", []) if t.get("type") == "research"]


def _build_current_state_section(registry: dict) -> str:
    recorded_phase = get_recorded_phase(registry, "unknown")
    lines = [
        "## 1. Current Phase State",
        "",
        f"> Source: `prae/track_registry.yaml` (current_phase: {recorded_phase})",
        "",
        "| Track ID | Type | Current state | Notes |",
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
        note = "; ".join(note_parts) if note_parts else "—"
        lines.append(
            f"| `{track['id']}` | {track.get('type', 'unknown')} | {track.get('state', 'unknown')} | {note} |"
        )
    return "\n".join(lines)


def _build_checklist_section(from_phase_num: int, gate_conditions: dict[str, bool], required_items: dict[int, list[str]]) -> str:
    lines = [
        "## 2. Gate Conditions — Item-by-Item Check",
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
    return f"; key experiment see [{latest}](tracks/{track_id}/experiments/{latest})"


def _build_evidence_section(project_dir: Path, registry: dict, from_phase_num: int) -> str:
    current_phase = registry.get("current_phase", "")
    lines = [
        "## 3. Evidence Summary",
        "",
        "> 1-2 sentences per key piece of evidence, linked to EXP_NNN.md or TRACK_LOG.md.",
        "",
    ]
    for track in _relevant_tracks(registry, from_phase_num):
        track_id = track["id"]
        summary = track.get("evidence_summary") or f"current state={track.get('state', 'unknown')}"
        latest_exp = _find_latest_experiment_link(project_dir, current_phase, track_id)
        lines.append(
            f"- **`{track_id}`**: {summary}. See [TRACK_LOG.md](tracks/{track_id}/TRACK_LOG.md){latest_exp}."
        )
    if len(lines) == 4:
        lines.append("- No referenceable track evidence yet.")
    return "\n".join(lines)


def _build_risks_section(evaluation: dict, from_phase_num: int, required_items: dict[int, list[str]]) -> str:
    unmet_conditions = [
        item for item in required_items[from_phase_num]
        if not evaluation["gate_conditions"].get(item, False)
    ]
    lines = [
        "## 4. Risks and Open Items",
        "",
        "> Risks that may affect the next phase, or questions not yet resolved.",
        "",
    ]
    if not unmet_conditions:
        lines.append("- No known blocking risks.")
        return "\n".join(lines)

    for item in unmet_conditions:
        lines.append(f"- `{item}` not met; advancing is not recommended at this time.")
    return "\n".join(lines)


def _build_recommendation_section(evaluation: dict, from_phase_num: int, required_items: dict[int, list[str]]) -> str:
    gate_passed = all(evaluation["gate_conditions"].values())
    action = "Advance" if gate_passed else "Do not advance yet"
    unmet_count = sum(
        1 for item in required_items[from_phase_num]
        if not evaluation["gate_conditions"].get(item, False)
    )
    if gate_passed:
        reason = "All phase gate conditions are met and PHASE_GATE.md is fully recorded; ready to submit for human approval."
    else:
        reason = f"{unmet_count} gate conditions still not met; please resolve the blocking items in Section 2 and Section 4 first."
    return "\n".join([
        "## 5. Recommendation",
        "",
        f"**Recommended Action**: {action}",
        "",
        f"**Rationale**: {reason}",
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
        "## 6. Pending Human Approval",
        "",
        f"APPROVED: {_single_line(fields.get('APPROVED', PHASE_GATE_APPROVAL_DEFAULTS['APPROVED'])) or PHASE_GATE_APPROVAL_DEFAULTS['APPROVED']}",
        f"APPROVER: {_single_line(fields.get('APPROVER', ''))}",
        f"APPROVED_AT: {_single_line(fields.get('APPROVED_AT', ''))}",
        f"COMMENT: {_single_line(fields.get('COMMENT', ''))}",
    ])


def default_approval_section() -> str:
    return render_approval_section(PHASE_GATE_APPROVAL_DEFAULTS)


def extract_approval_section(existing_content: str) -> str:
    match = re.search(r"## 6\. Pending Human Approval\n(.*)\Z", existing_content, re.DOTALL)
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
        f"# Phase {from_phase_num} → Phase {to_phase_num} Gate Analysis",
        "",
        f"**Research Cycle**: {get_cycle_label(registry)}",
        f"**Generated**: {datetime.date.today()}",
        "**Generated by**: AI (Analyst role)",
        f"**Target Phase**: {target_phase}",
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
