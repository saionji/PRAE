"""Registry / track shared helpers for PRAE tools."""
from __future__ import annotations

from pathlib import Path

import yaml

from _output import check_item


class RegistryError(RuntimeError):
    """Shared registry loading / validation error."""


PHASE_ALLOWED_TRACK_TYPES = {
    "phase_00_infra": {"infrastructure"},
    "phase_01_research": {"research"},
    "phase_02_validation": {"research"},
}
KNOWN_PHASES = set(PHASE_ALLOWED_TRACK_TYPES) | {"phase_03_conclusion"}


def load_registry(project_dir: str | Path, *, error_cls: type[Exception] = RegistryError) -> dict:
    registry_path = Path(project_dir) / "prae" / "track_registry.yaml"
    if not registry_path.exists():
        raise error_cls(f"track_registry.yaml not found: {registry_path}")

    try:
        with open(registry_path, encoding="utf-8") as f:
            registry = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise error_cls(f"track_registry.yaml format error: {exc}") from exc

    if not isinstance(registry, dict):
        raise error_cls("track_registry.yaml top level must be a mapping")

    override = registry.get("current_phase_override")
    if override not in (None, ""):
        if not isinstance(override, str):
            raise error_cls("current_phase_override must be a string")
        if override not in KNOWN_PHASES:
            raise error_cls(f"current_phase_override is invalid: {override}")
    return registry


def get_recorded_phase(registry: dict, default: str = "phase_00_infra") -> str:
    return registry.get("current_phase", default)


def get_phase_override(registry: dict) -> str | None:
    override = registry.get("current_phase_override")
    if isinstance(override, str):
        override = override.strip()
    return override or None


def get_current_phase(registry: dict, default: str = "phase_00_infra") -> str:
    return get_phase_override(registry) or get_recorded_phase(registry, default)


def describe_phase_context(registry: dict, default: str = "phase_00_infra") -> str:
    recorded = get_recorded_phase(registry, default)
    override = get_phase_override(registry)
    if override:
        return f"effective_phase={override}, recorded_phase={recorded}, current_phase_override=on"
    return f"effective_phase={recorded}, recorded_phase={recorded}"


def get_cycle_label(registry: dict) -> str:
    try:
        cycle = int(registry.get("current_cycle", 1))
    except (TypeError, ValueError):
        cycle = 1
    if cycle < 1:
        cycle = 1
    return f"cycle_{cycle}"


def find_track(registry: dict, track_id: str) -> dict | None:
    return next((t for t in registry.get("tracks", []) if t.get("id") == track_id), None)


def require_track(
    registry: dict,
    track_id: str,
    *,
    error_cls: type[Exception],
    expected_type: str | None = None,
) -> dict:
    track = find_track(registry, track_id)
    if track is None:
        raise error_cls(f"track {track_id} is not in track_registry.yaml")
    if expected_type and track.get("type") != expected_type:
        raise error_cls(
            f"track {track_id} has type {track.get('type')}, only applicable to {expected_type}"
        )
    return track


def validate_phase_track_match(
    current_phase: str,
    track: dict,
    *,
    action_label: str,
    blocked_phase03_detail: str,
    detail: str | None = None,
) -> dict:
    allowed = PHASE_ALLOWED_TRACK_TYPES.get(current_phase)
    track_type = track.get("type", "")
    detail = detail or f"current_phase={current_phase}, track_type={track_type}, allowed={sorted(allowed) if allowed else []}"
    if current_phase == "phase_03_conclusion":
        return check_item(
            f"Current phase permits {action_label}",
            False,
            blocked_phase03_detail,
        )
    if allowed is None:
        return check_item(f"Current phase permits {action_label}", True, f"{current_phase} has no extra restrictions configured")
    return check_item(
        f"Current phase permits {action_label}",
        track_type in allowed,
        detail,
    )


def save_registry(project_dir: Path, registry: dict) -> Path:
    registry_path = project_dir / "prae" / "track_registry.yaml"
    with open(registry_path, "w", encoding="utf-8") as f:
        yaml.dump(registry, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return registry_path
