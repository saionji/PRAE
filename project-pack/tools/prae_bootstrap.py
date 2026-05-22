#!/usr/bin/env python3
"""
prae_bootstrap.py — Deploy the PRAE framework files into a target research project

Exit codes:
  0  Deployment succeeded
  1  Deployment failed (file conflicts, etc.)
  2  Argument error or incomplete PRAE repository structure

Usage:
  python3 tools/prae_bootstrap.py --target <path> [--client claude-code|codex|auto] [--prae-path <path>]
"""
from __future__ import annotations
import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _output import check_item, error, result

PRAE_ROOT = Path(__file__).parent.parent


def detect_client(target: Path) -> str:
    """Auto-detect the target project's AI client type."""
    if (target / ".claude").is_dir() or (target / "CLAUDE.md").exists():
        return "claude-code"
    if (target / "AGENTS.md").exists():
        return "codex"
    return "unknown"


def copy_missing_tree(src_root: Path, dst_root: Path) -> int:
    """Recursively copy files missing on the target side, returning the count of files copied."""
    copied = 0
    for item in src_root.rglob("*"):
        rel = item.relative_to(src_root)
        dst = dst_root / rel
        if item.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(item, dst)
            copied += 1
    return copied


def deploy_project_pack(prae_root: Path, target: Path, checks: list[dict]) -> None:
    """Copy the project-pack/ skeleton into the target project."""
    pack_src = prae_root / "project-pack"
    if not pack_src.exists():
        checks.append(check_item("project-pack/ exists", False, str(pack_src)))
        return

    prae_dir = target / "prae"
    prae_dir.mkdir(parents=True, exist_ok=True)

    # Copy the minimal prae/ skeleton (keep only pre-initialization required files such as PRAE_INIT.md)
    pack_prae = pack_src / "prae"
    if pack_prae.exists():
        copy_missing_tree(pack_prae, prae_dir)
    checks.append(check_item("project-pack/prae/ skeleton deployed", True))

    # Copy abstract templates into prae/templates/
    templates_src = prae_root / "runtime" / "abstract"
    templates_dst = prae_dir / "templates"
    templates_dst.mkdir(parents=True, exist_ok=True)
    if templates_src.exists():
        for item in templates_src.iterdir():
            dst = templates_dst / item.name
            if not dst.exists():
                shutil.copy2(item, dst)
    checks.append(check_item("runtime/abstract/ templates deployed to prae/templates/", templates_src.exists()))

    # Copy project-pack/tools/ into the target tools/ so the research project can invoke gate/generator tools directly
    pack_tools = pack_src / "tools"
    tools_dst = target / "tools"
    if pack_tools.exists():
        copied_count = copy_missing_tree(pack_tools, tools_dst)
        checks.append(check_item("project-pack/tools/ tools deployed", True, f"copied={copied_count}"))
    else:
        checks.append(check_item("project-pack/tools/ exists", False, str(pack_tools)))


def deploy_claude_code(prae_root: Path, target: Path, checks: list[dict]) -> None:
    """Deploy the Claude Code execution layer into the .claude/ directory."""
    cc_src = prae_root / "runtime" / "claude-code"
    claude_dir = target / ".claude"

    for subdir in ("skills", "agents", "commands"):
        src = cc_src / subdir
        dst = claude_dir / subdir
        if not src.exists():
            checks.append(check_item(f".claude/{subdir}/ deployment", False, f"{src} does not exist"))
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            shutil.copy2(item, dst / item.name)
        checks.append(check_item(f".claude/{subdir}/ deployed ({len(list(src.iterdir()))} files)", True))


def deploy_codex(prae_root: Path, target: Path, checks: list[dict]) -> None:
    """Deploy the Codex execution layer: tasks into prae/tasks/, merge AGENTS_SNIPPET.md."""
    codex_src = prae_root / "runtime" / "codex"

    # Deploy tasks/
    tasks_src = codex_src / "tasks"
    tasks_dst = target / "prae" / "tasks"
    if tasks_src.exists():
        tasks_dst.mkdir(parents=True, exist_ok=True)
        for item in tasks_src.iterdir():
            shutil.copy2(item, tasks_dst / item.name)
        checks.append(check_item(f"prae/tasks/ deployed ({len(list(tasks_src.iterdir()))} files)", True))
    else:
        checks.append(check_item("prae/tasks/ deployment", False, str(tasks_src)))

    # Merge AGENTS_SNIPPET.md into AGENTS.md
    snippet_path = codex_src / "AGENTS_SNIPPET.md"
    agents_md = target / "AGENTS.md"
    if snippet_path.exists():
        snippet = snippet_path.read_text(encoding="utf-8")
        if agents_md.exists():
            existing = agents_md.read_text(encoding="utf-8")
            if "PRAE Research Methodology" not in existing:
                with open(agents_md, "a", encoding="utf-8") as f:
                    f.write("\n\n" + snippet)
                checks.append(check_item("AGENTS_SNIPPET.md appended to AGENTS.md", True))
            else:
                checks.append(check_item("AGENTS.md already contains the PRAE section (skipped)", True))
        else:
            agents_md.write_text(snippet, encoding="utf-8")
            checks.append(check_item("AGENTS.md created (with PRAE section)", True))
    else:
        checks.append(check_item("AGENTS_SNIPPET.md exists", False, str(snippet_path)))


def bootstrap(target_str: str, client: str, prae_root_str: str) -> None:
    target = Path(target_str).resolve()
    prae_root = Path(prae_root_str).resolve() if prae_root_str else PRAE_ROOT

    # Validate the PRAE repository structure
    if not (prae_root / "runtime" / "abstract").exists():
        error(f"Incomplete PRAE repository structure: {prae_root} is missing runtime/abstract/")

    # Auto-detect the client
    if client == "auto":
        client = detect_client(target)
        if client == "unknown":
            error("Cannot auto-detect the client type; use --client to specify claude-code or codex")

    checks: list[dict] = []
    checks.append(check_item(f"Target directory exists", target.is_dir(), str(target)))
    checks.append(check_item(f"Client type", True, client))

    # Deploy the project-pack skeleton
    deploy_project_pack(prae_root, target, checks)

    # Deploy the platform-specific execution layer
    if client == "claude-code":
        deploy_claude_code(prae_root, target, checks)
    elif client == "codex":
        deploy_codex(prae_root, target, checks)

    # PDAE is an optional companion (needed for infrastructure engineering and contract checking)
    # The detection result is written to data and does not affect all_passed — PRAE can run standalone
    pdae_home = os.environ.get("PDAE_HOME")
    pdae_available = bool(
        pdae_home and (Path(pdae_home) / "tools/check_contracts.py").exists()
    )

    all_passed = all(c["passed"] for c in checks)
    failed = [c for c in checks if not c["passed"]]
    result(all_passed, checks,
           f"Bootstrap {'succeeded' if all_passed else f'partially failed ({len(failed)} items)'}",
           data={"target": str(target), "client": client, "pdae_available": pdae_available})


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy the PRAE framework into a research project")
    parser.add_argument("--target", required=True, help="Target research project root directory")
    parser.add_argument("--client", default="auto",
                        choices=["claude-code", "codex", "auto"],
                        help="AI client type (default: auto-detect)")
    parser.add_argument("--prae-path", default="", help="PRAE repository path (default: auto-inferred)")
    args = parser.parse_args()
    bootstrap(args.target, args.client, args.prae_path)


if __name__ == "__main__":
    main()
