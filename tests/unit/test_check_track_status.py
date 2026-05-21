"""Unit tests for check_track_status.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).parent.parent.parent / "tools" / "check_track_status.py"


def run_tool(project_dir: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--project-dir", project_dir],
        capture_output=True, text=True
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


class TestCheckTrackStatus:
    def test_valid_project_exploring(self, fake_project):
        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["passed"] is True

    def test_locked_project_with_valid_files(self, locked_infra_project):
        rc, out = run_tool(str(locked_infra_project))
        assert rc == 0
        assert out["passed"] is True

    def test_missing_registry(self, tmp_path):
        rc, out = run_tool(str(tmp_path))
        assert rc == 2  # file missing error

    def test_invalid_state_reported(self, fake_project):
        import yaml
        reg = fake_project / "prae" / "track_registry.yaml"
        with open(reg) as f:
            r = yaml.safe_load(f)
        r["tracks"][0]["state"] = "INVALID_STATE"
        with open(reg, "w") as f:
            yaml.dump(r, f, allow_unicode=True)

        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_locked_without_contracts_fails(self, fake_project):
        import yaml
        reg = fake_project / "prae" / "track_registry.yaml"
        with open(reg) as f:
            r = yaml.safe_load(f)
        for t in r["tracks"]:
            if t["id"] == "infra_data_v1":
                t["state"] = "LOCKED"
                t["contracts"] = None
                t["module_spec"] = None
        with open(reg, "w") as f:
            yaml.dump(r, f, allow_unicode=True)

        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False
