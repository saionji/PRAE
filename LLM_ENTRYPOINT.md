# LLM Context Entry Point

This file is the **model context entry point for the PRAE repository**.  
If you are an LLM entering this repository for the first time, read this file first, then continue reading in the order given here.

## Entry-Point Definitions

- `LLM_ENTRYPOINT.md`: model context entry point
- `prae bootstrap` / `/prae-bootstrap`: project installation entry point
- `prae init` / `/prae-init`: project state initialization entry point

---

## 1. First Determine Which Scenario You Are In

### Scenario A: You are working inside this repository

That is, your current directory is `PRAE/` itself.  
In this case you are facing the **PRAE framework repository**, not a specific research project.

Your goal is usually one of the following:
- Understand the PRAE methodology itself
- Modify `tools/`, `runtime/`, `methodology/`
- Explain how to use this framework
- Fix gates / CLI / templates / tests

### Scenario B: You are working inside a "research project that uses PRAE"

That is, your current directory is not the PRAE repository but some business / research project, which contains:
- `prae/`
- `tools/`
- `AGENTS.md` or `CLAUDE.md`

In this case you are facing a **project that consumes PRAE**.  
Your goal is usually:
- Initialize the research project
- Open a new track / new experiment
- Record experiment results
- Advance a phase
- Produce a final conclusion / reopen

---

## 2. If You Are in the PRAE Framework Repository, Read in This Order

### Minimal required reading order

1. `README.md`
2. `methodology/PRAE_QUICKSTART.md`
3. `methodology/PRAE_CORE_MODEL.md`
4. `methodology/PRAE_ROLES.md`

### If you are going to modify the framework implementation, continue reading

5. `CLAUDE.md`
6. `runtime/codex/bin/prae`
7. The scripts in `tools/` directly relevant to your task
8. The corresponding unit / integration tests in `tests/`

### Quick reference for directory responsibilities

- `methodology/`: rules SSOT
- `tools/`: formal execution logic
- `runtime/`: command, prompt, and skill shells for Claude / Codex
- `project-pack/`: the deployment package dropped into research projects at bootstrap time
- `tests/`: behavior regression

---

## 3. If You Are in a Project That Consumes PRAE, Read in This Order

1. The `AGENTS.md` or `CLAUDE.md` in the project root
2. `prae/PRAE_INIT.md`
3. `prae/track_registry.yaml`
4. The current phase's `PHASE_BRIEF.md`
5. The target track's `TRACK_LOG.md`
6. The most recent `EXP_NNN.md`

If `prae/track_registry.yaml` does not exist, the project has likely only done bootstrap and has not been initialized yet.  
In that case, first complete `prae/PRAE_INIT.md`, then run initialization.

---

## 4. The Shortest Path to Using PRAE

Starting from this section, what we describe is the **project operation entry point**, not the model file entry point.  
In other words: the model reads this file first when it enters the repository for the first time; the first command to actually install PRAE in a project is still `bootstrap`.

If you are a human using PRAE in a research project, the shortest path is:

1. `bootstrap`
2. Fill out `prae/PRAE_INIT.md`
3. `init`
4. Phase 0: `new-track` / `new-exp` (infrastructure selection experiments) → `record-result` → `lock-infra`
5. After all infrastructure tracks are `LOCKED`, `advance-phase`
6. Phase 1: for already-registered research tracks use `new-track` → `new-exp` → `record-result`; for a brand-new hypothesis, run `add-track` first
7. After the user approves, `update-track-state`
8. `advance-phase`
9. `graduate / finalize / reopen`

### Codex CLI Entry Point

Main entry-point file:
- `runtime/codex/bin/prae`

Typical commands:

```bash
prae bootstrap
prae init
prae new-track infra_data_v1
prae new-exp infra_data_v1 --title "DuckDB selection experiment"
prae record-result infra_data_v1 EXP_001
prae lock-infra infra_data_v1 --approver saionji --reason "PDAE M3 passed"
prae advance-phase
prae add-track research_strategy_reversal --type research --hypothesis "The reversal factor is effective on A-share ETFs" --depends-on infra_data_v1
prae new-track research_strategy_momentum
prae new-exp research_strategy_momentum --title "First momentum experiment"
prae record-result research_strategy_momentum EXP_001
prae update-track-state research_strategy_momentum ACTIVE --approver saionji --reason "EXP_001 positive signal"
prae advance-phase
```

### Claude Code Entry Point

The main entry points are slash commands:
- `/prae-bootstrap`
- `/prae-init`
- `/prae-add-track`
- `/prae-new-track`
- `/prae-new-exp`
- `/prae-record-result`
- `/prae-lock-infra`
- `/prae-update-track-state`
- `/prae-advance-phase`
- `/prae-graduate`
- `/prae-finalize`
- `/prae-reopen`

---

## 5. The Hard Rules You Must Remember

1. Do not skip a gate.
2. Do not manually modify a research track's `state`; state changes go through `update_track_state.py` / `prae update-track-state`.
3. Do not manually modify an infrastructure track's `LOCKED` confirmation; locking goes through `lock_infra_track.py` / `prae lock-infra`.
4. After `prae init` the project is still in `phase_00_infra` by default; before Phase 0 is approved, do not directly create research-track experiments.
5. `new-track` only creates the current-phase directory for an already-registered track; for a brand-new track, run `add-track` first.
6. A research track cannot terminate directly from `EXPLORING → KILLED`; it must pass through `ACTIVE` first.
7. An `ACTIVE` track must pass the Research Gate before entering a terminal state.
8. `LOCKED` infrastructure cannot be modified directly; to change it, open a v2.
9. Experiment code follows the "lightweight PDAE" sequence: design first, define the Preflight first, then implement, then verify.

---

## 6. Minimal Startup Instruction for an LLM

If you want to get another LLM up to speed quickly, send it the block below directly:

```text
First read LLM_ENTRYPOINT.md in the repository root, and build your context strictly following its "file reading order" and "hard rules".

If you are currently in the PRAE framework repository:
- First read README.md
- Then read methodology/PRAE_QUICKSTART.md, PRAE_CORE_MODEL.md, PRAE_ROLES.md
- Then read the tools/, runtime/, tests/ directly relevant to your task

If you are currently in a research project that uses PRAE:
- First read AGENTS.md/CLAUDE.md
- Then read prae/PRAE_INIT.md, prae/track_registry.yaml, the current phase's PHASE_BRIEF.md, the target track's TRACK_LOG.md, and the most recent EXP_NNN.md

Strictly follow:
- Do not skip a gate
- Do not manually change a research track's state
- Do not manually set an infrastructure track to LOCKED; you must use lock_infra_track.py / prae lock-infra
- After prae init the project is still in phase_00_infra by default; do not directly start research experiments before Phase 0 is approved
- State changes must go through update_track_state.py / prae update-track-state
- EXPLORING cannot go directly to KILLED
- An ACTIVE track must pass the Research Gate before entering a terminal state
```

If you want to copy a ready-made version directly, you can also use these two files in the root directory:
- `CODEX_START_PROMPT.md`
- `CLAUDE_START_PROMPT.md`

---

## 7. The Boundary of This One File

This file is responsible only for **getting you into the correct context as fast as possible**.  
It is not a complete methodology document, nor the SSOT for execution conventions.

If this file conflicts with the following documents, those take precedence:
- `methodology/PRAE_CORE_MODEL.md`
- `methodology/PRAE_ROLES.md`
- `methodology/PRAE_PHASE_GATES.md`
- `methodology/PRAE_RESEARCH_GATE.md`
