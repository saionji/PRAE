"""Unit tests for advance_phase.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import yaml

from tests.unit.test_check_phase_gate import (
    make_phase1_active_track,
    make_phase2_graduated_track,
    make_valid_phase_gate_doc,
)

TOOL = Path(__file__).parent.parent.parent / "tools" / "advance_phase.py"


def run_tool(project_dir: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--project-dir", project_dir],
        capture_output=True,
        text=True,
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


class TestAdvancePhase:
    def test_pending_approval_fails(self, locked_infra_project):
        gate_dir = locked_infra_project / "prae" / "phases" / "phase_00_infra"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(0, 1, "phase_01_research", "pending"),
            encoding="utf-8",
        )

        rc, out = run_tool(str(locked_infra_project))
        assert rc == 1
        assert out["passed"] is False
        assert out["data"]["advanced"] is False

    def test_phase0_to_phase1_advance_creates_research_workspace(self, locked_infra_project):
        gate_dir = locked_infra_project / "prae" / "phases" / "phase_00_infra"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(0, 1, "phase_01_research", "yes"),
            encoding="utf-8",
        )

        rc, out = run_tool(str(locked_infra_project))
        assert rc == 0
        assert out["passed"] is True
        assert out["data"]["target_phase"] == "phase_01_research"

        registry = yaml.safe_load((locked_infra_project / "prae" / "track_registry.yaml").read_text())
        assert registry["current_phase"] == "phase_01_research"

        brief = locked_infra_project / "prae" / "phases" / "phase_01_research" / "PHASE_BRIEF.md"
        assert brief.exists()
        brief_content = brief.read_text(encoding="utf-8")
        assert "完成研究轨道的首轮实验与证据积累" in brief_content
        assert "cycle_1" in brief_content
        assert "research_strategy_momentum" in brief_content

        log_path = (
            locked_infra_project
            / "prae" / "phases" / "phase_01_research" / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        )
        assert log_path.exists()
        log_content = log_path.read_text(encoding="utf-8")
        assert "动量因子在A股日频数据上有显著正向收益" in log_content
        assert "cycle_1" in log_content
        assert "{{" not in log_content

    def test_phase1_to_phase2_advance_copies_active_track_log(self, fake_project):
        make_phase1_active_track(fake_project, with_research_artifacts=True)
        gate_dir = fake_project / "prae" / "phases" / "phase_01_research"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(1, 2, "phase_02_validation", "yes"),
            encoding="utf-8",
        )

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["passed"] is True
        assert out["data"]["target_phase"] == "phase_02_validation"
        assert out["data"]["copied_logs"] == 1

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text())
        assert registry["current_phase"] == "phase_02_validation"

        copied_log = (
            fake_project
            / "prae" / "phases" / "phase_02_validation" / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        )
        assert copied_log.exists()
        copied_content = copied_log.read_text(encoding="utf-8")
        assert "EXP_001" in copied_content
        assert "cycle_1" in copied_content

    def test_phase2_to_phase3_advance_generates_conclusion_brief(self, fake_project):
        make_phase2_graduated_track(fake_project)
        gate_dir = fake_project / "prae" / "phases" / "phase_02_validation"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(2, 3, "phase_03_conclusion", "yes"),
            encoding="utf-8",
        )

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["passed"] is True
        assert out["data"]["target_phase"] == "phase_03_conclusion"

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text())
        assert registry["current_phase"] == "phase_03_conclusion"
        assert registry["tracks"][1]["concluded_at"] == "2026-04-20"

        brief = fake_project / "prae" / "phases" / "phase_03_conclusion" / "PHASE_BRIEF.md"
        content = brief.read_text(encoding="utf-8")
        assert "待 PDAE 路由" in content
        assert "cycle_1" in content
        assert "research_strategy_momentum" in content

        conclusion = fake_project / "prae" / "phases" / "phase_03_conclusion" / "CONCLUSION.md"
        assert conclusion.exists()
        conclusion_content = conclusion.read_text(encoding="utf-8")
        assert "CONCLUSION" in conclusion_content
        assert "cycle_1" in conclusion_content

    def test_phase_override_blocks_advance(self, locked_infra_project):
        gate_dir = locked_infra_project / "prae" / "phases" / "phase_00_infra"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(0, 1, "phase_01_research", "yes"),
            encoding="utf-8",
        )

        registry_path = locked_infra_project / "prae" / "track_registry.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        registry["current_phase_override"] = "phase_00_infra"
        registry_path.write_text(
            yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        rc, out = run_tool(str(locked_infra_project))

        assert rc == 2, out
        assert "current_phase_override" in out.get("summary", out.get("stderr", ""))
