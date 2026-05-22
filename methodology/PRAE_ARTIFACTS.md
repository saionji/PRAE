# PRAE Artifacts

> **Purpose**: A complete inventory of all PRAE artifacts — who creates them, when they are created, how they are updated, their main fields, and how they relate to one another
> **Audience**: The LLM (you)
> **Status**: Active (PRAE v1.0)
> **Last updated**: 2026-04-20

---

## 1. Artifact Overview

PRAE artifacts fall into two broad categories:
- **Methodology artifacts**: located under `prae/`, describing the research process and decisions
- **Code artifacts**: located under `src/`, containing research code and infrastructure code

The table below lists them in reading order. Detailed specifications follow in later sections.

| # | File / path pattern | Creator | When created | Level |
|---|----------------|--------|----------|------|
| 1 | `CLAUDE.md` or `AGENTS.md` | Human (at initialization) | Project startup | Project level |
| 2 | `prae/PRAE_INIT.md` | AI Analyst + human confirmation | Project startup, filled in only once | Project level |
| 3 | `prae/track_registry.yaml` | AI initializes, human + AI maintain jointly | Project startup, continuously updated | Project level |
| 4 | `prae/phases/phase_NN_*/PHASE_BRIEF.md` | AI Analyst | At the start of a phase | Phase level |
| 5 | `prae/phases/phase_NN_*/PHASE_GATE.md` | AI Analyst + human approval | At the end of a phase | Phase level |
| 6 | `prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md` | AI Analyst | When a track enters a phase | Track level |
| 7 | `prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md` | AI Analyst | Each experiment | Experiment level |
| 8 | `src/tracks/{track_id}/experiments/EXP_NNN.py` | AI Analyst | Each experiment (experiment script code) | Experiment level |
| 9 | `src/tracks/{track_id}/impl/*.py` | AI Analyst / Executor | After mature code is moved out of experiments | Implementation level |
| 10 | `src/infra_{name}_v{N}/MODULE_SPEC.md` | AI Executor (running PDAE) | When the infrastructure enters PDAE M3 | Infrastructure level |
| 11 | `src/infra_{name}_v{N}/contracts.yaml` | AI Executor | When the infrastructure enters PDAE M2 | Infrastructure level |
| 12 | `src/shared/{module}/MODULE_SPEC.md` | AI Executor | When code is moved into shared | Shared level |
| 13 | `prae/phases/phase_03_conclusion/CONCLUSION.md` | AI Analyst | Phase 3 | Project level |

---

## 2. Detailed Specifications for Methodology Artifacts

### 2.1 `CLAUDE.md` or `AGENTS.md`

- **Role**: The first-read context when an LLM enters the project
- **Creator**: Human (copies the template when deploying the project-pack)
- **When created**: Project startup
- **Update rule**: Updated by a human whenever there is an important structural change in the project
- **Main fields**:
  - One-line description of the project
  - Relationship to PDAE
  - Quick reference to the PRAE core model
  - Repository directory structure
  - Current phase and next step
  - Common commands
- **Relations**: Points to all methodology documents under `methodology/`

### 2.2 `prae/PRAE_INIT.md`

- **Role**: The problem statement + component classification at project startup
- **Creator**: AI Analyst drafts, human confirms
- **When created**: During project startup, filled in only once
- **Update rule**: In principle, do not change it. If you discover mid-project that a component classification is wrong, append a record to the `CHANGE_LOG` section; do not delete the original content
- **Main fields (required)**:
  - `## Problem Statement`: what the research aims to solve and what the success criteria are
  - `## Component Classification → Infrastructure Tracks`: a table (track ID / description / dependencies)
  - `## Component Classification → Research Tracks`: a table (track ID / hypothesis / infrastructure depended on)
  - `## Phase 0 Success Criteria`: the concrete criteria for judging that all infrastructure is LOCKED
- **Relations**:
  - All track IDs must be synchronized and registered in `track_registry.yaml`
  - The `hypothesis` of each research track must be consistent with the later `TRACK_LOG.md`

### 2.3 `prae/track_registry.yaml`

