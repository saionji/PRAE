# PRAE AI Roles

> **Purpose**: Define the standard operating procedures for the two role types (Analyst / Executor) that an LLM plays within PRAE
> **Audience**: LLM (you)
> **Status**: Active (PRAE v1.0)
> **Last updated**: 2026-04-20

---

## 1. General Principles

Within PRAE you always play **one of only two roles**; you cannot play both at once or mix them:

| Role | Core output | Typical tools |
|------|----------|----------|
| Analyst | Hypotheses, experiment design, evidence interpretation, phase recommendations | Read TRACK_LOG, write EXP, write PHASE_GATE |
| Executor | Code, contracts, PDAE unit deliverables | Read MODULE_SPEC, write src/, run PDAE unit gating |

**The role is bound to "the current state of the current track"**, not to your identity for the whole day. You may switch roles repeatedly within the same session.

**Switching roles must be declared explicitly.** When you switch, write one line at the start of your reply:
```
[Switching to Analyst] Handling track research_strategy_momentum (EXPLORING)
```
or:
```
[Switching to Executor] Handling track infra_data_v1 (EXPLORING → LOCKED implementation phase)
```

---

## 2. Analyst SOP

### 2.1 Activation Conditions

Switch to the Analyst role when any of the following conditions is met:

- The track you are currently handling has `state = EXPLORING` (whether infrastructure or research)
- The track you are currently handling has `state = ACTIVE` (a research track in its validation phase)
- You are generating `PHASE_GATE.md` for a phase transition
- You are doing component classification during project startup (filling in `PRAE_INIT.md`)

### 2.2 Inputs (read only these files)

Read in order, no more than 8 in total:
1. The project root `CLAUDE.md` / `AGENTS.md`
2. `prae/PRAE_INIT.md`
3. `prae/track_registry.yaml`
4. The current phase `PHASE_BRIEF.md`
5. The target track's `TRACK_LOG.md`
6. The target track's most recent 2-3 `EXP_NNN.md`
7. (As needed) other tracks' `TRACK_LOG.md`, only if this track depends on them
8. (As needed) external literature excerpts, data samples

If `prae/track_registry.yaml` does not exist, the project may have only completed bootstrap and not yet run `/prae-init` / `prae init`. In that case, first complete `PRAE_INIT.md`, then let the initialization tool generate `track_registry.yaml` and the Phase 0 artifacts.

**Do not read**: PDAE's MODULE_SPEC, or source code under src/ (unless it is to interpret experiment output).

### 2.3 Action List (strictly in order)

#### A. When designing a new experiment for a research track

1. Read `TRACK_LOG.md`, confirm the `hypothesis` field and the "Known Evidence" section
2. Decide which sub-proposition of the hypothesis this experiment will validate
3. Create a new `EXP_NNN.md` under `prae/phases/phase_NN_*/tracks/{track_id}/experiments/` (NNN being the next three-digit sequence number). **Note**: `EXP_NNN.md` is a methodology record file, placed under `prae/`; the experiment code script (`EXP_NNN.py`) is placed under `src/tracks/{track_id}/experiments/`. The two are linked through the same NNN sequence number
4. Fill in `EXP_NNN.md` following the template:
   - `## Goal`: state in one sentence what you want to answer this time
   - `## Method`: data source, time window, parameters, random seed, control group
   - `## Preflight Check`: minimal smoke check, output contract, what is out of scope this time
   - `## Expected Signal`: criteria for success and failure (numerical thresholds or qualitative standards)
   - `## Result` (leave empty for now, fill in after the run)
   - `## Conclusion` (leave empty for now, fill in after the run)
5. Before writing code, first confirm that `Preflight Check` and `Expected Signal` are frozen; implement `EXP_NNN.py` along the minimal runnable path
6. Run the experiment (if you have execution permission), and fill the results into `## Result` and `## Conclusion`
7. Append a summary entry to the "Known Evidence" section of `TRACK_LOG.md`, linking to `EXP_NNN.md`
8. If the evidence triggers a state change (e.g., EXPLORING → ACTIVE), first leave a recommendation in `TRACK_LOG.md`; after the user confirms, call `python3 tools/update_track_state.py ...` or `prae update-track-state ...` to formally commit it

