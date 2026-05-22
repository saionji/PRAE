"""Unit tests for graduate_track.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import yaml

from tests.unit.test_generate_conclusion import make_phase3_project

TOOL = Path(__file__).parent.parent.parent / "tools" / "graduate_track.py"


def run_tool(project_dir: str, track_id: str, pdae_project_path: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--project-dir",
            project_dir,
            "--track-id",
            track_id,
            "--pdae-project-path",
            pdae_project_path,
        ],
        capture_output=True,
        text=True,
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


class TestGraduateTrack:
    def test_records_pdae_project_and_refreshes_conclusion(self, fake_project, tmp_path):
        make_phase3_project(fake_project)
        pdae_project = tmp_path / "pdae-project"
        pdae_project.mkdir()

        rc, out = run_tool(str(fake_project), "research_strategy_momentum", str(pdae_project))
        assert rc == 0
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text())
        track = next(t for t in registry["tracks"] if t["id"] == "research_strategy_momentum")
        assert track["pdae_project"] == str(pdae_project)

        log_path = fake_project / "prae" / "phases" / "phase_03_conclusion" / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        log_content = log_path.read_text(encoding="utf-8")
        assert "## PDAE Graduation Record" in log_content
        assert str(pdae_project) in log_content

        conclusion = fake_project / "prae" / "phases" / "phase_03_conclusion" / "CONCLUSION.md"
        conclusion_content = conclusion.read_text(encoding="utf-8")
        assert str(pdae_project) in conclusion_content

    def test_invalid_state_fails(self, fake_project, tmp_path):
        pdae_project = tmp_path / "pdae-project"
        pdae_project.mkdir()

        registry_path = fake_project / "prae" / "track_registry.yaml"
        registry = yaml.safe_load(registry_path.read_text())
        registry["current_phase"] = "phase_03_conclusion"
        with open(registry_path, "w") as f:
            yaml.dump(registry, f, allow_unicode=True, default_flow_style=False)

        rc, out = run_tool(str(fake_project), "research_strategy_momentum", str(pdae_project))
        assert rc == 2

    def test_missing_phase_logs_creates_phase3_track_log_with_cycle(self, fake_project, tmp_path):
        make_phase3_project(fake_project)
        pdae_project = tmp_path / "pdae-project"
        pdae_project.mkdir()

        phase2_log = (
            fake_project / "prae" / "phases" / "phase_02_validation"
            / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        )
        phase3_log = (
            fake_project / "prae" / "phases" / "phase_03_conclusion"
            / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        )
        phase2_log.unlink()
        phase3_log.unlink()

        rc, out = run_tool(str(fake_project), "research_strategy_momentum", str(pdae_project))
        assert rc == 0
        assert out["passed"] is True

        log_content = phase3_log.read_text(encoding="utf-8")
        assert "**Research Cycle**: cycle_1" in log_content
        assert "## PDAE Graduation Record" in log_content
