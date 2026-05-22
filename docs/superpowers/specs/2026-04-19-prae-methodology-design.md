# PRAE Methodology Design Spec

**Date:** 2026-04-19
**Status:** Design Approved, Pre-Implementation
**Author:** saionji + Claude Code

---

## 1. Positioning

**PRAE (Protocol-Driven Research & Experimentation)** is an AI-assisted scientific research methodology.

It is not a software engineering tool, but rather:
> a way to let an LLM act as a research assistant, managing the decision process of "which path is worth pursuing"

Core loop:
```
problem statement → infrastructure ready → parallel algorithm exploration → evidence-driven convergence → conclusion / graduation
```

Applicable scenarios (domain-agnostic):
- Quantitative trading: data pipeline (infrastructure) + strategy/model (research layer)
- Robot control: sensors/simulation/host controller (infrastructure) + control algorithm (research layer)
- Object detection: data processing pipeline (infrastructure) + detection algorithm (research layer)

---

## 2. Relationship to PDAE

| Dimension | PRAE | PDAE |
|------|------|------|
| What it governs | which path is worth pursuing (research decisions) | how to do it well (engineering quality) |
| End point | conclusion / graduation decision | a deliverable software unit |
| Core question | Does the hypothesis hold? | Does the implementation match the spec? |
| Uncertainty | high (exploration) | low (delivery) |

**When PRAE uses PDAE:**
- When an infrastructure track is locked → invoke the full PDAE M1→M3 engineering flow
- Shared code (shared/) governance → invoke the PDAE M3 unit gate
- Contract compliance checks → reuse `check_contracts.py`

**PDAE repository location:** `${PDAE_HOME}/`

---

## 3. Core Model

### 3.1 Two Kinds of Tracks

**Infrastructure Track**
- Purpose: provide a reliable data/environment/tooling foundation for research
- Lifecycle: `EXPLORING → [PDAE M1-M3] → LOCKED`
- Change rule: do not unlock; open a new v2 track; the v1 directory is read-only
- After locking: governed by PDAE gates, has a contracts.yaml, any modification goes through the PDAE flow

**Research Track**
- Purpose: test algorithm/strategy hypotheses in parallel, accumulate evidence
- Lifecycle: `EXPLORING → KILLED / MERGED / GRADUATED`
- Graduation rule: decided by a human, no quantitative threshold

### 3.2 The Four Phases

```
Phase 0  Infrastructure Readiness
         Goal: engineer and lock all necessary infrastructure
         Gate: all infrastructure tracks have state = LOCKED
         AI roles: Analyst (selection recommendations) + Executor (PDAE implementation)

Phase 1  Algorithm Exploration
         Goal: launch multiple research tracks in parallel, accumulate signal quickly
         Gate: AI recommends advancing after analyzing evidence + human approval
         AI role: Analyst (literature search, experiment design, result interpretation)

Phase 2  Algorithm Validation
         Goal: converge to the leading approach, kill/merge tracks
         Gate: AI recommends a conclusion after analysis + human approval
         AI roles: Analyst + Executor (mature tracks begin engineering)

Phase 3  Conclusion
         Goal: form a final conclusion, decide to archive or graduate into PDAE
         Gate: decided by a human
         AI role: documentation cleanup, PDAE routing for the graduation plan
```

### 3.3 Track State Machine

```
Infrastructure track:
  EXPLORING ──[experiment confirms direction]──▶ [PDAE M1-M3] ──▶ LOCKED
  LOCKED ──[requirement change]──▶ create a new v2 track (v1 stays LOCKED)

Research track:
  EXPLORING ──[positive signal]──▶ ACTIVE
  ACTIVE ──[clear failure]──▶ KILLED
  ACTIVE ──[complementary to another track]──▶ MERGED
  ACTIVE ──[conclusion confirmed]──▶ GRADUATED
```

### 3.4 AI Roles Bound to Track State

| Track State | AI Role | Concrete Work |
|----------|---------|----------|
| EXPLORING | Analyst | literature search, experiment design, result interpretation, selection recommendations |
| LOCKED (implementation period) | Executor | write code, run PDAE M1-M3 units |
| KILLED | — | archive the experiment record |
| GRADUATED | Executor | create the PDAE engineering project |

---

## 4. Four-Layer Gating System

| Gate | What It Governs | Tool | Trigger |
|------|--------|------|----------|
| PRAE Phase Gate | phase transition decisions | `check_phase_gate.py` (to be built) | AI recommends + human approves |
| Research Gate | minimum quality of research code | `check_research_gate.py` (to be built) | automatic, before commit |
| Contracts Gate | infrastructure boundary compliance | `check_contracts.py` (reused from PDAE) | automatic, before commit |
| PDAE M1-M3 Gate | engineering quality of infrastructure/shared code | full PDAE suite | explicitly triggered |

### Research Gate Checklist

