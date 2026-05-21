#!/usr/bin/env python3
"""
prae_bootstrap.py — 将 PRAE 框架文件部署到目标研究项目

退出码:
  0  部署成功
  1  部署失败（文件冲突等）
  2  参数错误或 PRAE 仓库结构不完整

用法:
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
    """自动检测目标项目的 AI 客户端类型。"""
    if (target / ".claude").is_dir() or (target / "CLAUDE.md").exists():
        return "claude-code"
    if (target / "AGENTS.md").exists():
        return "codex"
    return "unknown"


def copy_missing_tree(src_root: Path, dst_root: Path) -> int:
    """递归复制目录树中目标端缺失的文件，返回复制文件数。"""
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
    """复制 project-pack/ 骨架到目标项目。"""
    pack_src = prae_root / "project-pack"
    if not pack_src.exists():
        checks.append(check_item("project-pack/ 存在", False, str(pack_src)))
        return

    prae_dir = target / "prae"
    prae_dir.mkdir(parents=True, exist_ok=True)

    # 复制 prae/ 最小骨架（只保留 PRAE_INIT.md 等初始化前必需文件）
    pack_prae = pack_src / "prae"
    if pack_prae.exists():
        copy_missing_tree(pack_prae, prae_dir)
    checks.append(check_item("project-pack/prae/ 骨架已部署", True))

    # 复制 abstract 模板到 prae/templates/
    templates_src = prae_root / "runtime" / "abstract"
    templates_dst = prae_dir / "templates"
    templates_dst.mkdir(parents=True, exist_ok=True)
    if templates_src.exists():
        for item in templates_src.iterdir():
            dst = templates_dst / item.name
            if not dst.exists():
                shutil.copy2(item, dst)
    checks.append(check_item("runtime/abstract/ 模板已部署到 prae/templates/", templates_src.exists()))

    # 复制 project-pack/tools/ 到目标 tools/，供研究项目内直接调用 gate/generator 工具
    pack_tools = pack_src / "tools"
    tools_dst = target / "tools"
    if pack_tools.exists():
        copied_count = copy_missing_tree(pack_tools, tools_dst)
        checks.append(check_item("project-pack/tools/ 工具已部署", True, f"copied={copied_count}"))
    else:
        checks.append(check_item("project-pack/tools/ 存在", False, str(pack_tools)))


def deploy_claude_code(prae_root: Path, target: Path, checks: list[dict]) -> None:
    """部署 Claude Code 执行层到 .claude/ 目录。"""
    cc_src = prae_root / "runtime" / "claude-code"
    claude_dir = target / ".claude"

    for subdir in ("skills", "agents", "commands"):
        src = cc_src / subdir
        dst = claude_dir / subdir
        if not src.exists():
            checks.append(check_item(f".claude/{subdir}/ 部署", False, f"{src} 不存在"))
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            shutil.copy2(item, dst / item.name)
        checks.append(check_item(f".claude/{subdir}/ 已部署（{len(list(src.iterdir()))} 个文件）", True))


def deploy_codex(prae_root: Path, target: Path, checks: list[dict]) -> None:
    """部署 Codex 执行层：tasks 到 prae/tasks/，合并 AGENTS_SNIPPET.md。"""
    codex_src = prae_root / "runtime" / "codex"

    # 部署 tasks/
    tasks_src = codex_src / "tasks"
    tasks_dst = target / "prae" / "tasks"
    if tasks_src.exists():
        tasks_dst.mkdir(parents=True, exist_ok=True)
        for item in tasks_src.iterdir():
            shutil.copy2(item, tasks_dst / item.name)
        checks.append(check_item(f"prae/tasks/ 已部署（{len(list(tasks_src.iterdir()))} 个文件）", True))
    else:
        checks.append(check_item("prae/tasks/ 部署", False, str(tasks_src)))

    # 合并 AGENTS_SNIPPET.md 到 AGENTS.md
    snippet_path = codex_src / "AGENTS_SNIPPET.md"
    agents_md = target / "AGENTS.md"
    if snippet_path.exists():
        snippet = snippet_path.read_text(encoding="utf-8")
        if agents_md.exists():
            existing = agents_md.read_text(encoding="utf-8")
            if "PRAE 研究方法论" not in existing:
                with open(agents_md, "a", encoding="utf-8") as f:
                    f.write("\n\n" + snippet)
                checks.append(check_item("AGENTS_SNIPPET.md 已追加到 AGENTS.md", True))
            else:
                checks.append(check_item("AGENTS.md 已含 PRAE 段落（跳过）", True))
        else:
            agents_md.write_text(snippet, encoding="utf-8")
            checks.append(check_item("AGENTS.md 已创建（含 PRAE 段落）", True))
    else:
        checks.append(check_item("AGENTS_SNIPPET.md 存在", False, str(snippet_path)))


def bootstrap(target_str: str, client: str, prae_root_str: str) -> None:
    target = Path(target_str).resolve()
    prae_root = Path(prae_root_str).resolve() if prae_root_str else PRAE_ROOT

    # 验证 PRAE 仓库结构
    if not (prae_root / "runtime" / "abstract").exists():
        error(f"PRAE 仓库结构不完整: {prae_root} 缺少 runtime/abstract/")

    # 自动检测客户端
    if client == "auto":
        client = detect_client(target)
        if client == "unknown":
            error("无法自动检测客户端类型，请用 --client 指定 claude-code 或 codex")

    checks: list[dict] = []
    checks.append(check_item(f"目标目录存在", target.is_dir(), str(target)))
    checks.append(check_item(f"客户端类型", True, client))

    # 部署 project-pack 骨架
    deploy_project_pack(prae_root, target, checks)

    # 部署平台特定执行层
    if client == "claude-code":
        deploy_claude_code(prae_root, target, checks)
    elif client == "codex":
        deploy_codex(prae_root, target, checks)

    # PDAE 是可选 companion（基础设施工程化和契约检查需要它）
    # 检测状态写入 data，不参与 all_passed —— PRAE 本身可独立运行
    pdae_home = os.environ.get("PDAE_HOME")
    pdae_available = bool(
        pdae_home and (Path(pdae_home) / "tools/check_contracts.py").exists()
    )

    all_passed = all(c["passed"] for c in checks)
    failed = [c for c in checks if not c["passed"]]
    result(all_passed, checks,
           f"Bootstrap {'成功' if all_passed else f'部分失败 ({len(failed)} 项)'}",
           data={"target": str(target), "client": client, "pdae_available": pdae_available})


def main() -> None:
    parser = argparse.ArgumentParser(description="将 PRAE 框架部署到研究项目")
    parser.add_argument("--target", required=True, help="目标研究项目根目录")
    parser.add_argument("--client", default="auto",
                        choices=["claude-code", "codex", "auto"],
                        help="AI 客户端类型（默认自动检测）")
    parser.add_argument("--prae-path", default="", help="PRAE 仓库路径（默认自动推断）")
    args = parser.parse_args()
    bootstrap(args.target, args.client, args.prae_path)


if __name__ == "__main__":
    main()