- **Role**: The **single source of truth** for the state of all tracks
- **Creator**: AI initializes it from `PRAE_INIT.md`
- **When created**: Project startup
- **Update rule**:
  - State field changes: AI proposes → human approves → Executor commits the change to this file
  - experiments count, evidence_summary: AI may update directly
  - `current_phase` field: updated immediately after a phase gate is approved
  - Project wrap-up fields: `ARCHIVED / GRADUATED_TO_PDAE` are written by the terminal-state tool; `CONTINUE` is written by the reopen tool
- **Main fields** (project level, optional):
  - `project_decision`
  - `project_approver`
  - `project_decided_at`
  - `project_reopened_at` (only for `CONTINUE`)
  - `project_finalized_at` (only for a terminal decision)
  - `archived_at` (only for `ARCHIVED`)
- **Main fields** (per track):
  - `id` (required, prefixed with `infra_` or `research_`)
  - `type` (`infrastructure` or `research`)
  - `state` (see PRAE_CORE_MODEL.md § 2)
  - `src` (path to the source code directory)
  - Infrastructure-specific: `module_spec`, `contracts`, `locked_at`
  - Research-specific: `hypothesis`, `depends_on`, `experiments`, `evidence_summary`, `concluded_at`, `merged_into`
- **Relations**:
  - All track IDs are consistent with `PRAE_INIT.md`
  - The `src` path must match the real directory
  - The infrastructure `contracts` must correspond to a contracts.yaml that actually exists

**Example**:
```yaml
project: object-detection
current_cycle: 1
current_phase: phase_01_research
updated: 2026-04-22
project_decision: GRADUATED_TO_PDAE
project_approver: saionji
project_decided_at: 2026-04-22
project_finalized_at: 2026-04-22

tracks:
  - id: infra_data_v1
    type: infrastructure
    state: LOCKED
    src: src/infra_data_v1/
    module_spec: src/infra_data_v1/MODULE_SPEC.md
    contracts: src/infra_data_v1/contracts.yaml
    locked_at: 2026-04-18

  - id: research_detector_cnn
    type: research
    state: ACTIVE
    src: src/tracks/research_detector_cnn/
    hypothesis: "CNN achieves recall ≥ 0.85 in low-SNR scenarios"
    depends_on: [infra_data_v1]
    experiments: 3
    evidence_summary: "Preliminary recall 0.78, F1 0.72; need additional short-window experiments"
```

If the project is judged by a human at `Phase 3` with `DECISION: CONTINUE`, the tool archives the `phase_01/02/03` directories of the old cycle into `prae/history/cycle_N/phases/`, and increments `current_cycle` to the next cycle.

### 2.4 `prae/phases/phase_NN_{name}/PHASE_BRIEF.md`

- **Role**: The goals and success criteria of this phase
- **Creator**: AI Analyst
- **When created**: When creating this phase's directory immediately after the previous phase's PHASE_GATE is approved
- **Update rule**: Minor adjustments are allowed within a phase (for example, adding a research track), but the overall goal of the phase cannot be changed
- **Main fields**:
  - `## Phase Goal`
  - `## Success Criteria` (corresponding to the exit gate)
  - `## Tracks Present in This Phase`
  - `## Key Time Milestones` (optional)
- **Relations**: Points to the PHASE_GATE.md of the phase it belongs to (left empty until it is generated)

### 2.5 `prae/phases/phase_NN_{name}/PHASE_GATE.md`

- **Role**: The decision record and approval trail for a phase transition
- **Creator**: Generated by the AI Analyst; approved by a human
- **When created**: When you believe you can enter the next phase, generated proactively by the AI (or triggered by `/prae-advance-phase`)
- **Update rule**: The filename is fixed as `PHASE_GATE.md`. When regenerating, you may overwrite the same file, but you should preserve the human-filled approval fields in Section 6; after approval, if you want to actually advance the phase, you must invoke the official tool — filling in `APPROVED` alone does not take effect
- **Main fields** (6 sections, see PRAE_PHASE_GATES.md § 2):
  - `**Research Cycle**: cycle_N`
  1. Current phase status
  2. Item-by-item check of gate conditions
  3. Evidence summary
  4. Risks and open items
  5. Recommendation
  6. Pending human approval (the APPROVED field)
- **Relations**:
  - References the states in `track_registry.yaml`
  - References each track's `TRACK_LOG.md` and `EXP_NNN.md`
  - After approval, triggers the `current_phase` update and the creation of the next phase's directory

### 2.6 `prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md`

