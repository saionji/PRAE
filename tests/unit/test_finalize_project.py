"""Unit tests for finalize_project.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import yaml

from tests.unit.test_generate_conclusion import make_phase3_project
from tests.unit.test_graduate_track import run_tool as run_graduate_tool

TOOL = Path(__file__).parent.parent.parent / "tools" / "finalize_project.py"


def run_tool(project_dir: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--project-dir", project_dir],
        capture_output=True,
        text=True,
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


def approve_conclusion(conclusion_path: Path, decision: str) -> None:
    content = conclusion_path.read_text(encoding="utf-8")
    content = content.replace("APPROVED: pending", "APPROVED: yes")
    content = content.replace("DECISION: ", f"DECISION: {decision}")
    content = content.replace("APPROVER: ", "APPROVER: maintainer")
    content = content.replace("APPROVED_AT: ", "APPROVED_AT: 2026-04-20")
    conclusion_path.write_text(content, encoding="utf-8")


class TestFinalizeProject:
    def test_pending_conclusion_fails(self, fake_project):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        write_conclusion(fake_project)

        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_finalize_archived_records_metadata(self, fake_project):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        payload = write_conclusion(fake_project)
        approve_conclusion(Path(payload["data"]["path"]), "ARCHIVED")

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text())
        assert registry["project_decision"] == "ARCHIVED"
        assert registry["project_approver"] == "maintainer"
        assert registry["project_decided_at"] == "2026-04-20"
        assert registry["archived_at"] == "2026-04-20"

    def test_finalize_graduated_to_pdae_records_metadata(self, fake_project, tmp_path):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        pdae_project = tmp_path / "pdae-project"
        pdae_project.mkdir()
        run_graduate_tool(str(fake_project), "research_strategy_momentum", str(pdae_project))
        payload = write_conclusion(fake_project)
        approve_conclusion(Path(payload["data"]["path"]), "GRADUATED_TO_PDAE")

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["passed"] is True

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text())
        assert registry["project_decision"] == "GRADUATED_TO_PDAE"
        assert registry["project_approver"] == "maintainer"
        assert registry["project_decided_at"] == "2026-04-20"

    def test_finalize_continue_is_rejected(self, fake_project):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        payload = write_conclusion(fake_project)
        approve_conclusion(Path(payload["data"]["path"]), "CONTINUE")

        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False
