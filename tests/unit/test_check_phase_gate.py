"""Unit tests for check_phase_gate.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).parent.parent.parent / "tools" / "check_phase_gate.py"
PHASE_CHECKLIST_ITEMS = {
    0: [
        "所有 type=infrastructure 的轨道 state = LOCKED",
        "每条 LOCKED 轨道都有 contracts.yaml",
        "每条 LOCKED 轨道都有 MODULE_SPEC.md",
        "每条 LOCKED 轨道都通过 PDAE M3 门控（记录在 TRACK_LOG.md）",
        "check_contracts.py 对所有基础设施契约通过",
    ],
    1: [
        "≥1 条研究轨道 state = ACTIVE（有正向信号）",
        "所有仍 EXPLORING 的研究轨道有明确去留建议（继续 / KILL / 合并）",
        "每条 ACTIVE 轨道通过 Research Gate 检查",
    ],
    2: [
        "所有原 ACTIVE 研究轨道有明确终态建议",
        "至少一条轨道判定 GRADUATED（否则考虑整体 KILL 项目）",
        "所有 GRADUATED 候选通过 Research Gate 和 Contracts Gate",
        "所有 GRADUATED 候选有 `TRACK_LOG.md` 的最终结论段落",
    ],
}


def run_tool(project_dir: str, extra_args: list[str] | None = None) -> tuple[int, dict]:
    args = [sys.executable, str(TOOL), "--project-dir", project_dir] + (extra_args or [])
    proc = subprocess.run(args, capture_output=True, text=True)
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


def set_current_phase(project_dir: Path, phase_name: str) -> None:
    import yaml

    reg = project_dir / "prae" / "track_registry.yaml"
    with open(reg) as f:
        registry = yaml.safe_load(f)
    registry["current_phase"] = phase_name
    with open(reg, "w") as f:
        yaml.dump(registry, f, allow_unicode=True)


def set_phase_override(project_dir: Path, phase_name: str) -> None:
    import yaml

    reg = project_dir / "prae" / "track_registry.yaml"
    with open(reg) as f:
        registry = yaml.safe_load(f)
    registry["current_phase_override"] = phase_name
    with open(reg, "w") as f:
        yaml.dump(registry, f, allow_unicode=True)


def make_valid_phase_gate_doc(from_phase: int, to_phase: int, target_phase: str, approved: str,
                              *, drop_checklist_item: str | None = None,
                              unchecked_items: set[str] | None = None,
                              cycle_label: str = "cycle_1") -> str:
    approved_at = "2026-04-20" if approved == "yes" else ""
    approver = "saionji" if approved == "yes" else ""
    unchecked_items = unchecked_items or set()
    checklist_items = [
        item for item in PHASE_CHECKLIST_ITEMS[from_phase]
        if item != drop_checklist_item
    ]
    checklist = "\n".join(
        f"- [{' ' if item in unchecked_items else 'x'}] {item}" for item in checklist_items
    )
    return (
        f"# Phase {from_phase} → Phase {to_phase} 门控分析\n\n"
        f"**研究轮次**: {cycle_label}\n"
        f"**生成日期**: 2026-04-20\n"
        f"**生成者**: AI（分析者角色）\n"
        f"**目标阶段**: {target_phase}\n\n"
        "## 1. 当前阶段状态\n"
        "- infra_data_v1: LOCKED\n\n"
        "## 2. 门控条件逐项检查\n"
        f"{checklist}\n\n"
        "## 3. 证据摘要\n"
        "- 关键证据\n\n"
        "## 4. 风险与未决项\n"
        "- 暂无\n\n"
        "## 5. 建议\n"
        "**推荐动作**: 推进\n"
        "**理由**: 条件满足\n\n"
        "## 6. 待人工批准\n"
        f"APPROVED: {approved}\n"
        f"APPROVER: {approver}\n"
        f"APPROVED_AT: {approved_at}\n"
        "COMMENT: \n"
    )


def make_phase1_active_track(project_dir: Path, *, with_research_artifacts: bool) -> None:
    import yaml

    reg = project_dir / "prae" / "track_registry.yaml"
    with open(reg) as f:
        registry = yaml.safe_load(f)
    registry["current_phase"] = "phase_01_research"
    for track in registry["tracks"]:
        if track["id"] == "research_strategy_momentum":
            track["state"] = "ACTIVE"
            track["experiments"] = 1
    with open(reg, "w") as f:
        yaml.dump(registry, f, allow_unicode=True)

    track_dir = project_dir / "prae" / "phases" / "phase_01_research" / "tracks" / "research_strategy_momentum"
    track_dir.mkdir(parents=True, exist_ok=True)
    (track_dir / "TRACK_LOG.md").write_text(
        "# TRACK_LOG\n\n**研究轮次**: cycle_1\n\n## Experiments\n\n| EXP_001 | 2026-04-20 | test | ok | [EXP_001.md](experiments/EXP_001.md) |\n"
        "\n## Evidence Summary\n\n- 2026-04-20 EXP_001: 正向信号\n"
        "\n## Decision Log\n\n| 2026-04-20 | EXPLORING → ACTIVE | AI | saionji | EXP_001 信号正向 |\n"
    )

    if not with_research_artifacts:
        return

    exp_dir = track_dir / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "EXP_001.md").write_text(
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
        "## Result\n夏普: 1.2\n\n## Conclusion\n**结论**: 支持假设\n"
    )

    py_dir = project_dir / "src" / "tracks" / "research_strategy_momentum" / "experiments"
    py_dir.mkdir(parents=True, exist_ok=True)
    (py_dir / "EXP_001.py").write_text(
        "def main():\n    print('ok')\n\nif __name__ == '__main__':\n    main()\n"
    )


def make_phase2_graduated_track(project_dir: Path) -> None:
    import yaml

    reg = project_dir / "prae" / "track_registry.yaml"
    with open(reg) as f:
        registry = yaml.safe_load(f)
    registry["current_phase"] = "phase_02_validation"
    for track in registry["tracks"]:
        if track["id"] == "research_strategy_momentum":
            track["state"] = "GRADUATED"
            track["experiments"] = 1
            track["concluded_at"] = "2026-04-20"
    with open(reg, "w") as f:
        yaml.dump(registry, f, allow_unicode=True)

    track_dir = project_dir / "prae" / "phases" / "phase_02_validation" / "tracks" / "research_strategy_momentum"
    track_dir.mkdir(parents=True, exist_ok=True)
    (track_dir / "TRACK_LOG.md").write_text(
        "# TRACK_LOG\n\n**研究轮次**: cycle_1\n\n## Experiments\n\n| EXP_001 | 2026-04-20 | test | graduated | [EXP_001.md](experiments/EXP_001.md) |\n"
        "\n## Evidence Summary\n\n- 2026-04-20 EXP_001: 正向信号\n"
        "\n## 最终结论\n\nGRADUATED — 信号稳定，移交 PDAE。\n"
    )

    exp_dir = track_dir / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "EXP_001.md").write_text(
        "# EXP_001\n\n## Goal\n验证动量因子\n\n## Method\n"
        "- 数据源: infra_data_v1.load_daily_bars\n"
        "- 时间窗: 2020-01-01 至 2023-12-31\n"
        "- 随机种子: seed=42\n"
        "- 对照组: 无对照组\n\n"
        "## Preflight Check\n"
        "**最小冒烟检查**: 30s 内跑完，并打印 sharpe\n\n"
        "**输出契约**: stdout 至少包含 sharpe\n\n"
        "**本次不做**: 不抽象到 impl/\n\n"
        "## Expected Signal\n夏普>1.0\n\n"
        "## Result\n夏普: 1.2\n\n## Conclusion\n**结论**: 支持假设\n"
    )

    py_dir = project_dir / "src" / "tracks" / "research_strategy_momentum" / "experiments"
    py_dir.mkdir(parents=True, exist_ok=True)
    (py_dir / "EXP_001.py").write_text(
        "def main():\n    print('validated')\n\nif __name__ == '__main__':\n    main()\n"
    )


class TestPhaseGate0to1:
    def test_exploring_infra_fails(self, fake_project):
        rc, out = run_tool(str(fake_project), ["--phase", "0"])
        assert rc == 1
        assert out["passed"] is False

    def test_locked_infra_passes(self, locked_infra_project):
        rc, out = run_tool(str(locked_infra_project), ["--phase", "0"])
        assert rc == 0
        assert out["passed"] is True

    def test_missing_registry_is_error(self, tmp_path):
        rc, out = run_tool(str(tmp_path), ["--phase", "0"])
        assert rc == 2

    def test_override_blocks_regular_phase_gate(self, fake_project):
        set_phase_override(fake_project, "phase_00_infra")

        rc, out = run_tool(str(fake_project))

        assert rc == 2, out
        assert "current_phase_override" in out.get("summary", out.get("stderr", ""))


class TestPhaseGate1to2:
    def test_no_active_fails(self, fake_project):
        rc, out = run_tool(str(fake_project), ["--phase", "1"])
        assert rc == 1
        assert out["passed"] is False

    def test_with_active_track_passes(self, fake_project):
        make_phase1_active_track(fake_project, with_research_artifacts=True)
        rc, out = run_tool(str(fake_project), ["--phase", "1"])
        assert rc == 0
        assert out["passed"] is True

    def test_active_track_without_research_gate_fails(self, fake_project):
        make_phase1_active_track(fake_project, with_research_artifacts=False)
        rc, out = run_tool(str(fake_project), ["--phase", "1"])
        assert rc == 1
        assert out["passed"] is False


class TestPhaseGate2to3:
    def _make_phase2_project(self, fake_project):
        import yaml
        reg = fake_project / "prae" / "track_registry.yaml"
        with open(reg) as f:
            r = yaml.safe_load(f)
        r["current_phase"] = "phase_02_validation"
        for t in r["tracks"]:
            if t["id"] == "research_strategy_momentum":
                t["state"] = "GRADUATED"
                t["concluded_at"] = "2026-04-20"
        with open(reg, "w") as f:
            yaml.dump(r, f, allow_unicode=True)
        return fake_project

    def test_active_track_remaining_fails(self, fake_project):
        import yaml
        reg = fake_project / "prae" / "track_registry.yaml"
        with open(reg) as f:
            r = yaml.safe_load(f)
        r["current_phase"] = "phase_02_validation"
        for t in r["tracks"]:
            if t["id"] == "research_strategy_momentum":
                t["state"] = "ACTIVE"
        with open(reg, "w") as f:
            yaml.dump(r, f, allow_unicode=True)
        rc, out = run_tool(str(fake_project), ["--phase", "2"])
        assert rc == 1
        assert out["passed"] is False

    def test_no_graduated_fails(self, fake_project):
        import yaml
        reg = fake_project / "prae" / "track_registry.yaml"
        with open(reg) as f:
            r = yaml.safe_load(f)
        r["current_phase"] = "phase_02_validation"
        for t in r["tracks"]:
            if t["id"] == "research_strategy_momentum":
                t["state"] = "KILLED"
                t["concluded_at"] = "2026-04-20"
        with open(reg, "w") as f:
            yaml.dump(r, f, allow_unicode=True)
        rc, out = run_tool(str(fake_project), ["--phase", "2"])
        assert rc == 1
        assert out["passed"] is False

    def test_graduated_with_no_active_passes(self, fake_project):
        make_phase2_graduated_track(fake_project)
        rc, out = run_tool(str(fake_project), ["--phase", "2"])
        assert rc == 0
        assert out["passed"] is True


class TestCheckApproved:
    def test_pending_approval_fails(self, fake_project):
        gate_dir = fake_project / "prae" / "phases" / "phase_00_infra"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(0, 1, "phase_01_research", "pending")
        )
        rc, out = run_tool(str(fake_project), ["--check-approved"])
        assert rc == 1

    def test_yes_approval_passes(self, locked_infra_project):
        gate_dir = locked_infra_project / "prae" / "phases" / "phase_00_infra"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(0, 1, "phase_01_research", "yes")
        )
        rc, out = run_tool(str(locked_infra_project), ["--check-approved"])
        assert rc == 0

    def test_phase1_specific_checklist_passes(self, fake_project):
        make_phase1_active_track(fake_project, with_research_artifacts=True)
        set_current_phase(fake_project, "phase_01_research")
        gate_dir = fake_project / "prae" / "phases" / "phase_01_research"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(1, 2, "phase_02_validation", "yes")
        )
        rc, out = run_tool(str(fake_project), ["--check-approved"])
        assert rc == 0
        assert out["passed"] is True

    def test_phase2_specific_checklist_passes(self, fake_project):
        make_phase2_graduated_track(fake_project)
        set_current_phase(fake_project, "phase_02_validation")
        gate_dir = fake_project / "prae" / "phases" / "phase_02_validation"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(2, 3, "phase_03_conclusion", "yes")
        )
        rc, out = run_tool(str(fake_project), ["--check-approved"])
        assert rc == 0
        assert out["passed"] is True

    def test_invalid_structure_fails_even_if_approved(self, fake_project):
        gate_dir = fake_project / "prae" / "phases" / "phase_00_infra"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            "# Gate\n\nAPPROVED: yes\nAPPROVER: saionji\nAPPROVED_AT: 2026-04-20\n"
        )
        rc, out = run_tool(str(fake_project), ["--check-approved"])
        assert rc == 1
        assert out["passed"] is False

    def test_missing_phase_specific_checklist_fails(self, locked_infra_project):
        gate_dir = locked_infra_project / "prae" / "phases" / "phase_00_infra"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(
                0,
                1,
                "phase_01_research",
                "yes",
                drop_checklist_item="check_contracts.py 对所有基础设施契约通过",
            )
        )
        rc, out = run_tool(str(locked_infra_project), ["--check-approved"])
        assert rc == 1
        assert out["passed"] is False

    def test_checkbox_mismatch_with_actual_gate_fails(self, locked_infra_project):
        gate_dir = locked_infra_project / "prae" / "phases" / "phase_00_infra"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(
                0,
                1,
                "phase_01_research",
                "yes",
                unchecked_items={"每条 LOCKED 轨道都有 MODULE_SPEC.md"},
            )
        )
        rc, out = run_tool(str(locked_infra_project), ["--check-approved"])
        assert rc == 1
        assert out["passed"] is False

    def test_wrong_cycle_fails_even_if_approved(self, locked_infra_project):
        gate_dir = locked_infra_project / "prae" / "phases" / "phase_00_infra"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "PHASE_GATE.md").write_text(
            make_valid_phase_gate_doc(0, 1, "phase_01_research", "yes", cycle_label="cycle_2")
        )
        rc, out = run_tool(str(locked_infra_project), ["--check-approved"])
        assert rc == 1
        assert out["passed"] is False