- **Role**: The narrative of a track within this phase; the hypothesis, known evidence, list of experiments, and current state
- **Creator**: AI Analyst
- **When created**: When the track first appears in a given phase (in Phase 1, every research track must have one)
- **Path rule**: The **only** correct path for `TRACK_LOG.md` is `prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md`. It is a methodology artifact, located under the `prae/` directory tree, **not under `src/`**.
- **Update rule**: Append an entry for every experiment and every state change; research-track state changes should be synchronized here via `update_track_state.py` / `prae update-track-state`; do not delete history
- **Main fields**:
  - `**Research Cycle**: cycle_N` (must be consistent with `track_registry.yaml.current_cycle`)
  - `## Hypothesis` (research track) / `## Selection Goal` (infrastructure track)
  - `## State` + `## Depends On`
  - `## Experiments` (a table: EXP_ID / date / purpose / conclusion / link to the corresponding EXP_NNN.md)
  - `## Evidence Summary` (append a paragraph after each experiment)
  - `## Decision Log` (state-change records: when it changed from EXPLORING to ACTIVE, who proposed it, who approved it)
- **Relations**:
  - References the experiment records `prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md` under the same track
  - `**Research Cycle**` must match the current cycle; after `CONTINUE`, the new cycle's `TRACK_LOG.md` is recreated in the new phase directory, and the old cycle's history remains in `prae/history/cycle_N/phases/`
  - Referenced upward by `PHASE_GATE.md`

### 2.7 `prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md`

- **Role**: The complete methodology record of a single experiment (goal, method, result, conclusion)
- **Creator**: AI Analyst
- **When created**: Whenever a new experiment is started
- **Path rule**: EXP_NNN.md is a **methodology artifact**, located under the `prae/` directory tree, **not under `src/`**. Its paired experiment code `EXP_NNN.py` is under `src/tracks/{track_id}/experiments/`; the two are linked by the same NNN sequence number
- **Update rule**: `## Result` and `## Conclusion` are filled in after the experiment has finished running; they are not changed thereafter
- **Main fields** (required):
  - `## Goal`: a one-line goal
  - `## Method`: data source, time window, random seed, hyperparameters, control group
  - `## Preflight Check`: minimal smoke check, output contract, what is not done this time
  - `## Expected Signal`: success and failure criteria
  - `## Result`: numerical values, chart locations, raw output paths
  - `## Conclusion`: whether the hypothesis is supported / falsified / partially supported, plus a recommendation for the track's state
- **Coding order**: Follow the experiment-grade "lightweight PDAE" process: first `Goal / Method`, then write `Preflight Check` and `Expected Signal`, then implement `EXP_NNN.py`, and finally fill in `Result / Conclusion` according to the acceptance result
- **Numbering rule**: Three digits, starting from EXP_001; numbers are not reclaimed after deletion
- **Relations**: Referenced by the Experiments table in `TRACK_LOG.md`; the link format is the relative path `experiments/EXP_NNN.md`

### 2.8 `prae/phases/phase_03_conclusion/CONCLUSION.md`

- **Role**: The project's final conclusion
- **Creator**: AI Analyst
- **When created**: Phase 3
- **Update rule**: May be revised multiple times until a human decides to archive / graduate
- **Main fields**:
  - `## Project Conclusion`
  - `## Disposition of Each Track`
  - `## PDAE Project Links for Graduated Tracks`
  - `## Unresolved Issues`
  - `## Final Decision`
  - `APPROVED: <pending | yes | no>`
  - `DECISION: <ARCHIVED | GRADUATED_TO_PDAE | CONTINUE>`
  - `APPROVER: <user name or identifier>`
  - `APPROVED_AT: <YYYY-MM-DD>`
  - `COMMENT: <optional, additional human notes>`
- **Relations**:
  - Summarizes the final conclusions of all tracks' `TRACK_LOG.md`
  - Created after the `PHASE_GATE.md` (Phase 2→3) is approved

---

## 3. Detailed Specifications for Code Artifacts

### 3.1 `src/tracks/{track_id}/experiments/EXP_NNN.py` (or other scripts)

- **Role**: The executable script for an experiment
- **Creator**: AI Analyst
- **Update rule**: Every change is treated as a new experiment (a new `EXP_NNN.md` + a new `EXP_NNN.py`); do not repeatedly edit the same file
- **Key constraint**: **Cannot be imported by other code** (Research Gate rule 5)
- **Recommended process**: Before implementing, first write the `Preflight Check` clearly in the paired `EXP_NNN.md`; the code should prioritize being minimally runnable and satisfying the output contract, without engineering ahead of time

