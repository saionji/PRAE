"""Unit tests for reopen_project.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import yaml

from tests.unit.test_generate_conclusion import make_phase3_project

TOOL = Path(__file__).parent.parent.parent / "tools" / "reopen_project.py"


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


def approve_continue(conclusion_path: Path) -> None:
    content = conclusion_path.read_text(encoding="utf-8")
    content = content.replace("APPROVED: pending", "APPROVED: yes")
    content = content.replace("DECISION: ", "DECISION: CONTINUE")
    content = content.replace("APPROVER: ", "APPROVER: saionji")
    content = content.replace("APPROVED_AT: ", "APPROVED_AT: 2026-04-20")
    content = content.replace("COMMENT: ", "COMMENT: reopen for new hypothesis")
    conclusion_path.write_text(content, encoding="utf-8")


def seed_previous_phase_artifacts(fake_project: Path) -> None:
    for phase_name, filenames in {
        "phase_01_research": ["PHASE_BRIEF.md", "PHASE_GATE.md"],
        "phase_02_validation": ["PHASE_BRIEF.md", "PHASE_GATE.md"],
        "phase_03_conclusion": ["PHASE_BRIEF.md"],
    }.items():
        phase_dir = fake_project / "prae" / "phases" / phase_name
        phase_dir.mkdir(parents=True, exist_ok=True)
        for filename in filenames:
            (phase_dir / filename).write_text(f"# {phase_name} {filename}\n", encoding="utf-8")


class TestReopenProject:
    def test_pending_conclusion_fails(self, fake_project):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        write_conclusion(fake_project)

        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False

    def test_reopen_continue_archives_old_artifacts_and_resets_phase(self, fake_project):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        seed_previous_phase_artifacts(fake_project)
        payload = write_conclusion(fake_project)
        conclusion_path = Path(payload["data"]["path"])
        approve_continue(conclusion_path)

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["passed"] is True
        assert out["data"]["reopened"] is True
        assert out["data"]["target_phase"] == "phase_01_research"
        assert out["data"]["from_cycle"] == 1
        assert out["data"]["to_cycle"] == 2

        registry = yaml.safe_load((fake_project / "prae" / "track_registry.yaml").read_text())
        assert registry["current_cycle"] == 2
        assert registry["current_phase"] == "phase_01_research"
        assert registry["project_decision"] == "CONTINUE"
        assert registry["project_reopened_at"] is not None
        assert "project_finalized_at" not in registry

        assert not conclusion_path.exists()
        history_paths = out["data"]["archived_paths"]
        assert any(path.endswith("prae/history/cycle_1/phases/phase_03_conclusion") for path in history_paths)
        assert (fake_project / "prae" / "history" / "cycle_1" / "phases" / "phase_01_research" / "PHASE_BRIEF.md").exists()
        assert (fake_project / "prae" / "history" / "cycle_1" / "phases" / "phase_01_research" / "PHASE_GATE.md").exists()

        new_brief = fake_project / "prae" / "phases" / "phase_01_research" / "PHASE_BRIEF.md"
        assert new_brief.exists()
        assert "phase_01_research" in new_brief.read_text(encoding="utf-8")
        assert "cycle_2" in new_brief.read_text(encoding="utf-8")

    def test_reopen_requires_continue_decision(self, fake_project):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        payload = write_conclusion(fake_project)
        conclusion_path = Path(payload["data"]["path"])
        content = conclusion_path.read_text(encoding="utf-8")
        content = content.replace("APPROVED: pending", "APPROVED: yes")
        content = content.replace("DECISION: ", "DECISION: ARCHIVED")
        content = content.replace("APPROVER: ", "APPROVER: saionji")
        content = content.replace("APPROVED_AT: ", "APPROVED_AT: 2026-04-20")
        conclusion_path.write_text(content, encoding="utf-8")

        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False
