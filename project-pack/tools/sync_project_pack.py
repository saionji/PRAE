#!/usr/bin/env python3
"""
sync_project_pack.py — 将 tools/ 同步到 project-pack/tools/

用于内部维护：保证 project-pack/ 中的工具与根 tools/ 保持一致。
通常在修改了根 tools/ 后手动运行。

退出码:
  0  同步成功
  1  同步失败
  2  目录结构错误

用法:
  python3 tools/sync_project_pack.py [--dry-run]
"""
from __future__ import annotations
import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _output import check_item, result, error

PRAE_ROOT = Path(__file__).parent.parent
TOOLS_SRC = PRAE_ROOT / "tools"
PACK_TOOLS_DST = PRAE_ROOT / "project-pack" / "tools"

# 需要同步到 project-pack/tools/ 的文件
SYNC_FILES = [
    "add_track.py",
    "advance_phase.py",
    "check_contracts.py",
    "check_conclusion.py",
    "check_phase_gate.py",
    "finalize_project.py",
    "generate_conclusion.py",
    "generate_phase_gate.py",
    "graduate_track.py",
    "reopen_project.py",
    "check_research_gate.py",
    "check_track_status.py",
    "init_project.py",
    "lock_infra_track.py",
    "new_exp.py",
    "new_track.py",
    "prae_bootstrap.py",
    "record_result.py",
    "sync_project_pack.py",
    "update_track_state.py",
    "_artifacts.py",
    "_cli.py",
    "_conclusion_docs.py",
    "_gate_utils.py",
    "_output.py",
    "_phase_docs.py",
    "_registry.py",
]


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:8]


def sync(dry_run: bool) -> None:
    checks: list[dict] = []

    if not TOOLS_SRC.is_dir():
        error(f"tools/ 目录不存在: {TOOLS_SRC}")

    PACK_TOOLS_DST.mkdir(parents=True, exist_ok=True)

    for filename in SYNC_FILES:
        src = TOOLS_SRC / filename
        dst = PACK_TOOLS_DST / filename

        if not src.exists():
            checks.append(check_item(f"{filename}: 源文件存在", False, str(src)))
            continue

        src_hash = file_hash(src)
        dst_hash = file_hash(dst) if dst.exists() else "不存在"
        needs_update = src_hash != dst_hash

        if needs_update:
            if not dry_run:
                shutil.copy2(src, dst)
            checks.append(check_item(
                f"{filename}: {'已同步' if not dry_run else '需同步（dry-run）'}",
                True,
                f"src={src_hash} dst={dst_hash}"
            ))
        else:
            checks.append(check_item(f"{filename}: 已是最新", True, f"hash={src_hash}"))

    all_passed = all(c["passed"] for c in checks)
    result(all_passed, checks,
           f"sync_project_pack: {'干跑完成' if dry_run else '同步完成'}",
           data={"synced_files": len(SYNC_FILES), "dry_run": dry_run})


def main() -> None:
    parser = argparse.ArgumentParser(description="同步 tools/ 到 project-pack/tools/")
    parser.add_argument("--dry-run", action="store_true", help="只显示差异，不实际复制")
    args = parser.parse_args()
    sync(args.dry_run)


if __name__ == "__main__":
    main()
