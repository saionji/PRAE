"""Unit tests for check_research_gate.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).parent.parent.parent / "tools" / "check_research_gate.py"
TRACK_ID = "research_strategy_momentum"
PHASE = "phase_01_research"


def run_tool(project_dir: str, track_id: str = TRACK_ID) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--track-id", track_id, "--project-dir", project_dir],
        capture_output=True, text=True
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


def make_research_project(base: Path, *, lock_infra: bool = False) -> Path:
    """Set up a minimal research project with ACTIVE research track in phase_01."""
    import yaml

    reg = base / "prae" / "track_registry.yaml"
    with open(reg) as f:
        r = yaml.safe_load(f)
    r["current_phase"] = PHASE
    for t in r["tracks"]:
        if t["id"] == TRACK_ID:
            t["state"] = "ACTIVE"
            t["experiments"] = 1
    with open(reg, "w") as f:
        yaml.dump(r, f, allow_unicode=True)

    if lock_infra:
        infra_dir = base / "src" / "infra_data_v1"
        infra_dir.mkdir(parents=True, exist_ok=True)
        (infra_dir / "contracts.yaml").write_text("source: infra_data_v1\ngenerated_at: 2026-04-20\n")
        for t in r["tracks"]:
            if t["id"] == "infra_data_v1":
                t["state"] = "LOCKED"
                t["contracts"] = "src/infra_data_v1/contracts.yaml"
        with open(reg, "w") as f:
            yaml.dump(r, f, allow_unicode=True)

    # Create track log in phase_01
    track_dir = base / "prae" / "phases" / PHASE / "tracks" / TRACK_ID
    track_dir.mkdir(parents=True, exist_ok=True)
    (track_dir / "TRACK_LOG.md").write_text(
        "# TRACK_LOG\n\n**研究轮次**: cycle_1\n\n## Experiments\n\n| EXP_001 | 2026-04-20 | 测试动量因子 | 支持 | [EXP_001.md](experiments/EXP_001.md) |\n"
        "\n## Evidence Summary\n\n- EXP_001: 测试\n"
    )

    # Create EXP_001.md
    exp_dir = track_dir / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "EXP_001.md").write_text(
        "# EXP_001\n\n## Goal\n测试动量因子\n\n## Method\n"
        "- 数据源: infra_data_v1.load_daily_bars\n"
        "- 时间窗: 2020-01-01 至 2023-12-31\n"
        "- 随机种子: seed=42\n"
        "- 动量窗口: 20日\n\n"
        "- 对照组: 无对照组\n\n"
        "## Preflight Check\n"
        "**最小冒烟检查**: 30s 内跑完，并打印 sharpe\n\n"
        "**输出契约**: stdout 至少包含 sharpe\n\n"
        "**本次不做**: 不抽象到 impl/\n\n"
        "## Expected Signal\n夏普>1.0\n\n## Result\n夏普: 1.2\n\n## Conclusion\n**结论**: 支持假设\n"
    )

    # Create EXP_001.py
    py_dir = base / "src" / "tracks" / TRACK_ID / "experiments"
    py_dir.mkdir(parents=True, exist_ok=True)
    (py_dir / "EXP_001.py").write_text(
        "def main():\n    print('EXP_001')\n\nif __name__ == '__main__':\n    main()\n"
    )

    return base


class TestResearchGate:
    def test_missing_track_id_error(self, fake_project):
        rc, out = run_tool(str(fake_project), "research_nonexistent")
        assert rc == 2

    def test_infra_track_not_applicable(self, fake_project):
        rc, out = run_tool(str(fake_project), "infra_data_v1")
        assert rc == 2

    def test_full_pass(self, fake_project):
        make_research_project(fake_project)
        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["passed"] is True

    def test_fail_no_exp_py(self, fake_project):
        make_research_project(fake_project)
        # Remove the EXP py file
        py_file = fake_project / "src" / "tracks" / TRACK_ID / "experiments" / "EXP_001.py"
        py_file.unlink()
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_import_from_experiments(self, fake_project):
        make_research_project(fake_project)
        # Create impl/ file that imports from experiments/
        impl_dir = fake_project / "src" / "tracks" / TRACK_ID / "impl"
        impl_dir.mkdir(parents=True, exist_ok=True)
        (impl_dir / "signal.py").write_text(
            "from ..experiments.EXP_001 import main  # violation\n"
        )
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_rule1_latest_exp_not_in_track_log(self, fake_project):
        make_research_project(fake_project)
        exp_dir = fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "experiments"
        (exp_dir / "EXP_002.md").write_text(
            "# EXP_002\n\n## Goal\n第二次实验\n\n## Method\n"
            "- 数据源: infra_data_v1.load_daily_bars\n"
            "- 时间窗: 2021-01-01 至 2023-12-31\n"
            "- 随机种子: seed=42\n"
            "- 对照组: 无对照组\n\n"
            "## Preflight Check\n"
            "**最小冒烟检查**: 30s 内跑完，并打印 sharpe\n\n"
            "**输出契约**: stdout 至少包含 sharpe\n\n"
            "**本次不做**: 不抽象到 impl/\n\n"
            "## Expected Signal\n夏普>1.0\n\n## Result\n夏普: 1.1\n\n## Conclusion\n**结论**: 支持假设\n"
        )
        py_dir = fake_project / "src" / "tracks" / TRACK_ID / "experiments"
        (py_dir / "EXP_002.py").write_text("def main():\n    print('EXP_002')\n\nif __name__ == '__main__':\n    main()\n")
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_rule2_smoke_script_error(self, fake_project):
        make_research_project(fake_project)
        script = fake_project / "src" / "tracks" / TRACK_ID / "experiments" / "EXP_001.py"
        script.write_text("raise RuntimeError('boom')\n")
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_import_from_other_track(self, fake_project):
        """Rule 5 must catch cross-track imports too (scan all of src/)."""
        make_research_project(fake_project)
        other_dir = fake_project / "src" / "tracks" / "research_other" / "impl"
        other_dir.mkdir(parents=True, exist_ok=True)
        (other_dir / "use_exp.py").write_text(
            f"from tracks.{TRACK_ID}.experiments.EXP_001 import main\n"
        )
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_rule4_invalid_locked_contract(self, fake_project):
        make_research_project(fake_project, lock_infra=True)
        contracts = fake_project / "src" / "infra_data_v1" / "contracts.yaml"
        contracts.write_text("source: [broken\n")
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_rule1_no_exp_entry_in_log(self, fake_project):
        """Rule 1: TRACK_LOG.md without EXP_ data rows fails."""
        make_research_project(fake_project)
        log_path = fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "TRACK_LOG.md"
        log_path.write_text(
            "# TRACK_LOG\n\n**研究轮次**: cycle_1\n\n## Experiments\n\n| ID | Date | Goal | Conclusion | Link |\n"
            "|---|---|---|---|---|\n"  # header only, no EXP_ rows
        )
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_rule1_wrong_cycle_in_track_log(self, fake_project):
        make_research_project(fake_project)
        log_path = fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "TRACK_LOG.md"
        log_path.write_text(
            "# TRACK_LOG\n\n**研究轮次**: cycle_2\n\n## Experiments\n\n"
            "| EXP_001 | 2026-04-20 | 测试动量因子 | 支持 | [EXP_001.md](experiments/EXP_001.md) |\n"
            "\n## Evidence Summary\n\n- EXP_001: 测试\n",
            encoding="utf-8",
        )
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_rule3_missing_seed_in_method(self, fake_project):
        """Rule 3: EXP_NNN.md Method section missing seed/time/data fails."""
        make_research_project(fake_project)
        exp_md = (fake_project / "prae" / "phases" / PHASE / "tracks" /
                  TRACK_ID / "experiments" / "EXP_001.md")
        exp_md.write_text(
            "# EXP_001\n\n## Goal\n测试动量因子\n\n## Method\n"
            "- 动量窗口: 20日\n\n"  # missing seed, time range, data source
            "## Preflight Check\n"
            "**最小冒烟检查**: 30s 内跑完，并打印 sharpe\n\n"
            "**输出契约**: stdout 至少包含 sharpe\n\n"
            "## Expected Signal\n夏普>1.0\n\n"
            "## Result\n夏普: 1.2\n\n## Conclusion\n**结论**: 支持假设\n"
        )
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_rule3_missing_preflight_section(self, fake_project):
        make_research_project(fake_project)
        exp_md = (fake_project / "prae" / "phases" / PHASE / "tracks" /
                  TRACK_ID / "experiments" / "EXP_001.md")
        exp_md.write_text(
            "# EXP_001\n\n## Goal\n测试动量因子\n\n## Method\n"
            "- 数据源: infra_data_v1.load_daily_bars\n"
            "- 时间窗: 2020-01-01 至 2023-12-31\n"
            "- 随机种子: seed=42\n"
            "- 对照组: 无对照组\n\n"
            "## Expected Signal\n夏普>1.0\n\n"
            "## Result\n夏普: 1.2\n\n## Conclusion\n**结论**: 支持假设\n"
        )
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_fail_rule3_missing_expected_signal_section(self, fake_project):
        make_research_project(fake_project)
        exp_md = (fake_project / "prae" / "phases" / PHASE / "tracks" /
                  TRACK_ID / "experiments" / "EXP_001.md")
        exp_md.write_text(
            "# EXP_001\n\n## Goal\n测试动量因子\n\n## Method\n"
            "- 数据源: infra_data_v1.load_daily_bars\n"
            "- 时间窗: 2020-01-01 至 2023-12-31\n"
            "- 随机种子: seed=42\n"
            "- 对照组: 无对照组\n\n"
            "## Preflight Check\n"
            "**最小冒烟检查**: 30s 内跑完，并打印 sharpe\n\n"
            "**输出契约**: stdout 至少包含 sharpe\n\n"
            "**本次不做**: 不抽象到 impl/\n\n"
            "## Result\n夏普: 1.2\n\n## Conclusion\n**结论**: 支持假设\n"
        )
        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False
