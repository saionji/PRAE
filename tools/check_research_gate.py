#!/usr/bin/env python3
"""
check_research_gate.py — verify the five Research Gate rules for a research track

Exit codes:
  0  all rules passed
  1  one of rules 1-5 violated
  2  track does not exist or files missing

Usage:
  python3 tools/check_research_gate.py --track-id <id> --project-dir <path>
"""
from __future__ import annotations
import argparse
import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _gate_utils import gate_payload, summarize_violations
from _registry import (
    get_cycle_label,
    get_current_phase,
    load_registry as _shared_load_registry,
    require_track,
)
from check_contracts import run_check
from _output import check_item

SMOKE_TIMEOUT_SECONDS = 30
EXP_REQUIRED_SECTIONS = [
    "## Goal",
    "## Method",
    "## Preflight Check",
    "## Expected Signal",
    "## Result",
    "## Conclusion",
]
PREFLIGHT_REQUIRED_MARKERS = [
    "Minimal Smoke Check",
    "Output Contract",
]


class ResearchGateError(RuntimeError):
    """Research Gate configuration or input error."""


def find_current_phase(project_dir: str, registry: dict) -> str:
    return get_current_phase(registry)


def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=ResearchGateError)

def build_context(project_dir: str, track_id: str, current_phase: str) -> dict:
    exp_md_dir = Path(project_dir) / "prae" / "phases" / current_phase / "tracks" / track_id / "experiments"
    md_files = sorted(
        f.name for f in exp_md_dir.iterdir()
        if exp_md_dir.is_dir() and f.is_file() and f.name.startswith("EXP_") and f.suffix == ".md"
    ) if exp_md_dir.is_dir() else []

    latest_md_name = md_files[-1] if md_files else None
    latest_exp_id = Path(latest_md_name).stem if latest_md_name else ""
    latest_md_path = exp_md_dir / latest_md_name if latest_md_name else None
    latest_py_path = Path(project_dir) / "src" / "tracks" / track_id / "experiments" / f"{latest_exp_id}.py" if latest_exp_id else None

    return {
        "project_dir": project_dir,
        "track_id": track_id,
        "current_phase": current_phase,
        "exp_md_dir": exp_md_dir,
        "md_files": md_files,
        "latest_exp_id": latest_exp_id,
        "latest_md_path": latest_md_path,
        "latest_py_path": latest_py_path,
    }


def _preview_output(stdout: str, stderr: str, limit: int = 120) -> str:
    chunks = [part.strip() for part in (stdout, stderr) if part.strip()]
    if not chunks:
        return ""
    text = " | ".join(" ".join(chunk.split()) for chunk in chunks)
    return text if len(text) <= limit else text[: limit - 3] + "..."

