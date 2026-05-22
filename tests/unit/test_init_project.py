"""Unit tests for init_project.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

TOOL = Path(__file__).parent.parent.parent / "tools" / "init_project.py"
TEMPLATES = Path(__file__).parent.parent.parent / "runtime" / "abstract"


def run_tool(name: str, output_dir: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--name", name, "--output-dir", output_dir],
        capture_output=True, text=True
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


def setup_prae_init(target: Path) -> None:
    """Create a minimal PRAE_INIT.md and templates in target dir."""
    prae_dir = target / "prae"
    prae_dir.mkdir(parents=True, exist_ok=True)

    # Copy templates
    tmpl_dst = prae_dir / "templates"
    tmpl_dst.mkdir(parents=True, exist_ok=True)
    for f in TEMPLATES.iterdir():
        import shutil
        shutil.copy2(f, tmpl_dst / f.name)

    (prae_dir / "PRAE_INIT.md").write_text("""# PRAE Init

## Problem Statement

**Research Question**: Test project

**Success Criteria**: Test

## Component Classification → Infrastructure Tracks

| Track ID | Description | External Systems | Notes |
|---------|------|---------------|------|
| `infra_data_v1` | Data ingestion | — | — |

## Component Classification → Research Tracks

| Track ID | Hypothesis (one line) | Infrastructure Dependencies | Initial Priority |
|---------|--------------|---------------|------------|
| `research_strategy_momentum` | Momentum factor is effective | `infra_data_v1` | High |

## Phase 0 Success Criteria

| Infrastructure Track ID | LOCKED Criteria | Current State |
|----------------|----------------|---------|
| `infra_data_v1` | Interface stable | EXPLORING |
""")


class TestInitProject:
    def test_success(self, tmp_path):
        setup_prae_init(tmp_path)
        rc, out = run_tool("test-project", str(tmp_path))
        assert rc == 0
        assert out["passed"] is True
        assert out["data"]["infra_tracks"] == 1
        assert out["data"]["research_tracks"] == 1

    def test_creates_track_registry(self, tmp_path):
        setup_prae_init(tmp_path)
        run_tool("test-project", str(tmp_path))
        reg = tmp_path / "prae" / "track_registry.yaml"
        assert reg.exists()
        r = yaml.safe_load(reg.read_text())
        assert r["project"] == "test-project"
        assert r["current_phase"] == "phase_00_infra"
        assert len(r["tracks"]) == 2

    def test_creates_phase0_structure(self, tmp_path):
        setup_prae_init(tmp_path)
        run_tool("test-project", str(tmp_path))
        phase0 = tmp_path / "prae" / "phases" / "phase_00_infra"
        assert phase0.is_dir()
        track_dir = phase0 / "tracks" / "infra_data_v1"
        assert track_dir.is_dir()
        assert (track_dir / "experiments").is_dir()

    def test_missing_prae_init_fails(self, tmp_path):
        (tmp_path / "prae").mkdir()
        rc, out = run_tool("test-project", str(tmp_path))
        assert rc == 1
        assert out["passed"] is False

    def test_creates_src_structure(self, tmp_path):
        setup_prae_init(tmp_path)
        run_tool("test-project", str(tmp_path))
        assert (tmp_path / "src" / "shared").is_dir()
        assert (tmp_path / "src" / "tracks").is_dir()
        assert (tmp_path / "src" / "infra_data_v1").is_dir()

    def test_renders_phase0_brief_without_placeholders(self, tmp_path):
        setup_prae_init(tmp_path)
        run_tool("test-project", str(tmp_path))

        brief = tmp_path / "prae" / "phases" / "phase_00_infra" / "PHASE_BRIEF.md"
        content = brief.read_text(encoding="utf-8")
        assert "{{" not in content
        assert "**Phase**: phase_00_infra" in content
        assert "**Research Cycle**: cycle_1" in content
        assert "infra_data_v1" in content
        assert "Data ingestion" in content
        assert "LOCKED criteria: Interface stable" in content

    def test_renders_infra_track_log_without_placeholders(self, tmp_path):
        setup_prae_init(tmp_path)
        run_tool("test-project", str(tmp_path))

        log_path = (
            tmp_path / "prae" / "phases" / "phase_00_infra"
            / "tracks" / "infra_data_v1" / "TRACK_LOG.md"
        )
        content = log_path.read_text(encoding="utf-8")
        assert "{{" not in content
        assert "**Type**: infrastructure" in content
        assert "**Current Phase**: phase_00_infra" in content
        assert "**Research Cycle**: cycle_1" in content
        assert "Infrastructure goal: Data ingestion" in content
        assert "LOCKED criteria: Interface stable" in content
