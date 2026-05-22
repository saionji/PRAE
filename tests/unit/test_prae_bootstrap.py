"""Unit tests for prae_bootstrap.py."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).parent.parent.parent / "tools" / "prae_bootstrap.py"
PRAE_ROOT = Path(__file__).parent.parent.parent


def run_tool(target: str, client: str = "claude-code") -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(TOOL),
         "--target", target,
         "--client", client,
         "--prae-path", str(PRAE_ROOT)],
        capture_output=True, text=True
    )
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        output = {"raw": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, output


class TestPraeBootstrap:
    def test_claude_code_creates_skills(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        rc, out = run_tool(str(tmp_path), "claude-code")
        assert rc == 0
        skills_dir = tmp_path / ".claude" / "skills"
        assert skills_dir.is_dir()
        assert (skills_dir / "prae-guard.md").exists()
        assert (skills_dir / "prae-analyst.md").exists()
        assert (skills_dir / "prae-executor.md").exists()

    def test_claude_code_creates_agents(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        run_tool(str(tmp_path), "claude-code")
        agents_dir = tmp_path / ".claude" / "agents"
        assert agents_dir.is_dir()
        assert (agents_dir / "prae-literature-review.md").exists()

    def test_claude_code_creates_commands(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        run_tool(str(tmp_path), "claude-code")
        cmds_dir = tmp_path / ".claude" / "commands"
        assert cmds_dir.is_dir()
        assert (cmds_dir / "prae-add-track.md").exists()
        assert (cmds_dir / "prae-init.md").exists()
        assert (cmds_dir / "prae-advance-phase.md").exists()
        assert (cmds_dir / "prae-finalize.md").exists()
        assert (cmds_dir / "prae-lock-infra.md").exists()
        assert (cmds_dir / "prae-reopen.md").exists()
        assert (cmds_dir / "prae-update-track-state.md").exists()

    def test_codex_creates_tasks(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text("# Agents\n")
        rc, out = run_tool(str(tmp_path), "codex")
        assert rc == 0
        tasks_dir = tmp_path / "prae" / "tasks"
        assert tasks_dir.is_dir()
        assert (tasks_dir / "prae-add-track.md").exists()
        assert (tasks_dir / "prae-init.md").exists()
        assert (tasks_dir / "prae-finalize.md").exists()
        assert (tasks_dir / "prae-lock-infra.md").exists()
        assert (tasks_dir / "prae-reopen.md").exists()
        assert (tasks_dir / "prae-update-track-state.md").exists()

    def test_codex_appends_agents_snippet(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text("# Original\n\nExisting content.\n")
        run_tool(str(tmp_path), "codex")
        agents_md = (tmp_path / "AGENTS.md").read_text()
        assert "PRAE Research Methodology" in agents_md
        assert "Original" in agents_md  # original content preserved

    def test_codex_no_duplicate_snippet(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text("# PRAE Research Methodology\n\nAlready installed.\n")
        run_tool(str(tmp_path), "codex")
        agents_md = (tmp_path / "AGENTS.md").read_text()
        # Should not duplicate the header
        assert agents_md.count("PRAE Research Methodology") == 1

    def test_templates_deployed(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        run_tool(str(tmp_path), "claude-code")
        templates_dir = tmp_path / "prae" / "templates"
        assert templates_dir.is_dir()
        assert (templates_dir / "TRACK_LOG.template.md").exists()
        assert (templates_dir / "EXP_NNN.template.md").exists()

    def test_project_pack_prae_skeleton_is_minimal(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        rc, out = run_tool(str(tmp_path), "claude-code")
        assert rc == 0

        prae_dir = tmp_path / "prae"
        assert (prae_dir / "PRAE_INIT.md").exists()
        assert not (prae_dir / "track_registry.yaml").exists()
        assert not (prae_dir / "phases" / "phase_00_infra" / "PHASE_BRIEF.md").exists()

    def test_project_tools_deployed(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        rc, out = run_tool(str(tmp_path), "claude-code")
        assert rc == 0
        tools_dir = tmp_path / "tools"
        assert tools_dir.is_dir()
        assert (tools_dir / "_artifacts.py").exists()
        assert (tools_dir / "_cli.py").exists()
        assert (tools_dir / "_conclusion_docs.py").exists()
        assert (tools_dir / "_gate_utils.py").exists()
        assert (tools_dir / "_registry.py").exists()
        assert (tools_dir / "_phase_docs.py").exists()
        assert (tools_dir / "add_track.py").exists()
        assert (tools_dir / "advance_phase.py").exists()
        assert (tools_dir / "check_conclusion.py").exists()
        assert (tools_dir / "check_phase_gate.py").exists()
        assert (tools_dir / "finalize_project.py").exists()
        assert (tools_dir / "generate_conclusion.py").exists()
        assert (tools_dir / "generate_phase_gate.py").exists()
        assert (tools_dir / "graduate_track.py").exists()
        assert (tools_dir / "lock_infra_track.py").exists()
        assert (tools_dir / "new_exp.py").exists()
        assert (tools_dir / "new_track.py").exists()
        assert (tools_dir / "record_result.py").exists()
        assert (tools_dir / "reopen_project.py").exists()
        assert (tools_dir / "update_track_state.py").exists()

    def test_invalid_target_fails(self, tmp_path):
        rc, out = run_tool(str(tmp_path / "nonexistent"), "claude-code")
        assert rc in (1, 2)  # error or fail
