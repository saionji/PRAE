"""Unit tests for new_track.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

TOOL = Path(__file__).parent.parent.parent / "tools" / "new_track.py"
TRACK_ID = "research_strategy_momentum"


def run_tool(project_dir: str, extra_args: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--project-dir", project_dir] + extra_args,
        capture_output=True,
        text=True,
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        try:
            output = json.loads(proc.stderr)
        except json.JSONDecodeError:
            output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


def set_phase(project_dir: Path, phase: str) -> None:
    registry_path = project_dir / "prae" / "track_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["current_phase"] = phase
    registry_path.write_text(
        yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def set_phase_override(project_dir: Path, phase: str) -> None:
    registry_path = project_dir / "prae" / "track_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["current_phase_override"] = phase
    registry_path.write_text(
        yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


class TestNewTrack:
    def test_new_track_creates_research_phase_dir_and_log(self, fake_project):
        set_phase(fake_project, "phase_01_research")

        rc, out = run_tool(str(fake_project), ["--track-id", TRACK_ID])

        assert rc == 0, out
        assert out["passed"] is True

        track_dir = fake_project / "prae" / "phases" / "phase_01_research" / "tracks" / TRACK_ID
        log_path = track_dir / "TRACK_LOG.md"
        assert log_path.exists()
        assert (track_dir / "experiments").is_dir()
        assert (fake_project / "src" / "tracks" / TRACK_ID / "experiments").is_dir()
        assert (fake_project / "src" / "tracks" / TRACK_ID / "impl").is_dir()

        content = log_path.read_text(encoding="utf-8")
        assert "**Current Phase**: phase_01_research" in content
        assert "**Type**: research" in content
        assert "The momentum factor yields significant positive returns on daily-frequency equity data" in content

    def test_new_track_rejects_research_track_in_phase_0(self, fake_project):
        rc, out = run_tool(str(fake_project), ["--track-id", TRACK_ID])

        assert rc == 1, out
        assert out["passed"] is False
        assert "Current phase permits create track directory" in out["summary"]

    def test_new_track_respects_current_phase_override(self, fake_project):
        set_phase(fake_project, "phase_02_validation")
        set_phase_override(fake_project, "phase_00_infra")

        rc, out = run_tool(str(fake_project), ["--track-id", "infra_data_v1"])

        assert rc == 0, out
        assert out["passed"] is True
        assert out["data"]["current_phase"] == "phase_00_infra"
        assert (
            fake_project / "prae" / "phases" / "phase_00_infra" / "tracks" / "infra_data_v1" / "TRACK_LOG.md"
        ).exists()

    def test_new_track_keeps_existing_phase0_infra_log(self, fake_project):
        existing_log = (
            fake_project / "prae" / "phases" / "phase_00_infra" / "tracks" / "infra_data_v1" / "TRACK_LOG.md"
        )
        before = existing_log.read_text(encoding="utf-8")

        rc, out = run_tool(str(fake_project), ["--track-id", "infra_data_v1"])

        assert rc == 0, out
        assert out["passed"] is True
        assert "Track ready" in out["summary"]
        assert existing_log.read_text(encoding="utf-8") == before