This sequence is an experiment-grade "lightweight PDAE": design first, define the minimal check first, then implement, then accept. Do not upgrade every `EXP_NNN.py` into a full PDAE M1-M3.

#### B. When generating PHASE_GATE.md for a phase transition

1. Read `track_registry.yaml`, list the current state of all tracks
2. Cross-check, item by item, against the gating section for the corresponding phase in `PRAE_PHASE_GATES.md`
3. Write the analysis in `prae/phases/phase_NN_*/PHASE_GATE.md`, including:
   - `## Current Phase Status`: list all tracks and their state
   - `## Gating Conditions Item-by-Item Check`: mark with `- [x]` / `- [ ]`
   - `## Evidence Summary`: cite the conclusions of key experiments
   - `## Recommendation`: `Advance` / `Do not advance`, with reasons
   - `## Pending Human Approval`: leave empty, to be filled in manually with `APPROVED: yes/no` + approver + date
4. At the end of the reply, prompt the user to approve

#### C. When doing project-startup component classification

1. Ask for or read the project requirements statement
2. Write the "Problem Statement" and "Success Criteria" in `prae/PRAE_INIT.md`
3. Decompose the system into components. For each component, judge:
   - Is there uncertainty (algorithm choice, hypothesis validation)? → research track
   - Is it a foreseeable, specifiable supporting capability? → infrastructure track
4. Fill in track entries in the "Infrastructure Tracks" and "Research Tracks" tables of `PRAE_INIT.md`
5. Run `/prae-init` (Claude Code) or `prae init` (Codex), letting `tools/init_project.py` generate `prae/track_registry.yaml` and the Phase 0 artifacts
6. Do not manually copy templates to fake a `track_registry.yaml` or `PHASE_BRIEF.md`; if the tool is missing, first restore the tool, then rerun initialization

### 2.4 Outputs (you are allowed to write/update these files)

- `prae/PRAE_INIT.md` (at project startup)
- `prae/phases/phase_NN_*/PHASE_BRIEF.md`
- `prae/phases/phase_NN_*/PHASE_GATE.md`
- `prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md`
- `prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md` (methodology record)
- `src/tracks/{track_id}/experiments/EXP_NNN.py` (experiment code; research and infrastructure tracks both use this path)
- The `experiments` count and `evidence_summary` in `prae/track_registry.yaml` (a `state` change must go through the formal tool after human approval)

### 2.5 When to Switch to Executor

Switch immediately in the following cases:

- An infrastructure track's technology choice is finalized, and you need to start writing the MODULE_SPEC and implementation code
- A research track is judged `GRADUATED` and a PDAE engineering project needs to be created
- A shared function is imported by a second location and needs to be migrated to `src/shared/` and run through PDAE M3
- Any case requiring modification of actual source code under `src/` (other than `experiments/`)

### 2.6 Prohibitions (the Analyst absolutely never does these)

- Do not manually modify the `state` field of `track_registry.yaml`. Even after user approval, you must go through `update_track_state.py`
- Do not manually change an infrastructure track to `LOCKED`. Locking infrastructure must also go through `lock_infra_track.py` / `prae lock-infra`
- Do not skip human approval and create the next phase's directory on your own
- Do not run a research experiment without a `hypothesis`
- **Do not modify** any file under `src/infra_*/` (absolutely forbidden for LOCKED tracks; for EXPLORING tracks it is the Executor who modifies them)
- Reading `src/infra_*/` is limited to evaluating technical approaches **within Phase 0 technology-choice experiments** (for example, comparing existing code for DuckDB vs Parquet), and is read-only — never modify; the technology-choice experiment scripts are written under `src/tracks/{track_id}/experiments/`, not under `src/infra_*/`
- Do not mix two hypotheses in the same track; recommend splitting instead
- Do not give "it feels OK" judgments; every recommendation must cite an `EXP_NNN.md` or an external fact

---

## 3. Executor SOP

### 3.1 Activation Conditions

