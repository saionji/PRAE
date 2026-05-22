"""Shared pytest fixtures for PRAE tool tests."""
from __future__ import annotations
import shutil
import tempfile
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "fake_project"


@pytest.fixture
def fake_project(tmp_path: Path) -> Path:
    """Copy the fake_project fixture to a temp dir and return the path."""
    target = tmp_path / "fake_project"
    shutil.copytree(FIXTURES_DIR, target)
    return target


@pytest.fixture
def locked_infra_project(fake_project: Path) -> Path:
    """Variant with infra_data_v1 LOCKED and proper contracts/spec files."""
    import yaml

    # Create contracts.yaml and MODULE_SPEC.md
    infra_dir = fake_project / "src" / "infra_data_v1"
    infra_dir.mkdir(parents=True, exist_ok=True)
    (infra_dir / "contracts.yaml").write_text("exports:\n  - load_daily_bars\n")
    (infra_dir / "MODULE_SPEC.md").write_text("# MODULE_SPEC\n\n## Exports\n- load_daily_bars\n")

    # Update TRACK_LOG.md to mention PDAE M3
    log_path = fake_project / "prae" / "phases" / "phase_00_infra" / "tracks" / "infra_data_v1" / "TRACK_LOG.md"
    log_path.write_text(log_path.read_text() + "\n| 2026-04-20 | EXPLORING → LOCKED | AI | saionji | PDAE M3 passed |")

    # Update track_registry.yaml
    registry_path = fake_project / "prae" / "track_registry.yaml"
    with open(registry_path) as f:
        r = yaml.safe_load(f)
    for t in r["tracks"]:
        if t["id"] == "infra_data_v1":
            t["state"] = "LOCKED"
            t["locked_at"] = "2026-04-20"
            t["contracts"] = "src/infra_data_v1/contracts.yaml"
            t["module_spec"] = "src/infra_data_v1/MODULE_SPEC.md"
    with open(registry_path, "w") as f:
        yaml.dump(r, f, allow_unicode=True, default_flow_style=False)

    return fake_project
