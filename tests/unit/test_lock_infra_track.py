"""Unit tests for lock_infra_track.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

TOOL = Path(__file__).parent.parent.parent / "tools" / "lock_infra_track.py"
TRACK_ID = "infra_data_v1"


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


def prepare_infra_artifacts(base: Path) -> None:
    infra_dir = base / "src" / TRACK_ID
    infra_dir.mkdir(parents=True, exist_ok=True)
    (infra_dir / "contracts.yaml").write_text("exports:\n  - load_daily_bars\n", encoding="utf-8")
    (infra_dir / "MODULE_SPEC.md").write_text("# MODULE_SPEC\n\n## Exports\n- load_daily_bars\n", encoding="utf-8")


class TestLockInfraTrack:
    def test_lock_infra_infers_paths_and_updates_registry_and_track_log(self, fake_project):
        prepare_infra_artifacts(fake_project)

        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--approver", "maintainer",
                "--approved-at", "2026-04-20",
                "--reason", "PDAE M3 passed",
            ],
        )

        assert rc == 0, out
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text(encoding="utf-8"))
        track = next(t for t in registry["tracks"] if t["id"] == TRACK_ID)
        assert track["state"] == "LOCKED"
        assert track["locked_at"] == "2026-04-20"
        assert track["contracts"] == "src/infra_data_v1/contracts.yaml"
        assert track["module_spec"] == "src/infra_data_v1/MODULE_SPEC.md"

        log_content = (
            fake_project
            / "prae"
            / "phases"
            / "phase_00_infra"
            / "tracks"
            / TRACK_ID
            / "TRACK_LOG.md"
        ).read_text(encoding="utf-8")
        assert "**Current State**: LOCKED" in log_content
        assert "| 2026-04-20 | EXPLORING → LOCKED | AI | maintainer | PDAE M3 passed |" in log_content

    def test_lock_infra_rejects_non_phase_0(self, fake_project):
        prepare_infra_artifacts(fake_project)

        registry_path = fake_project / "prae" / "track_registry.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        registry["current_phase"] = "phase_01_research"
        registry_path.write_text(
            yaml.dump(registry, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--approver", "maintainer",
                "--reason", "PDAE M3 passed",
            ],
        )

        assert rc == 1, out
        assert out["passed"] is False

    def test_lock_infra_requires_contract_files(self, fake_project):
        rc, out = run_tool(
            str(fake_project),
            [
                "--track-id", TRACK_ID,
                "--approver", "maintainer",
                "--reason", "PDAE M3 passed",
            ],
        )

        assert rc == 1, out
        assert out["passed"] is False
