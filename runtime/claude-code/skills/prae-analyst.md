---
name: prae-analyst
description: Use when a research track is in EXPLORING or ACTIVE state — activates Analyst SOP for experiment design, evidence interpretation, and phase gate generation
---

# PRAE Analyst SOP (Claude Code)

> Install path: `.claude/skills/prae-analyst.md` (deployed automatically by prae-bootstrap)
> Spec reference: `methodology/PRAE_ROLES.md §2`, `runtime/abstract/ANALYST_ROLE.prompt.md`

This skill is the in-project Analyst behavior entry the model reads — not an install-command entry.
If the project does not yet have `prae/track_registry.yaml`, the project may only have been bootstrapped; run `/prae-init` first, and do not treat this skill as a signal that the project is already fully initialized.

---

## Announce on activation

Write at the start of your reply:
```
[switch to Analyst] working on track {track_id} ({state})
```

---

## Standard flow A: new experiment (track EXPLORING or ACTIVE)

### Step 1: Read context (at most 8 files)

```
1. prae/PRAE_INIT.md
2. prae/track_registry.yaml (if missing, run /prae-init first)
3. The current phase's PHASE_BRIEF.md
4. The target track's TRACK_LOG.md
5. The latest 1-3 EXP_NNN.md files (read the newest first)
6. The depended-on infrastructure's contracts.yaml (when you need to know the API)
```

If the project only has `prae/PRAE_INIT.md` and no `prae/track_registry.yaml` yet, stop experiment design and run `/prae-init` to generate the initialization artifacts.

### Step 2: Identify the evidence gap

In TRACK_LOG.md's Evidence Summary, look for:
- Core questions the hypothesis has not yet answered
- The "next step" suggestion left by the previous experiment

### Step 3: Design the experiment (the "design freeze" of lightweight PDAE)

Create the EXP record (fill Goal / Method / Preflight Check / Expected Signal first; leave Result empty):

```bash
# Determine the experiment number (with N existing EXPs, create EXP_{N+1:03d})
TRACK_ID="{{track_id}}"
PHASE="{{phase_NN_name}}"
EXP_DIR="prae/phases/${PHASE}/tracks/${TRACK_ID}/experiments"
mkdir -p "${EXP_DIR}"
# Copy the template
cp "prae/templates/EXP_NNN.template.md" \
   "${EXP_DIR}/EXP_$(printf '%03d' N).md"
```

Or call `/prae-new-exp {track_id}` directly.

### Step 4: Define the minimal check first, then implement the experiment code

```bash
CODE_DIR="src/tracks/${TRACK_ID}/experiments"
mkdir -p "${CODE_DIR}"
# Create EXP_NNN.py, using only the public interface declared in contracts.yaml
```

**Constraints:**
- Only import the public symbols declared in `src/infra_*/`'s contracts.yaml
- Do not import other EXP_NNN.py files (lateral dependencies are forbidden)
- Hardcoded parameters are allowed (do not over-abstract during the research phase)
- Finish writing `EXP_NNN.md`'s `## Preflight Check` section before writing code
- Implement the minimal runnable path first, satisfying the Preflight smoke check and output contract
- Do not abstract into `impl/` prematurely; only switch to Executor extraction when a stable reuse need appears

### Step 5: Run the experiment, accept it against Expected Signal, then fill in results

Fill in `EXP_NNN.md`'s `## Result` and `## Conclusion` sections.

### Step 6: Update TRACK_LOG.md

Append to the following sections (do not delete history):
- `## Experiments` table: add a row
- `## Evidence Summary`: add a paragraph (date + key findings)

### Step 7: State-change recommendation (if needed)

If the evidence supports EXPLORING → ACTIVE or ACTIVE → KILLED/MERGED/GRADUATED:

1. Record the recommendation in TRACK_LOG.md's `## Decision Log`
2. **After the user approves**, call `/prae-update-track-state` or `python3 tools/update_track_state.py`
3. Let the formal tool update `track_registry.yaml`, `concluded_at` / `merged_into`, and sync the `Decision Log`

---

## Standard flow B: generate PHASE_GATE.md

Prefer calling `/prae-advance-phase`. If the slash command is unavailable, call the formal tools directly:

1. `python3 tools/generate_phase_gate.py --project-dir .`
2. `python3 tools/check_phase_gate.py --project-dir .`
3. **Stop and wait for the user to fill `APPROVED: yes` in section 6**

Do not fall back to the old path of copying a template or hand-creating `PHASE_GATE.md`.

---

## Hard prohibitions (violating any → stop and tell the user)

- Modifying any file under `src/infra_*/` (read-only; Phase 0 selection experiments are an exception but still must not modify it)
- Creating `src/tracks/{track_id}/impl/*.py` (requires switching to Executor)
- Modifying `src/shared/` (requires switching to Executor + PDAE M3)
- Marking a research track directly from EXPLORING to KILLED (it must pass through ACTIVE)
- Updating `current_phase` without an `APPROVED: yes`
