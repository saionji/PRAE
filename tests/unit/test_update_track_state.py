"""Unit tests for update_track_state.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

TOOL = Path(__file__).parent.parent.parent / "tools" / "update_track_state.py"
TRACK_ID = "research_strategy_momentum"
PHASE = "phase_01_research"


def run_tool(project_dir: str, extra_args: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--project-dir", project_dir] + extra_args,
        capture_output=True,
        text=True,
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


def prepare_track_project(
    base: Path,
    *,
    state: str,
    lock_infra: bool = True,
    with_valid_research_gate: bool = True,
    add_merge_target: bool = False,
) -> Path:
    reg = base / "prae" / "track_registry.yaml"
    registry = yaml.safe_load(reg.read_text(encoding="utf-8"))
    registry["current_phase"] = PHASE

    for track in registry["tracks"]:
        if track["id"] == "infra_data_v1":
            if lock_infra:
                track["state"] = "LOCKED"
                track["contracts"] = "src/infra_data_v1/contracts.yaml"
                track["module_spec"] = "src/infra_data_v1/MODULE_SPEC.md"
                track["locked_at"] = "2026-04-20"
            else:
                track["state"] = "EXPLORING"
                track["contracts"] = None
                track["module_spec"] = None
                track["locked_at"] = None
        if track["id"] == TRACK_ID:
            track["state"] = state
            track["experiments"] = 1
            track["evidence_summary"] = "旧摘要"
            track["concluded_at"] = None
            track["merged_into"] = None

    if add_merge_target:
        registry["tracks"].append({
            "id": "research_strategy_reversal",
            "type": "research",
            "state": "ACTIVE",
            "src": "src/tracks/research_strategy_reversal/",
            "hypothesis": "反转因子在A股ETF上有效",
            "depends_on": ["infra_data_v1"],
            "experiments": 1,
            "evidence_summary": "候选主轨道",
            "concluded_at": None,
            "merged_into": None,
        })

    reg.write_text(
        yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    if lock_infra:
        infra_dir = base / "src" / "infra_data_v1"
        infra_dir.mkdir(parents=True, exist_ok=True)
        (infra_dir / "contracts.yaml").write_text("exports:\n  - load_daily_bars\n", encoding="utf-8")
        (infra_dir / "MODULE_SPEC.md").write_text("# MODULE_SPEC\n\n## Exports\n- load_daily_bars\n", encoding="utf-8")

    track_dir = base / "prae" / "phases" / PHASE / "tracks" / TRACK_ID
    track_dir.mkdir(parents=True, exist_ok=True)
    (track_dir / "TRACK_LOG.md").write_text(
        "\n".join([
            f"# 轨道日志：{TRACK_ID}",
            "",
            f"**轨道 ID**: `{TRACK_ID}`",
            "**类型**: research",
            f"**当前阶段**: {PHASE}",
            "**研究轮次**: cycle_1",
            "**创建日期**: 2026-04-20",
            "",
            "---",
            "",
            "## State",
            "",
            f"**当前状态**: {state}",
            "**依赖的轨道**:",
            "- `infra_data_v1`",
            "",
            "---",
            "",
            "## Experiments",
            "",
            "| EXP ID | 日期 | 目的 | 结论 | 链接 |",
            "|--------|------|------|------|------|",
            "| EXP_001 | 2026-04-20 | 动量因子测试 | 支持 | [EXP_001.md](experiments/EXP_001.md) |",
            "",
            "---",
            "",
            "## Evidence Summary",
            "",
            "- 2026-04-20 EXP_001: 正向信号。",
            "",
            "---",
            "",
            "## Decision Log",
            "",
            "| 日期 | 变更 | 建议者 | 批准者 | 原因 |",
            "|------|------|--------|--------|------|",
            f"| 2026-04-20 | 创建（{state}) | AI | — | 测试初始化 |",
            "",
        ]),
        encoding="utf-8",
    )

    exp_dir = track_dir / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)
    exp_md_content = (
        "# EXP_001\n\n## Goal\n测试动量因子\n\n## Method\n"
        "- 数据源: infra_data_v1.load_daily_bars\n"
        "- 时间窗: 2020-01-01 至 2023-12-31\n"
        "- 随机种子: seed=42\n"
        "- 对照组: 无对照组\n\n"
        "## Preflight Check\n"
        "**最小冒烟检查**: 30s 内跑完，并打印 sharpe\n\n"
        "**输出契约**: stdout 至少包含 sharpe\n\n"
        "**本次不做**: 不抽象到 impl/\n\n"
        "## Expected Signal\n夏普>1.0\n\n"
        "## Result\n夏普: 1.2\n\n"
        "## Conclusion\n**结论**: 支持假设\n"
    )
    if not with_valid_research_gate:
        exp_md_content = exp_md_content.replace("## Preflight Check\n", "")
    (exp_dir / "EXP_001.md").write_text(exp_md_content, encoding="utf-8")

    py_dir = base / "src" / "tracks" / TRACK_ID / "experiments"
    py_dir.mkdir(parents=True, exist_ok=True)
    if with_valid_research_gate:
        (py_dir / "EXP_001.py").write_text(
            "def main():\n    print('ok')\n\nif __name__ == '__main__':\n    main()\n",
            encoding="utf-8",
        )
    else:
        (py_dir / "EXP_001.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")

    return base


class TestUpdateTrackState:
    def test_exploring_to_active_updates_registry_and_track_log(self, fake_project):
        prepare_track_project(fake_project, state="EXPLORING", lock_infra=True)

        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--to-state", "ACTIVE",
                "--approver", "saionji",
                "--approved-at", "2026-04-20",
                "--exp-id", "EXP_001",
                "--reason", "EXP_001 显示正向信号",
                "--summary", "EXP_001: 夏普1.2，支持 ACTIVE",
            ],
        )

        assert rc == 0, out
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["state"] == "ACTIVE"
        assert track["evidence_summary"] == "EXP_001: 夏普1.2，支持 ACTIVE"
        assert track["concluded_at"] is None
        assert track["merged_into"] is None

        log_content = (
            fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "TRACK_LOG.md"
        ).read_text(encoding="utf-8")
        assert "**当前状态**: ACTIVE" in log_content
        assert "| 2026-04-20 | EXPLORING → ACTIVE | AI | saionji | EXP_001: EXP_001 显示正向信号 |" in log_content

    def test_exploring_to_killed_is_rejected(self, fake_project):
        prepare_track_project(fake_project, state="EXPLORING", lock_infra=True)

        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--to-state", "KILLED",
                "--approver", "saionji",
                "--reason", "负向信号",
            ],
        )

        assert rc == 1
        assert out["passed"] is False

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["state"] == "EXPLORING"

    def test_active_to_merged_requires_target(self, fake_project):
        prepare_track_project(fake_project, state="ACTIVE", lock_infra=True)

        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--to-state", "MERGED",
                "--approver", "saionji",
                "--reason", "与主轨道重合",
            ],
        )

        assert rc == 1
        assert out["passed"] is False

    def test_active_to_merged_records_terminal_metadata(self, fake_project):
        prepare_track_project(
            fake_project,
            state="ACTIVE",
            lock_infra=True,
            add_merge_target=True,
        )

        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--to-state", "MERGED",
                "--approver", "saionji",
                "--approved-at", "2026-04-20",
                "--reason", "与反转轨道证据互补，合并推进",
                "--merged-into", "research_strategy_reversal",
            ],
        )

        assert rc == 0, out
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["state"] == "MERGED"
        assert track["merged_into"] == "research_strategy_reversal"
        assert track["concluded_at"] == "2026-04-20"

    def test_active_to_graduated_requires_research_gate(self, fake_project):
        prepare_track_project(fake_project, state="ACTIVE", lock_infra=True, with_valid_research_gate=False)

        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--to-state", "GRADUATED",
                "--approver", "saionji",
                "--reason", "验证完成",
            ],
        )

        assert rc == 1
        assert out["passed"] is False

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["state"] == "ACTIVE"
        assert track["concluded_at"] is None

    def test_activate_requires_locked_dependencies(self, fake_project):
        prepare_track_project(fake_project, state="EXPLORING", lock_infra=False)

        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--to-state", "ACTIVE",
                "--approver", "saionji",
                "--reason", "正向信号出现",
            ],
        )

        assert rc == 1
        assert out["passed"] is False

