"""Unit tests for check_conclusion.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

from tests.unit.test_generate_conclusion import make_phase3_project
from tests.unit.test_graduate_track import run_tool as run_graduate_tool

TOOL = Path(__file__).parent.parent.parent / "tools" / "check_conclusion.py"


def run_tool(project_dir: str, extra_args: list[str] | None = None) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--project-dir", project_dir] + (extra_args or []),
        capture_output=True,
        text=True,
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


def approve_conclusion(path: Path, decision: str) -> None:
    content = path.read_text(encoding="utf-8")
    content = content.replace("APPROVED: pending", "APPROVED: yes")
    content = content.replace("DECISION: ", f"DECISION: {decision}")
    content = content.replace("APPROVER: ", "APPROVER: saionji")
    content = content.replace("APPROVED_AT: ", "APPROVED_AT: 2026-04-20")
    path.write_text(content, encoding="utf-8")


class TestCheckConclusion:
    def test_structure_passes_before_approval(self, fake_project):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        write_conclusion(fake_project)

        rc, out = run_tool(str(fake_project))
        assert rc == 0
        assert out["passed"] is True
        assert out["data"]["approved"] == "pending"

    def test_check_approved_fails_when_pending(self, fake_project):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        write_conclusion(fake_project)

        rc, out = run_tool(str(fake_project), ["--check-approved"])
        assert rc == 1
        assert out["passed"] is False

    def test_graduated_to_pdae_requires_registered_project(self, fake_project):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        payload = write_conclusion(fake_project)
        path = Path(payload["data"]["path"])
        approve_conclusion(path, "GRADUATED_TO_PDAE")

        rc, out = run_tool(str(fake_project), ["--check-approved"])
        assert rc == 1
        assert out["passed"] is False

    def test_graduated_to_pdae_passes_after_graduate_track(self, fake_project, tmp_path):
        from tools.generate_conclusion import write_conclusion

        make_phase3_project(fake_project)
        pdae_project = tmp_path / "pdae-project"
        pdae_project.mkdir()
        run_graduate_tool(str(fake_project), "research_strategy_momentum", str(pdae_project))

        payload = write_conclusion(fake_project)
        path = Path(payload["data"]["path"])
        approve_conclusion(path, "GRADUATED_TO_PDAE")

        rc, out = run_tool(str(fake_project), ["--check-approved"])
        assert rc == 0
        assert out["passed"] is True

    def test_legacy_final_decision_format_fails_structure_check(self, fake_project):
        make_phase3_project(fake_project)
        path = fake_project / "prae" / "phases" / "phase_03_conclusion" / "CONCLUSION.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# CONCLUSION — fake-research\n\n## 项目结论\n\nok\n\n## 各轨道去向\n\n| 轨道 ID | 最终状态 | 结论摘要 | 备注 |\n|---------|---------|---------|------|\n| `research_strategy_momentum` | GRADUATED | ok | — |\n\n## 毕业轨道的 PDAE 项目链接\n\n| 轨道 ID | PDAE 项目路径 |\n|---------|----------------|\n| `research_strategy_momentum` | `待填写` |\n\n## 未解决问题\n\n- none\n\n## 最终决定\n\n**APPROVED**: yes\n\n**决定**（人工填写）：\n\n```\nGRADUATED_TO_PDAE\n```\n\n**批准人**：saionji\n**日期**：2026-04-20\n",
            encoding="utf-8",
        )

        rc, out = run_tool(str(fake_project))
        assert rc == 1
        assert out["passed"] is False