```
✓ TRACK_LOG.md has a record of this experiment (goal, method, result, conclusion)
✓ At least one smoke test (runs successfully, output format is correct)
✓ Experiment parameters are recorded (random seed, hyperparameters, data time range)
✓ check_contracts passes (does not violate infrastructure contracts)
✗ No coverage requirement
✗ No design review requirement
```

---

## 5. Code and Document Structure

```
{project-name}/
├── CLAUDE.md                    ← AI session context (copied from the PRAE template)
├── prae/                        ← methodology files
│   ├── PRAE_INIT.md             ← problem statement + component classification (filled in at project start)
│   ├── track_registry.yaml      ← master table of all track states (single source of truth)
│   └── phases/
│       ├── phase_00_infra/
│       │   ├── PHASE_BRIEF.md   ← this phase's goal and success criteria
│       │   ├── PHASE_GATE.md    ← AI-generated phase analysis (archived after human approval)
│       │   └── tracks/
│       │       └── {track_id}/
│       │           ├── TRACK_LOG.md        ← hypothesis, experiment list, evidence, state
│       │           └── experiments/
│       │               └── EXP_001.md      ← a single experiment record
│       └── phase_01_research/
│           └── ...
└── src/                         ← all code
    ├── infra_{name}_v1/         ← infrastructure code (read-only after LOCKED)
    ├── infra_{name}_v2/         ← created on a version upgrade
    ├── shared/                  ← code shared across tracks (PDAE M3 gated)
    └── tracks/
        └── {track_id}/          ← research-track code (internally LOOSE)
            ├── experiments/     ← experiment scripts (not imported, disposable)
            └── impl/            ← implementation code that has matured
```

### Code Governance Rules

- Scripts under `experiments/`: fully LOOSE, record results only, not imported
- Code under `impl/` or `tracks/{id}/` that is imported by a second place: must be moved into `shared/`, triggering PDAE M3
- `infra_*/` directories: read-only after LOCKED, changes open a v2

---

## 6. PRAE_INIT.md Format

At project start, the researcher fills this out once:

```markdown
# {project name} — PRAE Initialization Document

## Problem Statement
[what research problem to solve, and what the success criteria are]

## Component Classification

### Infrastructure Tracks
| Track ID | Description | Depends On |
|--------|------|------|
| infra_data_v1 | data collection and storage | — |

### Research Tracks
| Track ID | Hypothesis | Infrastructure Depended On |
|--------|------|---------------|
| research_strategy_momentum | the momentum factor is effective | infra_data_v1 |

## Phase 0 Success Criteria
[the concrete criteria for judging that all infrastructure tracks are LOCKED]
```

---

## 7. track_registry.yaml Format

```yaml
project: {project-name}
updated: 2026-04-19

tracks:
  - id: infra_data_v1
    type: infrastructure
    state: LOCKED          # EXPLORING | LOCKED
    src: src/infra_data_v1/
    module_spec: src/infra_data_v1/MODULE_SPEC.md
    contracts: src/infra_data_v1/contracts.yaml
    locked_at: 2026-04-20

  - id: research_strategy_momentum
    type: research
    state: ACTIVE          # EXPLORING | ACTIVE | KILLED | MERGED | GRADUATED
    src: src/tracks/research_strategy_momentum/
    hypothesis: "The momentum factor is effective on A-share daily frequency, Sharpe > 1.0"
    depends_on: [infra_data_v1]
    experiments: 7
    evidence_summary: "Backtest Sharpe 1.2, but turnover is too high"
```

---

## 8. Tools to Be Built

| Tool | Purpose | Priority |
|------|------|--------|
| `tools/check_phase_gate.py` | validate PHASE_GATE.md structure and the legality of the phase transition | P1 |
| `tools/check_research_gate.py` | validate the minimum quality standard of a research track | P1 |
| `tools/check_track_status.py` | check track_registry.yaml consistency | P2 |
| `tools/init_project.py` | initialize a new PRAE project from a template | P2 |
| `project-pack/` | template package deployable to a specific research project | P3 |

Reused PDAE tools (no need to rebuild):
- `check_contracts.py` → call or copy directly from the PDAE repository
- The full PDAE M1-M3 flow → use directly when an infrastructure track is locked

---

## 9. Design Decision Record

| Decision | Choice | Reason |
|------|------|------|
| Infrastructure change strategy | versioning (new v2 track) | guarantees historical experiments are reproducible, v1 is not broken |
| Phase transition trigger | AI recommends + human approves | research judgment cannot be fully automated |
| Research code governance | four-layer grading (LOOSE/Research Gate/Contracts/PDAE) | avoid over-heavy constraints that stifle exploration |
| Relationship between PRAE and PDAE | two parallel governance dimensions, linked through the lock event | not tightly coupled, each governs its own scope |
| Graduation criteria | decided by a human, no quantitative threshold | the judgment of research value cannot be quantified |
