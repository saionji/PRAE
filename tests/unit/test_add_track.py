"""Unit tests for add_track.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

TOOL = Path(__file__).parent.parent.parent / "tools" / "add_track.py"


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


class TestAddTrack:
    def test_add_research_track_updates_registry(self, fake_project):
        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", "research_strategy_reversal",
                "--type", "research",
                "--hypothesis", "The reversal factor works on A-share ETFs",
                "--depends-on", "infra_data_v1",
            ],
        )

        assert rc == 0, out
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == "research_strategy_reversal")
        assert track["type"] == "research"
        assert track["state"] == "EXPLORING"
        assert track["src"] == "src/tracks/research_strategy_reversal/"
        assert track["depends_on"] == ["infra_data_v1"]

    def test_add_infrastructure_track_uses_default_src(self, fake_project):
        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", "infra_feature_v2",
                "--type", "infrastructure",
                "--description", "New feature pipeline",
            ],
        )

        assert rc == 0, out
        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == "infra_feature_v2")
        assert track["src"] == "src/infra_feature_v2/"
        assert track["description"] == "New feature pipeline"

    def test_add_track_rejects_prefix_type_mismatch(self, fake_project):
        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", "infra_feature_v2",
                "--type", "research",
                "--hypothesis", "invalid",
            ],
        )

        assert rc == 2, out
        assert "does not match type=research" in out["error"]
