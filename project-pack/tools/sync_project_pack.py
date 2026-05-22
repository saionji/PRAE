#!/usr/bin/env python3
"""
sync_project_pack.py — sync tools/ into project-pack/tools/

For internal maintenance: keeps the tools in project-pack/ consistent with the root tools/.
Usually run manually after modifying the root tools/.

Exit codes:
  0  synced successfully
  1  sync failed
  2  directory structure error

Usage:
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

# Files that need to be synced into project-pack/tools/
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
        error(f"tools/ directory does not exist: {TOOLS_SRC}")

    PACK_TOOLS_DST.mkdir(parents=True, exist_ok=True)

    for filename in SYNC_FILES:
        src = TOOLS_SRC / filename
        dst = PACK_TOOLS_DST / filename

        if not src.exists():
            checks.append(check_item(f"{filename}: source file exists", False, str(src)))
            continue

        src_hash = file_hash(src)
        dst_hash = file_hash(dst) if dst.exists() else "does not exist"
        needs_update = src_hash != dst_hash

        if needs_update:
            if not dry_run:
                shutil.copy2(src, dst)
            checks.append(check_item(
                f"{filename}: {'synced' if not dry_run else 'needs sync (dry-run)'}",
                True,
                f"src={src_hash} dst={dst_hash}"
            ))
        else:
            checks.append(check_item(f"{filename}: already up to date", True, f"hash={src_hash}"))

    all_passed = all(c["passed"] for c in checks)
    result(all_passed, checks,
           f"sync_project_pack: {'dry run complete' if dry_run else 'sync complete'}",
           data={"synced_files": len(SYNC_FILES), "dry_run": dry_run})


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync tools/ into project-pack/tools/")
    parser.add_argument("--dry-run", action="store_true", help="Show differences only; do not actually copy")
    args = parser.parse_args()
    sync(args.dry_run)


if __name__ == "__main__":
    main()