Switch to the Executor role when any of the following conditions is met:

- An infrastructure track's technology choice is finalized and it is ready to enter PDAE M1-M3 implementation
- An infrastructure track is in its PDAE implementation phase (the track state is still EXPLORING but about to become LOCKED)
- A research track is judged GRADUATED and a PDAE engineering project needs to be started
- Reusable code needs to be migrated to `src/shared/`, triggering PDAE M3
- `contracts.yaml` needs to be updated

### 3.2 Inputs

1. The target track's `TRACK_LOG.md` (to know why it is being done and what approach was chosen)
2. The target track's `MODULE_SPEC.md` (if it already exists)
3. The target track's `contracts.yaml` (if it already exists)
4. The `contracts.yaml` of related infrastructure tracks
5. PDAE's `PDAE_QUICKSTART.md` and `PDAE_UNIT_GATES.md` (located in `${PDAE_HOME}/`)
6. Existing code under `src/infra_{name}_v{N}/` (if continuing on an existing track)

### 3.3 Action List (strictly in order)

#### A. Infrastructure track EXPLORING → LOCKED

1. Confirm the Analyst has marked "technology choice finalized" in `TRACK_LOG.md`
2. Switch to the PDAE repository and enter the PDAE control thread:
   ```bash
   cd ${PDAE_HOME}
   source .venv/bin/activate
   ```
3. Run the full M1-M3 process per PDAE_QUICKSTART.md:
   - `pm_m1` → `scout_m1` → `architect_m1` → `architect_m2` → `reviewer_m2` → `architect_m3` → `qa_m3` → `coder_m3` → `reviewer_m3`
   - Run `check_unit_gate.py` after each step
4. After PDAE M3 passes entirely, place the code into the PRAE project's `src/infra_{name}_v{N}/`
5. Ensure `contracts.yaml` matches the `src/` structure, and run:
   ```bash
   python3 ${PDAE_HOME}/tools/check_contracts.py \
     --contracts src/infra_{name}_v{N}/contracts.yaml --src src/
   ```
6. After human approval, call the formal tool:
   ```bash
   python3 tools/lock_infra_track.py \
     --project-dir . \
     --track-id infra_{name}_v{N} \
     --approver <approver> \
     --reason "PDAE M3 passed"
   ```
   or:
   ```bash
   prae lock-infra infra_{name}_v{N} --approver <approver> --reason "PDAE M3 passed"
   ```
7. Let the formal tool update `track_registry.yaml`'s `state=LOCKED / locked_at / contracts / module_spec`, and sync the `Decision Log` in `TRACK_LOG.md`
8. After locking is complete, **switch back to Analyst** to continue subsequent work

#### B. Infrastructure track requirement change → open v2

1. **Do not** modify the v1 code
2. Add a new `infra_{name}_v2` entry in `prae/track_registry.yaml`, state=EXPLORING
3. Notify the Analyst: the new track needs a technology-choice experiment
4. Keep v1 LOCKED, continuing to serve dependents that have not yet migrated

#### C. Migrating shared code to `src/shared/`

1. Confirm the trigger condition: the function/module is imported by a **second location**
2. Move the code from `src/tracks/{track_id}/impl/` to `src/shared/{module_name}/`
3. Create a `MODULE_SPEC.md` for the new shared module (PDAE M3 module spec)
4. Run the full PDAE M3 unit:
   ```bash
   python3 tools/check_unit_gate.py --unit architect_m3 --module-spec src/shared/{module_name}/MODULE_SPEC.md
   python3 tools/check_unit_gate.py --unit qa_m3 --module-spec src/shared/{module_name}/MODULE_SPEC.md
   python3 tools/check_unit_gate.py --unit coder_m3 --module-spec src/shared/{module_name}/MODULE_SPEC.md
   python3 tools/check_unit_gate.py --unit reviewer_m3 --module-spec src/shared/{module_name}/MODULE_SPEC.md
   ```
5. Update all imports to point to the new path
6. Run the Contracts Gate once to confirm nothing downstream is broken

#### D. Research track GRADUATED → PDAE engineering project

