"""Unit tests for generate_phase_gate.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import yaml

from tests.unit.test_check_phase_gate import make_phase1_active_track, make_phase2_graduated_track

TOOL = Path(__file__).parent.parent.parent / "tools" / "generate_phase_gate.py"


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


class TestGeneratePhaseGate:
    def test_phase0_locked_infra_generates_positive_gate(self, locked_infra_project):
        rc, out = run_tool(str(locked_infra_project))
        assert rc == 0
        assert out["data"]["current_phase"] == "phase_00_infra"
        assert out["data"]["target_phase"] == "phase_01_research"
        assert out["data"]["gate_passed"] is True
        assert out["data"]["recommendation"] == "advance"

        gate_path = Path(out["data"]["path"])
        content = gate_path.read_text(encoding="utf-8")
        assert "# Phase 0 → Phase 1 Gate Analysis" in content
        assert "**Research Cycle**: cycle_1" in content
        assert "**Recommended Action**: Advance" in content
        assert "APPROVED: pending" in content
        assert "- [x] All type=infrastructure tracks state = LOCKED" in content
        assert "- [x] check_contracts.py passes for all infrastructure contracts" in content

    def test_preserves_existing_approval_section(self, locked_infra_project):
        rc, out = run_tool(str(locked_infra_project))
        assert rc == 0

        gate_path = Path(out["data"]["path"])
        gate_path.write_text(
            gate_path.read_text(encoding="utf-8").replace(
                "APPROVED: pending\nAPPROVER: \nAPPROVED_AT: \nCOMMENT: \n",
                "APPROVED: yes\nAPPROVER: saionji\nAPPROVED_AT: 2026-04-21\nCOMMENT: Agree to advance\n",
            ),
            encoding="utf-8",
        )

        rc, out = run_tool(str(locked_infra_project))
        assert rc == 0

        content = gate_path.read_text(encoding="utf-8")
        assert "APPROVED: yes" in content
        assert "APPROVER: saionji" in content
        assert "APPROVED_AT: 2026-04-21" in content
        assert "COMMENT: Agree to advance" in content

    def test_phase0_exploring_infra_generates_blocked_gate(self, fake_project):
        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["data"]["current_phase"] == "phase_00_infra"
        assert out["data"]["gate_passed"] is False
        assert out["data"]["recommendation"] == "do not advance yet"
        assert "All type=infrastructure tracks state = LOCKED" in out["data"]["failed_conditions"]

        gate_path = Path(out["data"]["path"])
        content = gate_path.read_text(encoding="utf-8")
        assert "**Recommended Action**: Do not advance yet" in content
        assert "- [ ] All type=infrastructure tracks state = LOCKED" in content
        assert "- `All type=infrastructure tracks state = LOCKED` not met; advancing is not recommended at this time." in content

    def test_phase1_active_track_generates_research_gate(self, fake_project):
        make_phase1_active_track(fake_project, with_research_artifacts=True)

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["data"]["current_phase"] == "phase_01_research"
        assert out["data"]["target_phase"] == "phase_02_validation"
        assert out["data"]["gate_passed"] is True

        gate_path = Path(out["data"]["path"])
        content = gate_path.read_text(encoding="utf-8")
        assert "- [x] Every ACTIVE track passes the Research Gate check" in content
        assert "[TRACK_LOG.md](tracks/research_strategy_momentum/TRACK_LOG.md)" in content
        assert "[EXP_001.md](tracks/research_strategy_momentum/experiments/EXP_001.md)" in content

    def test_phase2_graduated_track_generates_validation_gate(self, fake_project):
        make_phase2_graduated_track(fake_project)

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["data"]["current_phase"] == "phase_02_validation"
        assert out["data"]["target_phase"] == "phase_03_conclusion"
        assert out["data"]["gate_passed"] is True

        gate_path = Path(out["data"]["path"])
        content = gate_path.read_text(encoding="utf-8")
        assert "**Research Cycle**: cycle_1" in content
        assert "- [x] At least one track is judged GRADUATED (otherwise consider KILLing the whole project)" in content
        assert "- [x] All GRADUATED candidates have a final-conclusion section in TRACK_LOG.md" in content

    def test_phase_override_blocks_generation(self, fake_project):
        registry_path = fake_project / "prae" / "track_registry.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        registry["current_phase_override"] = "phase_00_infra"
        registry_path.write_text(
            yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        rc, out = run_tool(str(fake_project))

        assert rc == 2, out
        assert "current_phase_override" in out.get("summary", out.get("stderr", ""))
