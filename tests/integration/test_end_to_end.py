"""Integration test: full PRAE lifecycle from init to phase gate."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

TOOLS = Path(__file__).parent.parent.parent / "tools"
PRAE_ROOT = Path(__file__).parent.parent.parent
TEMPLATES = PRAE_ROOT / "runtime" / "abstract"


def run(tool: str, args: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOLS / tool)] + args,
        capture_output=True, text=True
    )
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        out = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, out


@pytest.fixture
def research_project(tmp_path: Path) -> Path:
    """Set up a complete PRAE research project for integration testing."""
    project = tmp_path / "my_research"
    project.mkdir()

    # Create .claude/ (Claude Code project)
    (project / ".claude").mkdir()

    # Bootstrap PRAE
    rc, out = run("prae_bootstrap.py", [
        "--target", str(project),
        "--client", "claude-code",
        "--prae-path", str(PRAE_ROOT),
    ])
    assert rc == 0, f"bootstrap failed: {out}"

    # Write a real PRAE_INIT.md
    (project / "prae" / "PRAE_INIT.md").write_text("""# PRAE Init

## Problem Statement

**Research Question**: Effectiveness study of A-share ETF momentum arbitrage strategy

**Success Criteria**: Sharpe >= 1.0, max drawdown <= 25%

## Component Classification → Infrastructure Tracks

| Track ID | Description | External Systems | Notes |
|---------|------|---------------|------|
| `infra_data_v1` | A-share daily market data | Wind | — |

## Component Classification → Research Tracks

| Track ID | Hypothesis (one line) | Infrastructure Dependencies | Initial Priority |
|---------|--------------|---------------|------------|
| `research_strategy_momentum` | Momentum factor yields positive excess return on A-share ETFs | `infra_data_v1` | High |

## Phase 0 Success Criteria

