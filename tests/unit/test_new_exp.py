"""Unit tests for new_exp.py."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

TOOL = Path(__file__).parent.parent.parent / "tools" / "new_exp.py"
PRAE_ROOT = Path(__file__).parent.parent.parent
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


def prepare_templates(project_dir: Path) -> None:
    templates_dir = project_dir / "prae" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PRAE_ROOT / "runtime" / "abstract" / "EXP_NNN.template.md", templates_dir / "EXP_NNN.template.md")


def set_phase(project_dir: Path, phase: str) -> None:
    registry_path = project_dir / "prae" / "track_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["current_phase"] = phase
    for track in registry["tracks"]:
        if track["id"] == TRACK_ID:
            track["experiments"] = 0
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


def materialize_track(project_dir: Path, phase: str) -> None:
    track_dir = project_dir / "prae" / "phases" / phase / "tracks" / TRACK_ID / "experiments"
    track_dir.mkdir(parents=True, exist_ok=True)


class TestNewExp:
    def test_new_exp_creates_md_py_and_updates_registry(self, fake_project):
        prepare_templates(fake_project)
        set_phase(fake_project, "phase_01_research")
        materialize_track(fake_project, "phase_01_research")

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--title", "首个动量实验"],
        )

        assert rc == 0, out
        assert out["passed"] is True
        assert out["data"]["exp_id"] == "EXP_001"

        exp_md = (
            fake_project / "prae" / "phases" / "phase_01_research" / "tracks" / TRACK_ID / "experiments" / "EXP_001.md"
        )
        exp_py = fake_project / "src" / "tracks" / TRACK_ID / "experiments" / "EXP_001.py"
        assert exp_md.exists()
        assert exp_py.exists()

        md_content = exp_md.read_text(encoding="utf-8")
        py_content = exp_py.read_text(encoding="utf-8")
        assert "# EXP_001：首个动量实验" in md_content
        assert "**状态**: 进行中" in md_content
        assert "{{NNN}}" not in md_content
        assert "EXP_001: 首个动量实验" in py_content
        assert "此文件不能被其他代码 import" in py_content

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["experiments"] == 1

    def test_new_exp_rejects_research_track_in_phase_0(self, fake_project):
        prepare_templates(fake_project)
        materialize_track(fake_project, "phase_00_infra")

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--title", "不应创建"],
        )

        assert rc == 1, out
        assert out["passed"] is False
        assert "当前阶段允许创建实验" in out["summary"]

    def test_new_exp_respects_current_phase_override(self, fake_project):
        prepare_templates(fake_project)
        set_phase(fake_project, "phase_01_research")
        set_phase_override(fake_project, "phase_00_infra")
        materialize_track(fake_project, "phase_00_infra")

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--title", "不应创建"],
        )

        assert rc == 1, out
        assert out["passed"] is False
        assert out["data"]["current_phase"] == "phase_00_infra"
        assert "当前阶段允许创建实验" in out["summary"]
