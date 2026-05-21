"""Unit tests for record_result.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

TOOL = Path(__file__).parent.parent.parent / "tools" / "record_result.py"
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


def prepare_research_project(base: Path, *, complete: bool, phase: str = PHASE) -> None:
    registry_path = base / "prae" / "track_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["current_phase"] = phase
    for track in registry["tracks"]:
        if track["id"] == TRACK_ID:
            track["state"] = "EXPLORING"
            track["experiments"] = 1
            track["evidence_summary"] = None
    registry_path.write_text(
        yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    track_dir = base / "prae" / "phases" / phase / "tracks" / TRACK_ID
    exp_dir = track_dir / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)
    (track_dir / "TRACK_LOG.md").write_text(
        "\n".join([
            f"# 轨道日志：{TRACK_ID}",
            "",
            f"**轨道 ID**: `{TRACK_ID}`",
            "**类型**: research",
            f"**当前阶段**: {phase}",
            "**研究轮次**: cycle_1",
            "**创建日期**: 2026-04-20",
            "",
            "---",
            "",
            "## State",
            "",
            "**当前状态**: EXPLORING",
            "**依赖的轨道**:",
            "- `infra_data_v1`",
            "",
            "---",
            "",
            "## Experiments",
            "",
            "| EXP ID | 日期 | 目的 | 结论 | 链接 |",
            "|--------|------|------|------|------|",
            "| — | — | 尚无实验记录 | — | — |",
            "",
            "---",
            "",
            "## Evidence Summary",
            "",
            "- 暂无实验记录。",
            "",
            "---",
            "",
        ]),
        encoding="utf-8",
    )

    if complete:
        exp_md = (
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
            "## Conclusion\n**结论**: 支持假设\n\n建议 state 变更: EXPLORING → ACTIVE\n"
        )
    else:
        exp_md = (
            "# EXP_001\n\n## Goal\n测试动量因子\n\n## Method\n"
            "- 数据源: infra_data_v1.load_daily_bars\n"
            "- 时间窗: 2020-01-01 至 2023-12-31\n"
            "- 随机种子: seed=42\n"
            "- 对照组: 无对照组\n\n"
            "## Result\n{{粘贴实验关键输出}}\n\n"
            "## Conclusion\n支持 / 证伪 / 部分支持 假设\n"
        )
    (exp_dir / "EXP_001.md").write_text(exp_md, encoding="utf-8")


def set_phase_override(project_dir: Path, phase: str) -> None:
    registry_path = project_dir / "prae" / "track_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["current_phase_override"] = phase
    registry_path.write_text(
        yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


class TestRecordResult:
    def test_record_result_updates_track_log_and_registry(self, fake_project):
        prepare_research_project(fake_project, complete=True)

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--exp-id", "EXP_001"],
        )

        assert rc == 0, out
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["evidence_summary"] == "EXP_001: 支持假设"

        log_content = (
            fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "TRACK_LOG.md"
        ).read_text(encoding="utf-8")
        assert "| EXP_001 |" in log_content
        assert "结论：支持假设。" in log_content
        assert "建议 EXPLORING → ACTIVE" in log_content
        assert "EXP_001 结果已记录，待人工批准" in log_content

    def test_record_result_rejects_incomplete_exp(self, fake_project):
        prepare_research_project(fake_project, complete=False)

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--exp-id", "EXP_001"],
        )

        assert rc == 1, out
        assert out["passed"] is False

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["evidence_summary"] is None

    def test_record_result_rejects_research_track_in_phase_0(self, fake_project):
        prepare_research_project(fake_project, complete=True, phase="phase_00_infra")

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--exp-id", "EXP_001"],
        )

        assert rc == 1, out
        assert out["passed"] is False
        assert "当前阶段允许记录实验结果" in out["summary"]

    def test_record_result_respects_current_phase_override(self, fake_project):
        prepare_research_project(fake_project, complete=True, phase=PHASE)
        set_phase_override(fake_project, "phase_00_infra")

        phase0_track_dir = fake_project / "prae" / "phases" / "phase_00_infra" / "tracks" / TRACK_ID
        phase0_exp_dir = phase0_track_dir / "experiments"
        phase0_exp_dir.mkdir(parents=True, exist_ok=True)
        (phase0_track_dir / "TRACK_LOG.md").write_text(
            (fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "TRACK_LOG.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (phase0_exp_dir / "EXP_001.md").write_text(
            (fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "experiments" / "EXP_001.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        rc, out = run_tool(
            str(fake_project),
            ["--track-id", TRACK_ID, "--exp-id", "EXP_001"],
        )

        assert rc == 1, out
        assert out["passed"] is False
        assert out["data"]["recorded"] is False
        assert "当前阶段允许记录实验结果" in out["summary"]
