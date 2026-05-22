"""Unit tests for record_result.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

TOOL = Path(__file__).parent.parent.parent / "tools" / "record_result.py"
TRACK_ID = "research_strategy_momentum"
PHASE = "phase_01_research"


def run_tool(project_dir: str, extra_args: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--project-dir", project_dir] + extra_args,
        capture_output=True,
        text=True,
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


def prepare_research_project(base: Path, *, complete: bool, phase: str = PHASE) -> None:
    registry_path = base / "prae" / "track_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["current_phase"] = phase
    for track in registry["tracks"]:
        if track["id"] == TRACK_ID:
            track["state"] = "EXPLORING"
            track["experiments"] = 1
            track["evidence_summary"] = None
    registry_path.write_text(
        yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    track_dir = base / "prae" / "phases" / phase / "tracks" / TRACK_ID
    exp_dir = track_dir / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)
    (track_dir / "TRACK_LOG.md").write_text(
        "\n".join([
            f"# Track Log: {TRACK_ID}",
            "",
            f"**Track ID**: `{TRACK_ID}`",
            "**Type**: research",
            f"**Current Phase**: {phase}",
            "**Research Cycle**: cycle_1",
            "**Created**: 2026-04-20",
            "",
            "---",
            "",
            "## State",
            "",
            "**Current State**: EXPLORING",
            "**Depends On**:",
            "- `infra_data_v1`",
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
            "- No experiment records yet.",
            "",
            "---",
            "",
        ]),
        encoding="utf-8",
    )

    if complete:
        exp_md = (
            "# EXP_001\n\n## Goal\nTest the momentum factor\n\n## Method\n"
            "- Data Source: infra_data_v1.load_daily_bars\n"
            "- Time Window: 2020-01-01 to 2023-12-31\n"
            "- Random Seed: seed=42\n"
            "- Control Group: no control group\n\n"
            "## Preflight Check\n"
            "**Minimal Smoke Check**: finishes within 30s and prints sharpe\n\n"
            "**Output Contract**: stdout contains at least sharpe\n\n"
            "**Out of Scope This Time**: do not abstract into impl/\n\n"
            "## Expected Signal\nSharpe > 1.0\n\n"
            "## Result\nSharpe: 1.2\n\n"
            "## Conclusion\n**Conclusion**: supports the hypothesis\n\nRecommended state change: EXPLORING → ACTIVE\n"
        )
    else:
        exp_md = (
            "# EXP_001\n\n## Goal\nTest the momentum factor\n\n## Method\n"
            "- Data Source: infra_data_v1.load_daily_bars\n"
            "- Time Window: 2020-01-01 to 2023-12-31\n"
            "- Random Seed: seed=42\n"
            "- Control Group: no control group\n\n"
            "## Result\n{{paste key experiment output}}\n\n"
            "## Conclusion\nsupports / falsifies / partially supports the hypothesis\n"
        )
    (exp_dir / "EXP_001.md").write_text(exp_md, encoding="utf-8")


def set_phase_override(project_dir: Path, phase: str) -> None:
    registry_path = project_dir / "prae" / "track_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["current_phase_override"] = phase
    registry_path.write_text(
        yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


class TestRecordResult:
    def test_record_result_updates_track_log_and_registry(self, fake_project):
        prepare_research_project(fake_project, complete=True)

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--exp-id", "EXP_001"],
        )

        assert rc == 0, out
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["evidence_summary"] == "EXP_001: supports the hypothesis"

        log_content = (
            fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "TRACK_LOG.md"
        ).read_text(encoding="utf-8")
        assert "| EXP_001 |" in log_content
        assert "Conclusion: supports the hypothesis." in log_content
        assert "Recommend EXPLORING → ACTIVE" in log_content
        assert "EXP_001 result recorded, pending human approval" in log_content

    def test_record_result_rejects_incomplete_exp(self, fake_project):
        prepare_research_project(fake_project, complete=False)

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--exp-id", "EXP_001"],
        )

        assert rc == 1, out
        assert out["passed"] is False

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["evidence_summary"] is None

    def test_record_result_rejects_research_track_in_phase_0(self, fake_project):
        prepare_research_project(fake_project, complete=True, phase="phase_00_infra")

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--exp-id", "EXP_001"],
        )

        assert rc == 1, out
        assert out["passed"] is False
        assert "Current phase permits record experiment result" in out["summary"]

    def test_record_result_respects_current_phase_override(self, fake_project):
        prepare_research_project(fake_project, complete=True, phase=PHASE)
        set_phase_override(fake_project, "phase_00_infra")

        phase0_track_dir = fake_project / "prae" / "phases" / "phase_00_infra" / "tracks" / TRACK_ID
        phase0_exp_dir = phase0_track_dir / "experiments"
        phase0_exp_dir.mkdir(parents=True, exist_ok=True)
        (phase0_track_dir / "TRACK_LOG.md").write_text(
            (fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "TRACK_LOG.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (phase0_exp_dir / "EXP_001.md").write_text(
            (fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "experiments" / "EXP_001.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--exp-id", "EXP_001"],
        )

        assert rc == 1, out
        assert out["passed"] is False
        assert out["data"]["recorded"] is False
        assert "Current phase permits record experiment result" in out["summary"]
