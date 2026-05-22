#!/usr/bin/env python3
"""
add_track.py — formally register a new track in track_registry.yaml

Exit codes:
  0  registered successfully
  1  registration conditions not met
  2  file missing, format error, or argument error

Usage:
  python3 tools/add_track.py \
    --project-dir <path> \
    --track-id <track_id> \
    --type <research|infrastructure> \
    [--hypothesis <text>] \
    [--depends-on infra_a infra_b ...] \
    [--description <text>] \
    [--src <path>]
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _cli import run_action
from _output import check_item
from _registry import get_current_phase, load_registry as _shared_load_registry, save_registry


class AddTrackError(RuntimeError):
    """Track registration input error."""


def load_registry(project_dir: str) -> dict:
    return _shared_load_registry(project_dir, error_cls=AddTrackError)


def validate_track_id(track_id: str, track_type: str) -> None:
    prefixes = {
        "research": "research_",
        "infrastructure": "infra_",
    }
    prefix = prefixes[track_type]
    if not track_id.startswith(prefix):
        raise AddTrackError(f"track_id={track_id} does not match type={track_type} (should start with {prefix})")


def ensure_unique_track_id(registry: dict, track_id: str) -> None:
    if any(track.get("id") == track_id for track in registry.get("tracks", [])):
        raise AddTrackError(f"track {track_id} already exists in track_registry.yaml")


def default_src(track_id: str, track_type: str) -> str:
    if track_type == "research":
        return f"src/tracks/{track_id}/"
    return f"src/{track_id}/"


def build_track_entry(args: argparse.Namespace) -> dict:
    src = args.src or default_src(args.track_id, args.type)

    if args.type == "research":
        if not args.hypothesis:
            raise AddTrackError("a research track must provide --hypothesis")
        return {
            "id": args.track_id,
            "type": "research",
            "state": "EXPLORING",
            "src": src,
            "hypothesis": args.hypothesis,
            "depends_on": args.depends_on or [],
            "experiments": 0,
            "evidence_summary": None,
            "concluded_at": None,
            "merged_into": None,
        }

    return {
        "id": args.track_id,
        "type": "infrastructure",
        "state": "EXPLORING",
        "src": src,
        "description": args.description or "to be filled in",
        "module_spec": None,
        "contracts": None,
        "locked_at": None,
    }


def add_track(project_dir: Path, args: argparse.Namespace) -> dict:
    registry = load_registry(str(project_dir))
    validate_track_id(args.track_id, args.type)
    ensure_unique_track_id(registry, args.track_id)

    entry = build_track_entry(args)
    registry.setdefault("tracks", []).append(entry)
    registry["updated"] = str(datetime.date.today())

    registry_path = save_registry(project_dir, registry)

    checks = [
        check_item("track_id matches the type", True, f"{args.track_id} / {args.type}"),
        check_item("track ID is not yet taken", True, args.track_id),
        check_item("track_registry.yaml has appended the new track", True, str(registry_path)),
    ]

    return {
        "passed": True,
        "summary": f"new track registered: {args.track_id}",
        "checks": checks,
        "data": {
            "track_id": args.track_id,
            "type": args.type,
            "state": "EXPLORING",
            "src": entry["src"],
            "current_phase": get_current_phase(registry),
            "registered": True,
            "registry_path": str(registry_path),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a new track in track_registry.yaml")
    parser.add_argument("--project-dir", required=True, help="Research project root directory")
    parser.add_argument("--track-id", required=True, help="Track ID")
    parser.add_argument("--type", required=True, choices=["research", "infrastructure"], help="Track type")
    parser.add_argument("--hypothesis", help="One-line hypothesis for a research track")
    parser.add_argument("--depends-on", nargs="*", default=[], help="Infrastructure track IDs that a research track depends on")
    parser.add_argument("--description", help="One-line description for an infrastructure track")
    parser.add_argument("--src", help="Optional: override the default src path")
    args = parser.parse_args()

    run_action(lambda: add_track(Path(args.project_dir), args), AddTrackError)


if __name__ == "__main__":
    main()