def rule1_track_log(project_dir: str, track_id: str, current_phase: str, context: dict, cycle_label: str) -> dict:
    """Rule 1: TRACK_LOG.md has a record of this experiment (at least one complete entry)."""
    log_path = os.path.join(project_dir, "prae", "phases", current_phase,
                             "tracks", track_id, "TRACK_LOG.md")
    if not os.path.exists(log_path):
        return check_item("Rule 1: TRACK_LOG.md exists", False, log_path)

    with open(log_path, encoding="utf-8") as f:
        content = f.read()

    expected_cycle_line = f"**Research Cycle**: {cycle_label}"
    if expected_cycle_line not in content:
        return check_item(
            "Rule 1: TRACK_LOG.md research cycle matches",
            False,
            f"missing or incorrect, expected {expected_cycle_line}",
        )

    # Check that the Experiments table has data rows (not just the header)
    exp_section = re.search(r"## Experiments\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    has_data_row = False
    if exp_section:
        lines = exp_section.group(1).strip().splitlines()
        # Data rows: lines containing | EXP_
        data_rows = [l for l in lines if "EXP_" in l and l.strip().startswith("|")]
        has_data_row = len(data_rows) >= 1

    if not has_data_row:
        return check_item("Rule 1: TRACK_LOG.md has a complete experiment entry", False,
                          "no data rows in the Experiments table (or no line containing EXP_ found)")

    latest_exp_id = context.get("latest_exp_id", "")
    if latest_exp_id and latest_exp_id not in content:
        return check_item("Rule 1: TRACK_LOG.md records the latest experiment", False,
                          f"latest experiment {latest_exp_id} not found in TRACK_LOG.md")

    detail = (
        f"research cycle={cycle_label}; latest experiment={latest_exp_id}"
        if latest_exp_id else f"research cycle={cycle_label}; no EXP_NNN.md found yet, TRACK_LOG line verified"
    )
    return check_item("Rule 1: TRACK_LOG.md has a complete experiment entry", True, detail)


def rule2_smoke_test(project_dir: str, track_id: str, context: dict) -> dict:
    """Rule 2: at least one EXP_NNN.py exists under experiments/ and the most recent script runs successfully."""
    exp_code_dir = os.path.join(project_dir, "src", "tracks", track_id, "experiments")
    if not os.path.isdir(exp_code_dir):
        return check_item("Rule 2: experiments/ directory exists", False, exp_code_dir)

    py_files = [f for f in os.listdir(exp_code_dir) if f.startswith("EXP_") and f.endswith(".py")]
    has_exp_py = len(py_files) >= 1
    if not has_exp_py:
        return check_item("Rule 2: experiments/ has EXP_NNN.py", False,
                          f"no EXP_*.py files in src/tracks/{track_id}/experiments/")

    latest_exp_id = context.get("latest_exp_id", "")
    if latest_exp_id:
        latest_py = f"{latest_exp_id}.py"
        script_path = os.path.join(exp_code_dir, latest_py)
        if not os.path.exists(script_path):
            return check_item("Rule 2: the latest experiment has a corresponding EXP_NNN.py", False,
                              f"{latest_exp_id}.md exists, but the corresponding script {latest_py} is missing")
    else:
        latest_py = sorted(py_files)[-1]
        script_path = os.path.join(exp_code_dir, latest_py)

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = project_dir if not existing_pythonpath else project_dir + os.pathsep + existing_pythonpath

    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=SMOKE_TIMEOUT_SECONDS,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return check_item("Rule 2: the most recent experiment script runs", False,
                          f"{latest_py} timed out (>{SMOKE_TIMEOUT_SECONDS}s)")

    preview = _preview_output(proc.stdout, proc.stderr)
    detail = f"{latest_py} exit={proc.returncode}"
    if preview:
        detail += f"; output={preview}"
    return check_item("Rule 2: the most recent experiment script runs", proc.returncode == 0, detail)


def rule3_params_recorded(project_dir: str, track_id: str, current_phase: str) -> dict:
    """Rule 3: the latest EXP_NNN.md is structurally complete and defines the minimal check and reproduction parameters first."""
    exp_md_dir = os.path.join(project_dir, "prae", "phases", current_phase,
                               "tracks", track_id, "experiments")
    if not os.path.isdir(exp_md_dir):
        return check_item("Rule 3: experiments/ record directory exists", False, exp_md_dir)

    md_files = sorted([f for f in os.listdir(exp_md_dir) if f.startswith("EXP_") and f.endswith(".md")])
    if not md_files:
        return check_item("Rule 3: has an EXP_NNN.md record", False, "no experiment record files")

    latest_md = os.path.join(exp_md_dir, md_files[-1])
    with open(latest_md, encoding="utf-8") as f:
        content = f.read()

    missing_sections = [section for section in EXP_REQUIRED_SECTIONS if section not in content]
    if missing_sections:
        return check_item("Rule 3: EXP_NNN.md is structurally complete", False,
                          f"missing sections: {', '.join(missing_sections)}")

    method_section = re.search(r"## Method\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not method_section:
        return check_item("Rule 3: Method section exists", False, f"{md_files[-1]}")

    method_text = method_section.group(1)
    # Check keywords
    has_seed = re.search(r"seed|Random Seed|no randomness", method_text, re.IGNORECASE) is not None
    has_time = re.search(r"\d{4}-\d{2}-\d{2}|Time Window|time", method_text, re.IGNORECASE) is not None
    has_data = re.search(r"Data Source|data|infra_", method_text, re.IGNORECASE) is not None
    has_control = re.search(r"Control Group|no control group|baseline|control", method_text, re.IGNORECASE) is not None

    passed = has_seed and has_time and has_data and has_control
    missing = []
    if not has_seed:
        missing.append("Random Seed")
    if not has_time:
        missing.append("time range")
    if not has_data:
        missing.append("Data Source")
    if not has_control:
        missing.append("Control Group")

    if not passed:
        return check_item(
            "Rule 3: Method section has seed/time range/data source/control group",
            False,
            f"missing: {', '.join(missing)}",
        )

    preflight_section = re.search(r"## Preflight Check\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if not preflight_section:
        return check_item("Rule 3: Preflight Check section exists", False, f"{md_files[-1]}")

    preflight_text = preflight_section.group(1)
    missing_markers = [
        marker for marker in PREFLIGHT_REQUIRED_MARKERS
        if marker not in preflight_text
    ]
    if missing_markers:
        return check_item(
            "Rule 3: Preflight Check defines the minimal smoke check and output contract",
            False,
            f"missing: {', '.join(missing_markers)}",
        )

    return check_item(
        "Rule 3: Method/Preflight have defined reproduction parameters and the minimal check",
        True,
        "Method and Preflight Check are structurally complete",
    )


def rule4_contracts(project_dir: str, registry: dict) -> dict:
    """Rule 4: actually run the Contracts Gate against all LOCKED infrastructure."""
    infra_tracks = [t for t in registry.get("tracks", []) if t.get("type") == "infrastructure"]
    if not infra_tracks:
        return check_item("Rule 4: there is an infrastructure contract to check", False, "no infrastructure tracks, cannot run contract checks")

    locked = [t for t in infra_tracks if t.get("state") == "LOCKED" and t.get("contracts")]
    if not locked:
        return check_item("Rule 4: contract check (no LOCKED infrastructure, skipped)", True,
                           "no LOCKED infrastructure contracts yet, no check needed (normal during Phase 0)")

    src_dir = Path(project_dir) / "src"
    if not src_dir.is_dir():
        return check_item("Rule 4: Contracts Gate passed", False, f"src directory does not exist: {src_dir}")
    failures: list[str] = []
    warnings: list[str] = []

    for track in locked:
        track_id = track["id"]
        contracts_rel = track.get("contracts", "")
        contracts_path = Path(project_dir) / contracts_rel

        if not contracts_path.exists():
            failures.append(f"{track_id}: contracts file does not exist ({contracts_rel})")
            continue

        try:
            with open(contracts_path, encoding="utf-8") as f:
                contract_data = yaml.safe_load(f)
        except (OSError, yaml.YAMLError) as exc:
            failures.append(f"{track_id}: contracts parse failed ({exc})")
            continue
        if contract_data is not None and not isinstance(contract_data, dict):
            failures.append(f"{track_id}: contracts top level must be a mapping")
            continue

        violations = run_check(contracts_path, [src_dir])
        if violations.has_immutable() or violations.has_critical():
            failures.append(summarize_violations(track_id, violations))
        elif violations.has_need_review():
            warnings.append(summarize_violations(track_id, violations))

    if failures:
        detail = "; ".join(failures[:3]) + ("..." if len(failures) > 3 else "")
        return check_item("Rule 4: Contracts Gate passed", False, detail)

    detail = f"checked {len(locked)} LOCKED infrastructure contracts"
    if warnings:
        detail += f"; NEED_REVIEW: {'; '.join(warnings[:2])}"
        if len(warnings) > 2:
            detail += "..."
    return check_item("Rule 4: Contracts Gate passed", True, detail)


def rule5_no_import_experiments(project_dir: str, track_id: str) -> dict:
    """Rule 5: scripts under experiments/ are not imported by other code (scans the entire src/)."""
    src_track_dir = os.path.join(project_dir, "src", "tracks", track_id)
    if not os.path.isdir(src_track_dir):
        return check_item("Rule 5: src/tracks/ directory exists", False, src_track_dir)

    violations: list[str] = []
    exp_dir = os.path.join(src_track_dir, "experiments")

    # Find all py module names under experiments/
    exp_modules: set[str] = set()
    if os.path.isdir(exp_dir):
        for f in os.listdir(exp_dir):
            if f.endswith(".py") and not f.startswith("__"):
                exp_modules.add(f[:-3])  # strip .py

    if not exp_modules:
        return check_item("Rule 5: experiments/ has py files (imports can be checked)", False,
                           "no experiment scripts, cannot check imports (please create an experiment first)")

    # Scan the entire src/ (cross-track too), skipping this track's own experiments/
    src_dir = os.path.join(project_dir, "src")
    scan_root = src_dir if os.path.isdir(src_dir) else src_track_dir

    for root, dirs, files in os.walk(scan_root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        # Skip the checked track's own experiments/ directory (it naturally contains these modules)
        if os.path.abspath(root) == os.path.abspath(exp_dir):
            dirs[:] = []
            continue

        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = []
                    if isinstance(node, ast.ImportFrom) and node.module:
                        names.append(node.module)
                    elif isinstance(node, ast.Import):
                        names.extend(alias.name for alias in node.names)

                    for name in names:
                        parts = name.split(".")
                        if "experiments" in parts:
                            violations.append(f"{fpath}: import {name}")

    passed = len(violations) == 0
    return check_item("Rule 5: no code imports experiments/", passed,
                       "; ".join(violations[:3]) + ("..." if len(violations) > 3 else ""))


def evaluate_research_gate(project_dir: str, track_id: str) -> dict:
    registry = load_registry(project_dir)
    track = require_track(
        registry,
        track_id,
        error_cls=ResearchGateError,
        expected_type="research",
    )
    current_phase = find_current_phase(project_dir, registry)
    context = build_context(project_dir, track_id, current_phase)
    cycle_label = get_cycle_label(registry)

    checks = [
        rule1_track_log(project_dir, track_id, current_phase, context, cycle_label),
        rule2_smoke_test(project_dir, track_id, context),
        rule3_params_recorded(project_dir, track_id, current_phase),
        rule4_contracts(project_dir, registry),
        rule5_no_import_experiments(project_dir, track_id),
    ]

    return gate_payload(
        "Research Gate",
        checks,
        data={
            "track_id": track_id,
            "state": track.get("state"),
            "current_phase": current_phase,
            "cycle_label": cycle_label,
            "latest_exp_id": context.get("latest_exp_id"),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Research Gate rules for a research track")
    parser.add_argument("--track-id", required=True, help="Track ID (e.g. research_strategy_momentum)")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    args = parser.parse_args()
    run_action(
        lambda: evaluate_research_gate(args.project_dir, args.track_id),
        ResearchGateError,
    )


if __name__ == "__main__":
    main()
