"""Shared conclusion document helpers for PRAE tools."""
from __future__ import annotations

import re


VALID_DECISIONS = ("ARCHIVED", "GRADUATED_TO_PDAE", "CONTINUE")
FINAL_DECISION_DEFAULTS = {
    "APPROVED": "pending",
    "DECISION": "",
    "APPROVER": "",
    "APPROVED_AT": "",
    "COMMENT": "",
}
FINAL_DECISION_FIELDS = tuple(FINAL_DECISION_DEFAULTS.keys())
CONCLUSION_SECTIONS = [
    "## Project Conclusion",
    "## Disposition of Each Track",
    "## PDAE Project Links for Graduated Tracks",
    "## Unresolved Issues",
    "## Final Decision",
]


def _single_line(value: str) -> str:
    return str(value).splitlines()[0].strip() if str(value).splitlines() else ""


def _normalize_decision_value(value: str) -> str:
    candidate = _single_line(value)
    return candidate if candidate in VALID_DECISIONS else ""


def extract_final_decision_body(content: str) -> str:
    match = re.search(r"## Final Decision\n(.*)\Z", content, re.DOTALL)
    return match.group(1).strip("\n") if match else ""


def has_structured_final_decision_fields(final_section: str) -> bool:
    return all(
        re.search(rf"^{field}:[ \t]*.*$", final_section, re.MULTILINE) is not None
        for field in FINAL_DECISION_FIELDS
    )


def parse_final_decision_fields(final_section: str) -> dict[str, str]:
    fields = dict(FINAL_DECISION_DEFAULTS)
    if has_structured_final_decision_fields(final_section):
        for field in FINAL_DECISION_FIELDS:
            match = re.search(rf"^{field}:[ \t]*(.*)$", final_section, re.MULTILINE)
            fields[field] = _single_line(match.group(1)) if match else fields[field]
        fields["DECISION"] = _normalize_decision_value(fields["DECISION"])
        return fields

    approved_match = re.search(r"\*\*APPROVED\*\*:\s*(yes|no|pending)", final_section)
    if approved_match:
        fields["APPROVED"] = approved_match.group(1)

    decision_match = re.search(r"```\s*(.*?)\s*```", final_section, re.DOTALL)
    if decision_match:
        fields["DECISION"] = _normalize_decision_value(decision_match.group(1))
    else:
        for decision in VALID_DECISIONS:
            if re.search(rf"\b{re.escape(decision)}\b", final_section):
                fields["DECISION"] = decision
                break

    approver_match = re.search(r"\*\*Approver\*\*:\s*(.*)", final_section)
    if approver_match:
        fields["APPROVER"] = _single_line(approver_match.group(1))

    date_match = re.search(r"\*\*Date\*\*:\s*(.*)", final_section)
    if date_match:
        fields["APPROVED_AT"] = _single_line(date_match.group(1))

    return fields


def render_final_decision_section(fields: dict[str, str]) -> str:
    return "\n".join([
        "## Final Decision",
        "",
        "> DECISION allowed values: ARCHIVED / GRADUATED_TO_PDAE / CONTINUE",
        "",
        f"APPROVED: {_single_line(fields.get('APPROVED', FINAL_DECISION_DEFAULTS['APPROVED'])) or FINAL_DECISION_DEFAULTS['APPROVED']}",
        f"DECISION: {_single_line(fields.get('DECISION', ''))}",
        f"APPROVER: {_single_line(fields.get('APPROVER', ''))}",
        f"APPROVED_AT: {_single_line(fields.get('APPROVED_AT', ''))}",
        f"COMMENT: {_single_line(fields.get('COMMENT', ''))}",
    ])


def default_final_decision_section() -> str:
    return render_final_decision_section(FINAL_DECISION_DEFAULTS)


def extract_final_decision_section(existing_content: str) -> str:
    body = extract_final_decision_body(existing_content)
    if not body:
        return default_final_decision_section()
    if has_structured_final_decision_fields(body):
        return "## Final Decision\n" + body
    return render_final_decision_section(parse_final_decision_fields(body))


def render_conclusion_document(
    *,
    project_name: str,
    cycle_label: str,
    project_conclusion: str,
    track_outcomes_rows: str,
    pdae_links_rows: str,
    unresolved_issues: str,
    final_decision_section: str,
) -> str:
    return "\n".join([
        f"# CONCLUSION — {project_name}",
        "",
        f"**Research Cycle**: {cycle_label}",
        "",
        "---",
        "",
        "## Project Conclusion",
        "",
        project_conclusion,
        "",
        "---",
        "",
        "## Disposition of Each Track",
        "",
        "| Track ID | Final State | Conclusion Summary | Notes |",
        "|---------|---------|---------|------|",
        track_outcomes_rows,
        "",
        "---",
        "",
        "## PDAE Project Links for Graduated Tracks",
        "",
        "| Track ID | PDAE Project Path |",
        "|---------|----------------|",
        pdae_links_rows,
        "",
        "---",
        "",
        "## Unresolved Issues",
        "",
        unresolved_issues,
        "",
        "---",
        "",
        final_decision_section,
        "",
    ])