1. Read the final conclusion in the research track's `TRACK_LOG.md`
2. Start a new project in the PDAE repository: create a Routing Decision per `PDAE_QUICKSTART.md`
3. Use the research track's code as factual input to PDAE `scout_m1` (the code is a validated prototype)
4. Run the full PDAE M1-M3
5. Confirm that the track's state in `prae/track_registry.yaml` is already `GRADUATED` and `concluded_at` is filled in (done by the Analyst after human approval)
6. Append a link to the location of the PDAE engineering project at the end of `TRACK_LOG.md`

### 3.4 Outputs

- All source code under `src/infra_{name}_v{N}/`
- All source code under `src/shared/`
- `src/infra_{name}_v{N}/MODULE_SPEC.md`
- `src/infra_{name}_v{N}/contracts.yaml`
- `src/shared/{module}/MODULE_SPEC.md`
- Changes to the `state` field of `prae/track_registry.yaml` (only when PDAE has passed and compliance conditions are met)
- All M1-M3 artifacts under the PDAE repository

### 3.5 When to Switch Back to Analyst

- PDAE M3 has fully passed and the track is LOCKED
- The v2 track has been created and is awaiting its technology-choice experiment
- The PDAE engineering project has been started and is awaiting subsequent research
- You encounter a case requiring new experiment design or evidence interpretation

### 3.6 Prohibitions (the Executor absolutely never does these)

- Do not modify the source code of a LOCKED infrastructure track (not even a typo; you must open v2)
- Do not skip PDAE gating and modify code directly
- Do not import code from `src/tracks/B/` inside `src/tracks/A/`
- Do not write modules under `experiments/` that will be imported by `impl/`
- Do not start writing the implementation without an explicit technology-choice conclusion in `TRACK_LOG.md`
- Do not advance a phase on your own (phase advancement is always Analyst + human)

---

## 4. Role-Switching Examples

**Example 1**: The project has just started
```
Analyst: read PRAE_INIT.md → find that the technology choice for infra_data_v1 is not yet settled → design EXP_001 to compare DuckDB vs Parquet
Analyst: run the experiment → fill in EXP_001.md → update TRACK_LOG.md → recommend choosing DuckDB
[Switch] → Executor: start from PDAE M1, write MODULE_SPEC, implementation
Executor: PDAE M3 passes → call lock_infra_track.py / prae lock-infra to formally lock
[Switch] → Analyst: start generating the PHASE_GATE for Phase 0 → Phase 1
```

**Example 2**: Mid-way through a research track
```
Analyst: read the TRACK_LOG of research_strategy_momentum → design EXP_007 to validate the high-turnover-rate issue
Analyst: run the experiment → find that a new signal-smoothing function is needed
Analyst: write the function in experiments/smooth.py → find that another track, research_strategy_reversal, also needs it
[Switch] → Executor: migrate smooth.py into src/shared/signal/, run PDAE M3
Executor: M3 passes → update the imports of both tracks
[Switch] → Analyst: continue the result analysis of EXP_007
```

---

## 5. Key Rules Recap

1. You can play only one role at a time
2. Switching roles must be declared explicitly at the start of the reply
3. The Analyst produces decisions and evidence; the Executor produces code and contracts
4. Rules for changing the state field of `track_registry.yaml`:
   - **Research track** (EXPLORING → ACTIVE / KILLED / MERGED / GRADUATED): Analyst recommends → human approves → the **Analyst** calls `update_track_state.py` / `prae update-track-state` to formally update the registry and the `Decision Log`
   - **Infrastructure track** (EXPLORING → LOCKED): Analyst recommends → human approves → the **Executor** calls `lock_infra_track.py` / `prae lock-infra` after PDAE M3 has fully passed to formally update the registry and the `Decision Log`
5. When a hard rule of PRAE_CORE_MODEL.md is violated, stop and prompt the user regardless of role
6. **A research track cannot jump directly from EXPLORING to KILLED**: there must first be at least one experiment that moves the track into ACTIVE before it can be marked KILLED; a KILLED that skips ACTIVE is invalid
