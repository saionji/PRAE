# PRAE — Protocol-Driven Research & Experimentation

> I run several real research and engineering projects, all managed with this toolchain. PRAE is the methodology + tools I extracted from that work. Open-sourced because the discipline of public docs makes it better.

**Status**: `v0.1.0-alpha` · single maintainer · in production use by the author · documentation is in English.

**Quickstart**: see [Quick Start](#quick-start). **Concepts**: see [Core Model](#core-model). **What is PDAE**: see [Relationship to PDAE](#relationship-to-pdae).

---

## What is PRAE

The hard problem in research projects (quant strategies, object detection, robot control) is *not* writing code. It's deciding **which experiment to run next, which result to believe, when to abandon a line of work**.

PRAE structures that decision process — using two track types, four phases, and four layers of gates — so that AI can assist research-level decisions while keeping reproducibility, traceability, and human approval in the loop:

- Experiments are reproducible (recorded parameters + random seeds).
- Decisions are documented (every move recorded in `TRACK_LOG.md` and `PHASE_GATE.md`).
- Infrastructure is locked down *before* algorithmic exploration begins (Phase 0 gate).
- Code graduates to production only after a full engineering review (PDAE M1-M3).

If you're an LLM entering this repository for the first time, read `LLM_ENTRYPOINT.md` first.

## Entry points

- `LLM_ENTRYPOINT.md` — model context entry
- `prae bootstrap` / `/prae-bootstrap` — installs PRAE into your research project
- `prae init` / `/prae-init` — initializes a project's state machine

---

## Quick Start

### Install PRAE into an existing research project

This is the **project-level entry point** — the first command a new research project runs to onboard PRAE.

**Claude Code users:**

```
/prae-bootstrap
```

(Claude detects your project type and deploys the PRAE files.)

**Codex CLI users:**

```
codex exec --task /path/to/PRAE/runtime/codex/tasks/prae-bootstrap.md
```

**Manual install (works for either runtime):**

```bash
python3 /path/to/PRAE/tools/prae_bootstrap.py \
  --target /path/to/your/project \
  --client claude-code   # or "codex"
```

See `runtime/claude-code/SKILLS_README.md` if you want only the role-discipline skills without the rest of PRAE.

### Initialize the research project

1. Edit `prae/PRAE_INIT.md` — write down your research question and your track plan.
2. Run `/prae-init` (Claude Code) or `prae init` (Codex CLI).
   This generates `prae/track_registry.yaml`, `prae/phases/phase_00_infra/PHASE_BRIEF.md`, and the initial `TRACK_LOG.md` for each infrastructure track.
3. **Finish Phase 0 first.** For each infrastructure track, record selection experiments and — after the implementation passes PDAE M3 — formally lock it with `/prae-lock-infra` (or `prae lock-infra`).
4. Once every infrastructure track is `LOCKED`, run `/prae-advance-phase` to generate a gate document for human approval. Approve it (write `APPROVED: yes` in `PHASE_GATE.md`), then run the same command again to actually enter Phase 1.
5. In Phase 1, run `/prae-new-track` and `/prae-new-exp` for tracks already registered in `track_registry.yaml`. If you have a brand-new hypothesis, run `/prae-add-track` first, then `/prae-new-track`.
6. Record experiment outcomes with `/prae-record-result`. If you approve a state change, use `/prae-update-track-state` (or `prae update-track-state`).

---

## Core Model

### Two track types

| Type | Lifecycle | Description |
|------|-----------|-------------|
| Infrastructure track | `EXPLORING → LOCKED` | Data pipelines, feature engineering, and similar supporting components. Once `LOCKED`, the track is read-only; any change opens `_v2`. |
| Research track | `EXPLORING → ACTIVE → KILLED / MERGED / GRADUATED` | Algorithmic hypotheses. Each experiment is recorded as an `EXP_NNN.md` file. |

### Four phases

```
Phase 0  Infrastructure readiness   All infrastructure tracks must be LOCKED before Phase 1 starts.
Phase 1  Algorithmic exploration    Parallel experiments; AI analysis; human approval on state changes.
Phase 2  Algorithmic validation     Focused validation; strict parameter discipline.
Phase 3  Conclusion                 Archive or graduate into PDAE.
```

### AI roles

- **Analyst** — Activated when a research track is in `EXPLORING` or `ACTIVE`. Designs experiments, runs literature search, interprets results.
- **Executor** — Activated when a track is approaching `LOCKED` or stable implementation needs extracting. Writes code, runs PDAE unit-level gates.

---

## Repository layout

```
PRAE/
├── methodology/          ← Source-of-truth (LLMs read these; humans can too)
│   ├── PRAE_QUICKSTART.md
│   ├── PRAE_CORE_MODEL.md       ← Authoritative track / phase / state-machine definitions
│   ├── PRAE_ROLES.md            ← Analyst / Executor SOPs
│   ├── PRAE_PHASE_GATES.md
│   ├── PRAE_RESEARCH_GATE.md
│   └── PRAE_ARTIFACTS.md
│
├── runtime/
│   ├── abstract/         ← Platform-agnostic templates (TRACK_LOG, EXP_NNN, etc.)
│   ├── claude-code/      ← Claude Code: skills + agents + commands
│   └── codex/            ← Codex CLI: prompts + tasks + bin/prae wrapper
│
├── project-pack/         ← Deployment skeleton (copied into your project by bootstrap)
├── tools/                ← Gating scripts (check_phase_gate.py, lock_infra_track.py, …)
└── tests/                ← Unit + integration tests
```

---

## Gating tools

All tools emit JSON. Exit code: `0` = pass, `1` = fail, `2` = missing file or invalid input.

```bash
# Phase gate (e.g. 0→1)
python3 tools/check_phase_gate.py --project-dir . --phase 0

# Research-track gate
python3 tools/check_research_gate.py --project-dir . --track-id research_strategy_momentum

# Track-registry consistency
python3 tools/check_track_status.py --project-dir .

# Contracts check (PDAE-vendored)
python3 tools/check_contracts.py --contracts src/infra_data_v1/contracts.yaml --src src/
```

---

## Relationship to PDAE

PDAE (Project-Driven Application Engineering) is PRAE's sibling project. PRAE manages **which research direction to invest in**; PDAE manages **how to engineer a particular component well**.

| Scenario | PRAE | PDAE |
|---|---|---|
| Deciding which experiment to run | ✓ | — |
| Engineering an infrastructure component | triggers → | ✓ |
| Unit gates / contract checks | reuses tooling | ✓ |
| Graduating to production | triggers → | ✓ |

PDAE is a separate project. If you have it installed, set the `PDAE_HOME` environment variable so PRAE can discover it.

---

## Development & testing

```bash
# Run all tests
pytest tests/ -v

# Run integration tests (full lifecycle)
pytest tests/integration/test_end_to_end.py -v

# Manual smoke
mkdir /tmp/prae-smoke && touch /tmp/prae-smoke/.claude
python3 tools/prae_bootstrap.py --target /tmp/prae-smoke --client claude-code
python3 tools/init_project.py --name smoke --output-dir /tmp/prae-smoke
```

CI on every push to `main` runs the same test suite across Python 3.10 / 3.11 / 3.12.

---

## Status & roadmap

`v0.1.0-alpha` is the first public release. Known short-term work:

- Translate `methodology/*.md` to English (currently the Chinese versions are authoritative).
- Polish `--help` output across all 27 tools.
- Manual Codex CLI end-to-end smoke (post-launch — see `SMOKE_TEST_REPORT.md` if you cloned that copy).

Contributions welcome — see `CONTRIBUTING.md`.

## License

[Apache-2.0](LICENSE)
