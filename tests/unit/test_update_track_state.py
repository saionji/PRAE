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
            track["evidence_summary"] = "old summary"
            track["concluded_at"] = None
            track["merged_into"] = None

    if add_merge_target:
        registry["tracks"].append({
            "id": "research_strategy_reversal",
            "type": "research",
            "state": "ACTIVE",
            "src": "src/tracks/research_strategy_reversal/",
            "hypothesis": "Reversal factor is effective on A-share ETFs",
            "depends_on": ["infra_data_v1"],
            "experiments": 1,
            "evidence_summary": "candidate lead track",
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
            f"# Track Log: {TRACK_ID}",
            "",
            f"**Track ID**: `{TRACK_ID}`",
            "**Type**: research",
            f"**Current Phase**: {PHASE}",
            "**Research Cycle**: cycle_1",
            "**Created**: 2026-04-20",
            "",
            "---",
            "",
            "## State",
            "",
            f"**Current State**: {state}",
            "**Depends On**:",
            "- `infra_data_v1`",
            "",
            "---",
            "",
            "## Experiments",
            "",
            "| EXP ID | Date | Purpose | Conclusion | Link |",
            "|--------|------|------|------|------|",
            "| EXP_001 | 2026-04-20 | Momentum factor test | Supports | [EXP_001.md](experiments/EXP_001.md) |",
            "",
            "---",
            "",
            "## Evidence Summary",
            "",
            "- 2026-04-20 EXP_001: positive signal.",
            "",
            "---",
            "",
            "## Decision Log",
            "",
            "| Date | Change | Advisor | Approver | Reason |",
            "|------|------|--------|--------|------|",
            f"| 2026-04-20 | Created ({state}) | AI | — | Test initialization |",
            "",
        ]),
        encoding="utf-8",
    )

    exp_dir = track_dir / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)
    exp_md_content = (
        "# EXP_001\n\n## Goal\nTest the momentum factor\n\n## Method\n"
        "- Data Source: infra_data_v1.load_daily_bars\n"
        "- Time Window: 2020-01-01 to 2023-12-31\n"
        "- Random Seed: seed=42\n"
        "- Control Group: no control group\n\n"
        "## Preflight Check\n"
        "**Minimal Smoke Check**: finishes within 30s and prints sharpe\n\n"
        "**Output Contract**: stdout contains at least sharpe\n\n"
        "**Out of Scope This Time**: do not abstract into impl/\n\n"
        "## Expected Signal\nSharpe > 1.0\n\n"
        "## Result\nSharpe: 1.2\n\n"
        "## Conclusion\n**Conclusion**: supports the hypothesis\n"
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
                "--approver", "maintainer",
                "--approved-at", "2026-04-20",
                "--exp-id", "EXP_001",
                "--reason", "EXP_001 shows a positive signal",
                "--summary", "EXP_001: Sharpe 1.2, supports ACTIVE",
            ],
        )

        assert rc == 0, out
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["state"] == "ACTIVE"
        assert track["evidence_summary"] == "EXP_001: Sharpe 1.2, supports ACTIVE"
        assert track["concluded_at"] is None
        assert track["merged_into"] is None

        log_content = (
            fake_project / "prae" / "phases" / PHASE / "tracks" / TRACK_ID / "TRACK_LOG.md"
        ).read_text(encoding="utf-8")
        assert "**Current State**: ACTIVE" in log_content
        assert "| 2026-04-20 | EXPLORING → ACTIVE | AI | maintainer | EXP_001: EXP_001 shows a positive signal |" in log_content

    def test_exploring_to_killed_is_rejected(self, fake_project):
        prepare_track_project(fake_project, state="EXPLORING", lock_infra=True)

        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--to-state", "KILLED",
                "--approver", "maintainer",
                "--reason", "negative signal",
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
                "--approver", "maintainer",
                "--reason", "overlaps with the lead track",
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
                "--approver", "maintainer",
                "--approved-at", "2026-04-20",
                "--reason", "evidence complements the reversal track, merging forward",
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
                "--approver", "maintainer",
                "--reason", "validation complete",
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
                "--approver", "maintainer",
                "--reason", "positive signal appeared",
            ],
        )

        assert rc == 1
        assert out["passed"] is False

