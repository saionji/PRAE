# PRAE Quick Start

> **Purpose**: The single primary operating manual for PRAE; from project startup to graduation, it explains in real execution order how an LLM runs the complete flow
> **Audience**: The LLM (you)
> **Status**: Active (PRAE v1.0)
> **Last updated**: 2026-04-21

---

## 1. One-Line Positioning

PRAE governs **"which research route is worth pursuing"**, PDAE governs **"how to build the code well"**.
Once you finish this page, you can start executing the methodology in any PRAE research project.

PRAE is not a development process; it is a research decision protocol. Your primary output is not code, but:
- Evidence records (experiment records, hypothesis validation results)
- Decision recommendations (PHASE_GATE.md, track state change recommendations)
- Role switching (Analyst ↔ Executor)

---

## 2. First Time Entering a Project: Required Reading Order

What is described here is the **required reading order after the model enters a project**, not the order of project installation commands.
If the project has not yet adopted PRAE, the project operation entry point is still `/prae-bootstrap` / `prae bootstrap`.

When you are dropped into an unfamiliar PRAE research project, read the files in the following order (do not skip, do not reorder):

1. **The `CLAUDE.md` or `AGENTS.md` in the project root**
   Establishes project context. If it does not exist, the project has not deployed a project-pack, and you need to create one first per PRAE_ARTIFACTS.md.

2. **`methodology/PRAE_CORE_MODEL.md` (same directory as this file)**
   Master the authoritative definitions of the two track types, four phases, and the state machine.

3. **`methodology/PRAE_ROLES.md`**
   Confirm whether you should currently act as the Analyst or the Executor.

4. **The project's `prae/PRAE_INIT.md`**
   Read the project's problem statement and component classification. If it does not exist, your current job is to produce it.

5. **The project's `prae/track_registry.yaml`**
   Read the current state of all tracks. This is the **single source of truth**; any track state defers to this file.
   If the file does not exist, the project may have only completed bootstrap and not yet run `/prae-init`; complete initialization first.

6. **The current phase directory `prae/phases/phase_NN_*/PHASE_BRIEF.md`**
   Read the current phase goal and success criteria.

7. **The relevant tracks' `TRACK_LOG.md` and the most recent `experiments/EXP_NNN.md`**
   Only read the tracks involved in your current task; do not read all of them.

**Context management**: Read at most 5-8 files at a time. If there are many tracks, pick only the ones relevant to the current task.

---

## 3. Complete Phase Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRAE complete lifecycle                     │
└─────────────────────────────────────────────────────────────────┘

[Project startup]
   │
   │ Fill in PRAE_INIT.md, run /prae-init to generate track_registry.yaml and Phase 0 artifacts
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 0  Infrastructure readiness period                         │
│ Goal: all infra_* tracks state = LOCKED                          │
│ AI role: Analyst (selection) → Executor (PDAE M1-M3 impl)         │
│ Gate: all infrastructure tracks LOCKED                            │
└─────────────────────────────────────────────────────────────────┘
   │
   │ Phase Gate 0→1: AI writes PHASE_GATE.md, human approval
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1  Algorithm exploration period                            │
│ Goal: start multiple research tracks in parallel, accumulate signal│
│ AI role: Analyst (literature search, experiment design, result interpretation)│
│ Gate: ≥1 research track state = ACTIVE                            │
└─────────────────────────────────────────────────────────────────┘
   │
   │ Phase Gate 1→2: AI writes PHASE_GATE.md, human approval
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2  Algorithm validation period                             │
│ Goal: converge to the leading approach, kill/merge tracks         │
│ AI role: Analyst + Executor (mature tracks start engineering)     │
│ Gate: all ACTIVE research tracks have a clear conclusion          │
└─────────────────────────────────────────────────────────────────┘
   │
   │ Phase Gate 2→3: AI writes PHASE_GATE.md, human approval
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3  Conclusion period                                       │
│ Goal: form the final conclusion, archive or graduate             │
│ AI role: documentation cleanup / PDAE routing                     │
│ Gate: human decision                                             │
└─────────────────────────────────────────────────────────────────┘
   │
   ├── Archive: project ends
   └── Graduate (GRADUATED): switch to the PDAE repository to create an engineering project
