# {{project_name}} — Research Project AI Context

> **Installation**: Rename this file to `CLAUDE.md` (Claude Code) or `AGENTS.md` (Codex), fill in the project information, then delete this line.

## Entry Points

- `CLAUDE.md` / `AGENTS.md`: model context entry point
- `/prae-bootstrap` or `prae bootstrap`: project installation entry point
- `/prae-init` or `prae init`: project state initialization entry point

---

## Project Overview

**Project name**: {{project_name}}
**Research question**: {{research_question}}
**Current phase**: phase_00_infra (initial — update as the project progresses)

---

## PRAE Methodology

This project uses PRAE (Protocol-Driven Research & Experimentation) to manage the research decision process.

**Methodology documents** (PRAE repository):
- `methodology/PRAE_QUICKSTART.md` — operations manual
- `methodology/PRAE_CORE_MODEL.md` — track / phase / state machine definitions
- `methodology/PRAE_ROLES.md` — Analyst / Executor SOPs
- `methodology/PRAE_PHASE_GATES.md` — four-phase gate rules
- `methodology/PRAE_RESEARCH_GATE.md` — research track gate rules
- `methodology/PRAE_ARTIFACTS.md` — specifications for all artifacts

---

## PDAE Integration

When an infrastructure track enters the LOCKED state, invoke the PDAE engineering flow:
- PDAE repository: `${PDAE_HOME}/`
- Key tools: `tools/check_contracts.py`, `tools/check_unit_gate.py`

---

## Project Structure

```
{{project_name}}/
├── CLAUDE.md / AGENTS.md    ← this file
├── prae/
│   ├── PRAE_INIT.md         ← problem statement and component classification (filled in only once)
│   ├── track_registry.yaml  ← master track state table (created after `/prae-init`)
│   └── phases/
│       ├── phase_00_infra/  ← infrastructure readiness period (created after `/prae-init`)
│       ├── phase_01_research/ (created after Phase 0 passes)
│       ├── phase_02_validation/
│       └── phase_03_conclusion/
└── src/
    ├── infra_{name}_v1/     ← LOCKED infrastructure (read-only)
    ├── shared/              ← shared across multiple tracks (PDAE M3)
    └── tracks/{track_id}/  ← research code
        ├── experiments/     ← experiment scripts (never imported)
        └── impl/            ← stable implementation (created by the Executor)
```

---

## Common Commands

```bash
# Check track status
python3 tools/check_track_status.py --project-dir .

# Check the phase gate
python3 tools/check_phase_gate.py --project-dir . --phase 0

# Check the research gate
python3 tools/check_research_gate.py --track-id {track_id} --project-dir .

# Contract check (requires PDAE)
python3 tools/check_contracts.py --contracts src/{infra_track}/contracts.yaml --src src/
```

---

## Current Status

- Total tracks: {{N}}
- Current phase: phase_00_infra
- Next step:
  - If the project has not yet adopted PRAE: first run `/prae-bootstrap` or `prae bootstrap`
  - If it has been bootstrapped but `prae/track_registry.yaml` does not yet exist: fill in `prae/PRAE_INIT.md`, then run `/prae-init` (Claude Code) or `prae init` (Codex)
