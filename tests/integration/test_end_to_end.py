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

## 问题陈述

**研究问题**: A股ETF动量套利策略有效性研究

**成功标准**: 夏普 ≥ 1.0，最大回撤 ≤ 25%

## 组件分类 → 基础设施轨道

| 轨道 ID | 描述 | 依赖的外部系统 | 备注 |
|---------|------|---------------|------|
| `infra_data_v1` | A股日频行情数据 | Wind | — |

## 组件分类 → 研究轨道

| 轨道 ID | 假设（一句话） | 依赖的基础设施 | 初始优先级 |
|---------|--------------|---------------|------------|
| `research_strategy_momentum` | 动量因子在A股ETF上有正向超额收益 | `infra_data_v1` | 高 |

## Phase 0 成功标准

| 基础设施轨道 ID | LOCKED 判断标准 | 当前状态 |
|----------------|----------------|---------|
| `infra_data_v1` | 接口稳定，contracts.yaml 定义完成 | EXPLORING |
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
        assert "**研究轮次**: cycle_1" in brief_content

        log_path = (
            research_project / "prae" / "phases" / "phase_00_infra"
            / "tracks" / "infra_data_v1" / "TRACK_LOG.md"
        )
        log_content = log_path.read_text(encoding="utf-8")
        assert "{{" not in log_content
        assert "**研究轮次**: cycle_1" in log_content

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
            "--reason", "PDAE M3 通过",
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
            "# EXP_001\n\n## Goal\n动量因子测试\n\n## Method\n"
            "- 数据源: infra_data_v1.load_daily_bars\n"
            "- 时间窗: 2020-01-01 至 2023-12-31\n"
            "- 随机种子: seed=42\n"
            "- 对照组: 无对照组\n\n"
            "## Preflight Check\n"
            "**最小冒烟检查**: 30s 内跑完，并打印 sharpe\n\n"
            "**输出契约**: stdout 至少包含 sharpe\n\n"
            "**本次不做**: 不抽象到 impl/\n\n"
            "## Expected Signal\n夏普>1.0\n\n## Result\n夏普: 1.2\n\n"
            "## Conclusion\n**结论**: 支持假设\n\n建议 state 变更: ACTIVE → GRADUATED\n"
        )
        (track_dir / "TRACK_LOG.md").write_text(
            "# TRACK_LOG\n\n**研究轮次**: cycle_1\n\n## Experiments\n\n| EXP ID | 日期 | 目的 | 结论 | 链接 |\n|--------|------|------|------|------|\n| — | — | 尚无实验记录 | — | — |\n"
            "\n---\n\n## Evidence Summary\n\n- 暂无实验记录。\n"
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
            "--reason", "PDAE M3 通过",
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
