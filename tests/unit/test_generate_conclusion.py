"""Unit tests for generate_conclusion.py."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from tests.unit.test_check_phase_gate import make_phase2_graduated_track

TOOL = Path(__file__).parent.parent.parent / "tools" / "generate_conclusion.py"


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


def make_phase3_project(fake_project: Path) -> Path:
    make_phase2_graduated_track(fake_project)
    registry_path = fake_project / "prae" / "track_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text())
    registry["current_cycle"] = registry.get("current_cycle", 1)
    registry["current_phase"] = "phase_03_conclusion"
    with open(registry_path, "w") as f:
        yaml.dump(registry, f, allow_unicode=True, default_flow_style=False)

    src = fake_project / "prae" / "phases" / "phase_02_validation" / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
    dst = fake_project / "prae" / "phases" / "phase_03_conclusion" / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return fake_project


class TestGenerateConclusion:
    def test_phase3_conclusion_marks_pending_pdae(self, fake_project):
        make_phase3_project(fake_project)

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["passed"] is True
        conclusion_path = Path(out["data"]["path"])
        content = conclusion_path.read_text(encoding="utf-8")
        assert "# CONCLUSION — fake-research" in content
        assert "**Research Cycle**: cycle_1" in content
        assert "`research_strategy_momentum` | `to be filled in`" in content
        assert "is GRADUATED but has no registered PDAE project path yet" in content
        assert "APPROVED: pending" in content
        assert "DECISION: " in content
        assert "APPROVER: " in content
        assert "APPROVED_AT: " in content
        assert "COMMENT: " in content

    def test_existing_structured_final_decision_is_preserved(self, fake_project):
        make_phase3_project(fake_project)
        conclusion_path = fake_project / "prae" / "phases" / "phase_03_conclusion" / "CONCLUSION.md"
        conclusion_path.parent.mkdir(parents=True, exist_ok=True)
        conclusion_path.write_text(
            "# CONCLUSION\n\n## Final Decision\n\nAPPROVED: yes\nDECISION: GRADUATED_TO_PDAE\nAPPROVER: saionji\nAPPROVED_AT: 2026-04-20\nCOMMENT: ready\n",
            encoding="utf-8",
        )

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        content = conclusion_path.read_text(encoding="utf-8")
        assert "DECISION: GRADUATED_TO_PDAE" in content
        assert "APPROVER: saionji" in content
        assert "COMMENT: ready" in content

    def test_legacy_final_decision_is_migrated(self, fake_project):
        make_phase3_project(fake_project)
        conclusion_path = fake_project / "prae" / "phases" / "phase_03_conclusion" / "CONCLUSION.md"
        conclusion_path.parent.mkdir(parents=True, exist_ok=True)
        conclusion_path.write_text(
            "# CONCLUSION\n\n## Final Decision\n\n**APPROVED**: yes\n\n**Decision** (human-filled):\n\n```\nGRADUATED_TO_PDAE\n```\n\n**Approver**: saionji\n**Date**: 2026-04-20\n",
            encoding="utf-8",
        )

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        content = conclusion_path.read_text(encoding="utf-8")
        assert "APPROVED: yes" in content
        assert "DECISION: GRADUATED_TO_PDAE" in content
        assert "APPROVER: saionji" in content
        assert "APPROVED_AT: 2026-04-20" in content

    def test_conclusion_can_read_archived_cycle_track_log(self, fake_project):
        make_phase3_project(fake_project)
        registry_path = fake_project / "prae" / "track_registry.yaml"
        registry = yaml.safe_load(registry_path.read_text())
        registry["current_cycle"] = 2
        with open(registry_path, "w") as f:
            yaml.dump(registry, f, allow_unicode=True, default_flow_style=False)

        current_log = (
            fake_project / "prae" / "phases" / "phase_03_conclusion"
            / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        )
        archived_log = (
            fake_project / "prae" / "history" / "cycle_1" / "phases" / "phase_03_conclusion"
            / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        )
        archived_log.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current_log, archived_log)
        current_log.unlink()

        archived_validation_log = (
            fake_project / "prae" / "history" / "cycle_1" / "phases" / "phase_02_validation"
            / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        )
        archived_validation_log.parent.mkdir(parents=True, exist_ok=True)
        validation_log = (
            fake_project / "prae" / "phases" / "phase_02_validation"
            / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        )
        shutil.copy2(validation_log, archived_validation_log)
        shutil.rmtree(fake_project / "prae" / "phases" / "phase_02_validation")

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        content = Path(out["data"]["path"]).read_text(encoding="utf-8")
        assert "**Research Cycle**: cycle_2" in content
        assert "GRADUATED — signal is stable, handed off to PDAE." in content