```

---

## 4. Typical LLM Actions in Each Phase

### 4.1 Phase 0 Typical Actions (Infrastructure Readiness)

In this phase, 90% of your time is as the Executor, with a small amount as the Analyst. In order:

1. Read the infrastructure tracks listed in `PRAE_INIT.md` and confirm the goal of each `infra_*`.
2. For each infrastructure track with state=EXPLORING:
   - If the track has not yet materialized its directory, first call `prae new-track <track_id>` to create the current phase directory and `TRACK_LOG.md`
   - Analyst role: call `prae new-exp <track_id>` to create selection experiment skeletons (EXP_001, EXP_002)
   - Analyst role: after running the experiments, call `prae record-result <track_id> <EXP_ID>` to write the results back to `TRACK_LOG.md`
   - After the selection is decided: switch to the Executor role and trigger the complete PDAE M1-M3 flow (see PRAE_ROLES.md § Executor SOP).
   - After PDAE M3 passes: get human approval, then call `prae lock-infra` / `tools/lock_infra_track.py` to formally change the track from `EXPLORING` to `LOCKED`.
3. When all `infra_*` tracks are LOCKED, call `prae advance-phase` to generate `phases/phase_00_infra/PHASE_GATE.md`.
4. Wait for human approval; after approval, call `prae advance-phase` again — this should directly verify the approved gate and formally advance to `phase_01_research`. If you bypass the wrapper, you can also run `python3 tools/check_phase_gate.py --project-dir . --check-approved` followed by `python3 tools/advance_phase.py --project-dir .` directly.

### 4.2 Phase 1 Typical Actions (Algorithm Exploration)

In this phase you act almost exclusively as the Analyst. In order:

1. Read the research track list in `PRAE_INIT.md`. If a new research track is not yet registered, first call `prae add-track ...`; for already-registered tracks, call `prae new-track <track_id>` to materialize the current phase directory and `TRACK_LOG.md`.
2. Call `prae new-exp <track_id>` to create `EXP_NNN.md` and `EXP_NNN.py`; first write out the experiment design clearly, then implement and run it.
3. After the experiment completes, call `prae record-result <track_id> <EXP_ID>` to write the results, evidence summary, and pending-approval state recommendation back to `TRACK_LOG.md`.
4. When a positive signal is confirmed, first form a state recommendation; after human approval, call `prae update-track-state` / `tools/update_track_state.py` to formally change the track from `EXPLORING` to `ACTIVE`.
5. When ≥1 track is ACTIVE and sufficient evidence has accumulated, call `prae advance-phase` to generate `PHASE_GATE.md`; after approval, call the same command again, or run `tools/check_phase_gate.py --check-approved` + `tools/advance_phase.py` directly to formally advance to Phase 2.

### 4.3 Phase 2 Typical Actions (Algorithm Validation)

Analyst + partly Executor. In order:

1. For each ACTIVE research track:
   - Read the historical evidence in `TRACK_LOG.md`
   - Call `prae new-exp <track_id>` to design validation experiments (usually stricter: longer time window, more samples, control groups)
   - After running, call `prae record-result <track_id> <EXP_ID>` to form a recommendation of `KILLED` / `MERGED` / `GRADUATED` / continue observing
2. After human approval, call `prae update-track-state ...` for the terminal states that need to be committed; if `MERGED`, you must include `--merged-into ...`.
3. If a track is judged `GRADUATED`: switch to the Executor role and prepare to graduate to PDAE; single-track graduation registration goes through `prae graduate <track_id>`.
4. Once all ACTIVE tracks have a conclusion, call `prae advance-phase` to generate the Phase 2→3 `PHASE_GATE.md`; after approval, call the same command again, or run `tools/check_phase_gate.py --check-approved` + `tools/advance_phase.py` directly to formally advance to Phase 3.

### 4.4 Phase 3 Typical Actions (Conclusion)

Mainly documentation cleanup. In order:

1. After entering `phase_03_conclusion`, the official tooling generates `phases/phase_03_conclusion/CONCLUSION.md`; the AI builds on this to add project-level conclusions and PDAE routing information.
2. For each `GRADUATED` track: switch to the PDAE repository and start the engineering project; when done, call `prae graduate <track_id>` to write the trace back to PRAE.
3. The human fills in the structured final decision in `CONCLUSION.md`:
   - `ARCHIVED` / `GRADUATED_TO_PDAE`: call `prae finalize`
   - `CONTINUE`: call `prae reopen`
4. The logs of `KILLED` / `MERGED` tracks remain traceable; do not delete them.

---

## 5. Slash Command Index Table

(This table lists the commands provided by the PRAE execution layer; for the concrete implementation see `runtime/claude-code/commands/`)

| Command | Purpose | When to use |
|------|------|--------|
| `/prae-bootstrap` | Deploy the PRAE minimal skeleton, templates, tools, and runtime commands into the current research project | When installing PRAE in a new project for the first time |
| `/prae-init` | Generate `track_registry.yaml` and Phase 0 artifacts (`PHASE_BRIEF.md`, infrastructure `TRACK_LOG.md`) from `PRAE_INIT.md` | When the project starts up for the first time |
| `/prae-add-track <id>` | Formally register a new track in `track_registry.yaml` | When you need to add an infrastructure or research track that is not yet registered |
| `/prae-new-track <id>` | Create the current phase directory and `TRACK_LOG.md` skeleton for an already-registered track | When enabling a track after `init`, or when entering a new phase |
| `/prae-new-exp <track_id>` | Create the EXP_NNN.md record file and EXP_NNN.py code skeleton under the current track | Each time you start a new experiment |
| `/prae-record-result <track_id> <exp_id>` | Write the experiment result into TRACK_LOG, update evidence_summary; if there is a state recommendation, write it into the pending-approval `Decision Log` | When recording results after an experiment finishes |
| `/prae-lock-infra <track_id>` | After human approval, formally update an infrastructure track to `LOCKED` and write to the `Decision Log` | After Phase 0 infrastructure passes PDAE M3 |
| `/prae-update-track-state <track_id> <state>` | After human approval, formally update a research track's state and write to the `Decision Log` | When a recommended state change needs to be committed |
| `/prae-advance-phase` | The first call generates PHASE_GATE.md; when approved, verifies the gate and formally advances the phase | When you believe you can move to the next phase |
| `/prae-graduate <track_id>` | Verify graduation conditions, switch to the PDAE repository to create an engineering project, update the registry | When a research track passes validation and needs to graduate |
| `/prae-finalize` | Verify and register the project's terminal-state decision | When the Phase 3 human decision is `ARCHIVED` or `GRADUATED_TO_PDAE` |
| `/prae-reopen` | Per a `CONTINUE` decision, archive the old round and reopen back to Phase 1 | When the Phase 3 human decision is `CONTINUE` |

**What to do if you cannot find the corresponding command**: Prefer restoring the wrapper or directly calling the corresponding `tools/*.py`. Only when the repository is damaged, the tool is missing, and the user explicitly requests it should you do a temporary manual workaround; once the workaround is complete, return to the official tool path as soon as possible.

---

## 6. Tool Invocation Cheat Sheet

```bash
# Phase Gate check (check the gating conditions for advancing to the next phase)
python3 tools/check_phase_gate.py --project-dir . --phase 0   # Phase 0→1
python3 tools/check_phase_gate.py --project-dir . --phase 1   # Phase 1→2
python3 tools/check_phase_gate.py --project-dir . --check-approved  # check approved

# Research Gate check
python3 tools/check_research_gate.py --project-dir . --track-id research_strategy_momentum

# Track state consistency
python3 tools/check_track_status.py --project-dir .

# Contracts Gate (deployed to the local tools/ by bootstrap)
python3 tools/check_contracts.py \
  --contracts src/infra_data_v1/contracts.yaml --src src/

# PDAE M1-M3 (called when locking an infrastructure track)
cd ${PDAE_HOME}
python3 tools/check_unit_gate.py --unit architect_m3 \
  --module-spec /path/to/project/src/infra_data_v1/MODULE_SPEC.md
```

---

## 7. When to Switch Roles

- You are reading literature, writing hypotheses, designing experiments, interpreting results → **Analyst**
- You are writing infrastructure code, running PDAE units, filling in MODULE_SPEC.md → **Executor**
- When a track crosses from `EXPLORING` into the PDAE flow, switch from Analyst to Executor
- After PDAE is complete and the track is LOCKED, return to the Analyst to continue observing subsequent research tracks

See `PRAE_ROLES.md` for details.

---

## 8. Common Questions and Failure Recovery

### Q1: `track_registry.yaml` and some `TRACK_LOG.md` state are inconsistent
Defer to `track_registry.yaml`. It is the single source of truth. Correct the state field at the top of `TRACK_LOG.md` to align with the registry.

### Q2: After an infrastructure track is LOCKED, you discover a requirement change
**Do not modify v1.** Add an `infra_{name}_v2` entry in `track_registry.yaml` with state = EXPLORING. Keep v1 LOCKED and read-only. All research tracks depending on v1 continue using v1 for now, switching track by track once v2 is stable.

### Q3: A research track has two routes at once, and you want to explore which is better
Do not compare them within the same track. **Split them into two independent research tracks** (for example `research_momentum_daily` and `research_momentum_weekly`), run experiments for each, and decide KILL / MERGE / GRADUATE in Phase 2.

### Q4: You discover two research tracks use the same helper function
That function has now been imported in a second place; it must be moved into `src/shared/`, and the PDAE M3 gate must be triggered on that file. Do not cross-import between `src/tracks/*/`.

### Q5: The scripts under `experiments/` are getting messier and messier
That is normal. The area under `experiments/` is a LOOSE zone; it only records results and is not a dependency source for subsequent code. Only code in `impl/` or moved into `shared/` is subject to gating.

### Q6: PHASE_GATE.md is rejected by the human
Read the rejection reason and fix it per the "Common Blockers" section of `PRAE_PHASE_GATES.md`. It is usually insufficient evidence, an unclear track conclusion, or infrastructure that is not all LOCKED.

### Q7: You are unsure which Phase you are currently in
Look at the `current_phase` field in `track_registry.yaml` (if this field is absent, look at the largest phase directory number under `phases/`). If the latest `PHASE_GATE.md` is in "pending approval", you are still in the current phase.

### Q8: Contracts Gate fails
Read the error; it is usually research code that imported an internal symbol of an infrastructure track. The fix: access only through the public interface declared in the infrastructure track's `contracts.yaml`.

---

## 9. Recap of This Page's Key Rules

1. This page is the single primary operating manual for PRAE
2. `track_registry.yaml` is the single source of truth for track state
3. An infrastructure track cannot be modified after it is LOCKED; for changes, open a v2
4. Research track conclusions must be supported by evidence, not subjective judgment
5. Phase transitions must go through human approval; the AI only generates recommendations
6. Research code under `experiments/` is LOOSE; reused code moves into `shared/` and is governed by PDAE
