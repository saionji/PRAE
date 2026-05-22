---
name: prae-guard
description: Use at the start of any PRAE research project session — enforces PRAE behavioral contracts, role discipline, and gate rules throughout the conversation
---

# PRAE Guard — Behavioral Contract

> Install path: `.claude/skills/prae-guard.md` (deployed automatically by prae-bootstrap)
> Spec reference: `methodology/PRAE_ROLES.md`, `methodology/PRAE_CORE_MODEL.md`

First, distinguish three kinds of "entry point":
- This skill: the in-project conversation-context entry the model reads
- `/prae-bootstrap`: the project install entry
- `/prae-init`: the project state-initialization entry

So seeing this skill does NOT mean the project is fully initialized. If `prae/track_registry.yaml` is missing, it only means the project may still be sitting right after bootstrap.

---

## Session startup checks

When entering a PRAE project, run these checks first, in order:

```bash
# 1. Confirm the minimal bootstrap skeleton exists
ls prae/PRAE_INIT.md || { echo "prae/PRAE_INIT.md not found — run /prae-bootstrap first"; exit 1; }

# 2. Find track_registry.yaml (if missing, the project has not been init'd)
ls prae/track_registry.yaml || {
  echo "track_registry.yaml not found. The project may only have been bootstrapped."
  echo "Fill in prae/PRAE_INIT.md first, then run /prae-init."
  exit 1
}

# 3. Read the current phase
python3 -c "
import yaml
r = yaml.safe_load(open('prae/track_registry.yaml'))
print(f'current phase: {r[\"current_phase\"]}')
print(f'track count: {len(r[\"tracks\"])}')
for t in r['tracks']:
    print(f'  {t[\"id\"]} [{t[\"type\"]}] -> {t[\"state\"]}')
"
```

Show the output to the user, then ask: "Which track do you want to work on, or what operation should I perform?"

---

## Role rules (hard constraints)

**You play exactly one role at a time.** Every switch must be announced at the start of your reply:
```
[switch to Analyst] working on track research_strategy_momentum (EXPLORING)
[switch to Executor] working on track infra_data_v1 (EXPLORING → LOCKED engineering phase)
```

| Role | Activation condition | Forbidden actions |
|------|---------------------|-------------------|
| Analyst | track state = EXPLORING or ACTIVE; generating PHASE_GATE | modifying src/infra_*/; creating impl/*.py; editing an approved PHASE_GATE |
| Executor | infrastructure engineering; impl/ code extraction; shared migration | writing experiment code; directly advancing a research track's state |

---

## Gate rules (must not be bypassed)

1. **Phases never auto-advance**: after generating PHASE_GATE.md you must stop and wait for `APPROVED: yes`
2. **Research track EXPLORING → KILLED is forbidden**: it must pass through ACTIVE (at least one experiment)
3. **Before an ACTIVE track reaches a terminal state** it must pass the Research Gate (`tools/check_research_gate.py`)
4. **Before infrastructure reaches LOCKED** it must complete PDAE M1-M3 and have contracts.yaml + MODULE_SPEC.md
5. **LOCKED infrastructure cannot be modified**: open a v2 track for new requirements

---

## File path quick reference

| File | Path | Created by |
|------|------|-----------|
| Experiment record EXP_NNN.md | `prae/phases/.../tracks/{track_id}/experiments/EXP_NNN.md` | Analyst |
| Experiment code EXP_NNN.py | `src/tracks/{track_id}/experiments/EXP_NNN.py` | Analyst |
| Track log | `prae/phases/.../tracks/{track_id}/TRACK_LOG.md` | Analyst |
| Phase gate | `prae/phases/phase_NN_*/PHASE_GATE.md` | Analyst |
| Infrastructure code | `src/infra_{name}_v{N}/` | Executor |
| Stable implementation | `src/tracks/{track_id}/impl/*.py` | Executor |

---

## Available slash commands

| Command | Purpose |
|---------|---------|
| `/prae-bootstrap` | Deploy the PRAE skeleton, templates, tools, and commands into the current research project |
| `/prae-init` | Generate `track_registry.yaml` and Phase 0 artifacts from `PRAE_INIT.md` |
| `/prae-add-track <id>` | Formally register a new track in `track_registry.yaml` |
| `/prae-new-track <id>` | Create the current-phase directory and TRACK_LOG.md for a registered track |
| `/prae-new-exp <track_id>` | Create a new experiment |
| `/prae-record-result <track_id> <exp_id>` | Fill in experiment results |
| `/prae-lock-infra <track_id>` | Formally lock an infrastructure track after human approval |
| `/prae-update-track-state <track_id> <state>` | Formally update a research track's state after human approval |
| `/prae-advance-phase` | First call generates PHASE_GATE.md; once approved, validates the gate and formally advances the phase |
| `/prae-graduate <track_id>` | Start a track's graduation to PDAE |
| `/prae-finalize` | Record the project's final-state decision |
| `/prae-reopen` | Reopen to Phase 1 based on a CONTINUE decision |

---

## Handling emergencies

- Found a state inconsistency (yaml disagrees with files) → stop, tell the user, do not auto-fix
- A required file is missing → report the missing path explicitly, do not guess and create it
- A tool errors out → print the full error, do not silently ignore it