| Infrastructure Track ID | LOCKED Criteria | Current State |
|----------------|----------------|---------|
| `infra_data_v1` | Interface stable, contracts.yaml definition complete | EXPLORING |
""")

    return project


class TestEndToEnd:
    def test_step1_bootstrap(self, research_project):
        """Bootstrap deployed key files."""
        assert (research_project / ".claude" / "skills" / "prae-guard.md").exists()
        assert (research_project / "tools" / "_artifacts.py").exists()
        assert (research_project / "tools" / "_cli.py").exists()
        assert (research_project / "tools" / "_conclusion_docs.py").exists()
        assert (research_project / "tools" / "_gate_utils.py").exists()
        assert (research_project / "tools" / "_phase_docs.py").exists()
        assert (research_project / "prae" / "templates" / "TRACK_LOG.template.md").exists()
        assert (research_project / "tools" / "_registry.py").exists()
        assert (research_project / "tools" / "add_track.py").exists()
        assert (research_project / "tools" / "advance_phase.py").exists()
        assert (research_project / "tools" / "check_conclusion.py").exists()
        assert (research_project / "tools" / "generate_conclusion.py").exists()
        assert (research_project / "tools" / "generate_phase_gate.py").exists()
        assert (research_project / "tools" / "finalize_project.py").exists()
        assert (research_project / "tools" / "graduate_track.py").exists()
        assert (research_project / "tools" / "lock_infra_track.py").exists()
        assert (research_project / "tools" / "new_exp.py").exists()
        assert (research_project / "tools" / "new_track.py").exists()
        assert (research_project / "tools" / "record_result.py").exists()
        assert (research_project / "tools" / "reopen_project.py").exists()
        assert (research_project / "tools" / "update_track_state.py").exists()

    def test_step2_init_project(self, research_project):
        """init_project creates registry + phase 0 structure."""
        rc, out = run("init_project.py", [
            "--name", "my_research",
            "--output-dir", str(research_project),
        ])
        assert rc == 0
        assert out["passed"] is True

        reg = research_project / "prae" / "track_registry.yaml"
        assert reg.exists()
        r = yaml.safe_load(reg.read_text())
        assert r["current_cycle"] == 1
        assert r["current_phase"] == "phase_00_infra"
        assert any(t["id"] == "infra_data_v1" for t in r["tracks"])

        brief = research_project / "prae" / "phases" / "phase_00_infra" / "PHASE_BRIEF.md"
        brief_content = brief.read_text(encoding="utf-8")
        assert "{{" not in brief_content
        assert "**Research Cycle**: cycle_1" in brief_content

        log_path = (
            research_project / "prae" / "phases" / "phase_00_infra"
            / "tracks" / "infra_data_v1" / "TRACK_LOG.md"
        )
        log_content = log_path.read_text(encoding="utf-8")
        assert "{{" not in log_content
        assert "**Research Cycle**: cycle_1" in log_content

    def test_step3_track_status_exploring(self, research_project):
        """After init, track status check passes with EXPLORING tracks."""
        run("init_project.py", ["--name", "my_research", "--output-dir", str(research_project)])
        rc, out = run("check_track_status.py", ["--project-dir", str(research_project)])
        assert rc == 0
        assert out["passed"] is True

    def test_step4_phase_gate_fails_exploring(self, research_project):
        """Phase 0→1 gate fails when infra is still EXPLORING."""
        run("init_project.py", ["--name", "my_research", "--output-dir", str(research_project)])
        rc, out = run("check_phase_gate.py", [
            "--project-dir", str(research_project), "--phase", "0"
        ])
        assert rc == 1
        assert out["passed"] is False

    def test_step5_lock_infra_and_gate_passes(self, research_project):
        """After locking infra with contracts + spec, Phase 0→1 gate passes."""
        run("init_project.py", ["--name", "my_research", "--output-dir", str(research_project)])

        infra_dir = research_project / "src" / "infra_data_v1"
        infra_dir.mkdir(parents=True, exist_ok=True)
        (infra_dir / "contracts.yaml").write_text("exports:\n  - load_daily_bars\n")
        (infra_dir / "MODULE_SPEC.md").write_text("# MODULE_SPEC\n\n## Exports\n- load_daily_bars\n")

        rc, out = run("lock_infra_track.py", [
            "--project-dir", str(research_project),
            "--track-id", "infra_data_v1",
            "--approver", "saionji",
            "--approved-at", "2026-04-20",
            "--reason", "PDAE M3 passed",
        ])
        assert rc == 0, out

        rc, out = run("check_phase_gate.py", [
            "--project-dir", str(research_project), "--phase", "0"
        ])
        assert rc == 0, f"Phase gate failed: {out}"
        assert out["passed"] is True

    def test_step6_research_gate_after_experiment(self, research_project):
        """Research Gate passes after a complete experiment is recorded."""
        run("init_project.py", ["--name", "my_research", "--output-dir", str(research_project)])

        reg = research_project / "prae" / "track_registry.yaml"
        r = yaml.safe_load(reg.read_text())
        r["current_phase"] = "phase_01_research"
        for t in r["tracks"]:
            if t["id"] == "research_strategy_momentum":
                t["state"] = "ACTIVE"
                t["experiments"] = 1
        with open(reg, "w") as f:
            yaml.dump(r, f, allow_unicode=True, default_flow_style=False)

        track_dir = (research_project / "prae" / "phases" / "phase_01_research"
                     / "tracks" / "research_strategy_momentum")
        track_dir.mkdir(parents=True, exist_ok=True)
        exp_dir = track_dir / "experiments"
        exp_dir.mkdir()
        (exp_dir / "EXP_001.md").write_text(
            "# EXP_001\n\n## Goal\nMomentum factor test\n\n## Method\n"
            "- Data Source: infra_data_v1.load_daily_bars\n"
            "- Time Window: 2020-01-01 to 2023-12-31\n"
            "- Random Seed: seed=42\n"
            "- Control Group: no control group\n\n"
            "## Preflight Check\n"
            "**Minimal Smoke Check**: completes within 30s and prints sharpe\n\n"
            "**Output Contract**: stdout contains at least sharpe\n\n"
            "**Out of Scope This Time**: do not abstract into impl/\n\n"
            "## Expected Signal\nSharpe > 1.0\n\n## Result\nSharpe: 1.2\n\n"
            "## Conclusion\n**Conclusion**: supports the hypothesis\n\nRecommended state change: ACTIVE → GRADUATED\n"
        )
        (track_dir / "TRACK_LOG.md").write_text(
            "# TRACK_LOG\n\n**Research Cycle**: cycle_1\n\n## Experiments\n\n| EXP ID | Date | Purpose | Conclusion | Link |\n|--------|------|------|------|------|\n| — | — | No experiment records yet | — | — |\n"
            "\n---\n\n## Evidence Summary\n\n- No experiment records yet.\n"
        )
        py_dir = research_project / "src" / "tracks" / "research_strategy_momentum" / "experiments"
        py_dir.mkdir(parents=True, exist_ok=True)
        (py_dir / "EXP_001.py").write_text("def main():\n    print('sharpe=1.2')\nif __name__=='__main__':\n    main()\n")

        rc_record, out_record = run("record_result.py", [
            "--project-dir", str(research_project),
            "--track-id", "research_strategy_momentum",
            "--exp-id", "EXP_001",
        ])
        assert rc_record == 0, out_record

        rc, out = run("check_research_gate.py", [
            "--track-id", "research_strategy_momentum",
            "--project-dir", str(research_project),
        ])
        assert rc == 0, f"Research gate failed: {out}"
        assert out["passed"] is True

    def test_step7_generate_approve_and_advance_phase(self, research_project):
        """Generate PHASE_GATE, approve it, then advance to Phase 1 via the formal tool."""
        run("init_project.py", ["--name", "my_research", "--output-dir", str(research_project)])

        infra_dir = research_project / "src" / "infra_data_v1"
        infra_dir.mkdir(parents=True, exist_ok=True)
        (infra_dir / "contracts.yaml").write_text("exports:\n  - load_daily_bars\n")
        (infra_dir / "MODULE_SPEC.md").write_text("# MODULE_SPEC\n\n## Exports\n- load_daily_bars\n")

        rc_lock, out_lock = run("lock_infra_track.py", [
            "--project-dir", str(research_project),
            "--track-id", "infra_data_v1",
            "--approver", "saionji",
            "--approved-at", "2026-04-20",
            "--reason", "PDAE M3 passed",
        ])
        assert rc_lock == 0, out_lock

        reg = research_project / "prae" / "track_registry.yaml"

        rc, out = run("generate_phase_gate.py", ["--project-dir", str(research_project)])
        assert rc == 0
        gate_path = Path(out["data"]["path"])
        content = gate_path.read_text(encoding="utf-8")
        content = content.replace("APPROVED: pending", "APPROVED: yes")
        content = content.replace("APPROVER: ", "APPROVER: saionji")
        content = content.replace("APPROVED_AT: ", "APPROVED_AT: 2026-04-20")
        gate_path.write_text(content, encoding="utf-8")

        rc2, out2 = run("advance_phase.py", ["--project-dir", str(research_project)])
        assert rc2 == 0, out2
        assert out2["passed"] is True

        updated = yaml.safe_load(reg.read_text())
        assert updated["current_phase"] == "phase_01_research"
        assert (research_project / "prae" / "phases" / "phase_01_research" / "PHASE_BRIEF.md").exists()
        assert (
            research_project / "prae" / "phases" / "phase_01_research"
            / "tracks" / "research_strategy_momentum" / "TRACK_LOG.md"
        ).exists()