### 3.3 `src/tracks/{track_id}/impl/*.py`

- **Role**: Stable implementation code distilled from experiments/
- **Creator**: AI Executor (when the Analyst discovers that distillation is needed, switch to the Executor role first before creating it)
- **When created**: When the same piece of logic is reused across multiple EXPs, it is migrated here
- **Update rule**: A normal Python module; when it is imported by a second other track, it **must** be moved into `src/shared/`
- **Key constraint**: May import the public symbols declared in `src/shared/` and in the infrastructure track's `contracts.yaml`; may not import its own track's `experiments/`

### 3.4 `src/infra_{name}_v{N}/MODULE_SPEC.md`

- **Role**: The PDAE module spec for an infrastructure track
- **Creator**: AI Executor (when running PDAE M1)
- **When created**: When an infrastructure track enters the PDAE implementation period
- **Update rule**: Read-only after LOCKED; when a change is needed, open a new v2 track and a new MODULE_SPEC
- **Main fields**: Follow the PDAE `MODULE_SPEC_TEMPLATE.md` format
- **Relations**: Corresponds strictly to `contracts.yaml`; matches the path in the `module_spec` field of `track_registry.yaml`

### 3.5 `src/infra_{name}_v{N}/contracts.yaml`

- **Role**: The public interface contract that an infrastructure track exposes externally
- **Creator**: AI Executor
- **When created**: The PDAE M2 phase
- **Update rule**: Read-only after LOCKED; `check_contracts.py` verifies that no imports cross the boundary
- **Main fields**: Follow the PDAE `CONTRACTS_SPEC.md`
- **Relations**:
  - All research tracks may only import the symbols declared in this file
  - Aligned with the real source code symbols (enforced by `check_contracts.py`)

### 3.6 `src/shared/{module}/MODULE_SPEC.md`

- **Role**: The PDAE M3 module spec for code shared across tracks
- **Creator**: AI Executor
- **When created**: When some code is imported by a second track and moved into shared
- **Update rule**: Changes must go through PDAE M3 (`architect_m3 → qa_m3 → coder_m3 → reviewer_m3`)
- **Relations**: Imported by the `impl/` code of at least two tracks

---

## 4. Artifact Relationship Diagram

```
CLAUDE.md
   │
   ▼
PRAE_INIT.md ──────────────┐
   │                       │
   ▼                       ▼
track_registry.yaml ◀──▶ PHASE_BRIEF.md ──▶ PHASE_GATE.md
   │                       │
   │                       ▼
   │                    TRACK_LOG.md ──▶ EXP_NNN.md ──▶ EXP_NNN.py
   │                                         │
   │                                         ▼
   │                                      impl/*.py ──▶ shared/{module}/MODULE_SPEC.md
   │
   ▼
infra_{name}_v{N}/MODULE_SPEC.md
infra_{name}_v{N}/contracts.yaml ◀── enforced by check_contracts.py ── all code under src/
```

---

## 5. Naming Conventions

| Object | Rule | Example |
|------|------|------|
| Infrastructure track ID | `infra_{name}_v{N}` | `infra_data_v1`, `infra_sim_v2` |
| Research track ID | `research_{topic}_{variant}` | `research_detector_cnn`, `research_strategy_momentum` |
| Phase directory | `phase_{NN}_{name}` | `phase_00_infra`, `phase_01_research` |
| Experiment file | `EXP_{NNN}.md` / `EXP_{NNN}.py` | `EXP_001.md`, `EXP_047.py` |
| shared module | `shared/{snake_case_name}/` | `shared/signal_utils/` |

---

## 6. Recap of Key Rules

1. Every artifact has a clear creator and update rule — do not cross the boundary
2. `track_registry.yaml` is the single source of truth
3. All artifacts of a LOCKED infrastructure track (source code, MODULE_SPEC, contracts.yaml) are read-only
4. Scripts under `experiments/` are never imported by other code
5. `PHASE_GATE.md` always uses the same filename; preserve the approval area when regenerating, and advance the phase via the official tool after approval
6. The reference relationships between artifacts must stay consistent (track IDs, paths, phase names)
