# PRAE Core Model

> **Purpose**: The authoritative definition document for the PRAE methodology; precise specifications for tracks, states, phases, and gates
> **Audience**: LLM (you)
> **Status**: Active (PRAE v1.0)
> **Last updated**: 2026-04-19

This document is the **definition layer**, not a tutorial. When concepts conflict, this document takes precedence.

---

## 1. Full definitions of the two track types

PRAE breaks a research project into several **tracks**. Every track must strictly belong to one of the following two types:

### 1.1 Infrastructure Track

**Definition**: A track that provides research with a reliable data / environment / tooling foundation.

**Fields** (required in `track_registry.yaml`):
| Field | Type | Description |
|------|------|------|
| `id` | string | Must start with the `infra_` prefix and include a version number (`infra_data_v1`) |
| `type` | `"infrastructure"` | Fixed value |
| `state` | enum | `EXPLORING` or `LOCKED`; no other legal values |
| `src` | path | Source directory path, format `src/infra_{name}_v{N}/` |
| `module_spec` | path | Points to the PDAE MODULE_SPEC.md |
| `contracts` | path | Points to contracts.yaml |
| `locked_at` | date | Required when state=LOCKED; must be empty or absent when state=EXPLORING |

**Lifecycle**:
```
EXPLORING ──[selection confirmed + PDAE M1-M3 passed]──▶ LOCKED
LOCKED    ──[requirement change]──────────────────────▶ create infra_{name}_v2 (v1 stays LOCKED)
```

**Constraints (hard rules)**:
- Once `state = LOCKED`, the track's source directory `src/infra_{name}_v{N}/` becomes read-only
- A LOCKED track's `contracts.yaml` becomes a contract; all downstream consumers must obey it
- When a LOCKED track needs changes, **never unlock it**; instead create a v2 track
- v1 and v2 can coexist. Until migration is complete, v1 continues to serve research tracks that have not yet migrated

### 1.2 Research Track

**Definition**: A parallel experiment space that carries a single research hypothesis.

**Fields**:
| Field | Type | Description |
|------|------|------|
| `id` | string | Must start with the `research_` prefix (`research_strategy_momentum`) |
| `type` | `"research"` | Fixed value |
| `state` | enum | `EXPLORING` / `ACTIVE` / `KILLED` / `MERGED` / `GRADUATED` |
| `src` | path | Source directory path, format `src/tracks/{track_id}/` |
| `hypothesis` | string | An explicit, falsifiable hypothesis |
| `depends_on` | list[string] | List of infrastructure track IDs it depends on |
| `experiments` | int | Number of experiments already run |
| `evidence_summary` | string | A one-sentence summary of the current evidence |
| `concluded_at` | date | Required when state ∈ {KILLED, MERGED, GRADUATED} |

**Lifecycle**:
```
EXPLORING ──[positive signal]──▶ ACTIVE
ACTIVE ──[clear failure]──────────▶ KILLED    (terminal)
ACTIVE ──[complements another track]──▶ MERGED    (terminal)
ACTIVE ──[conclusion firm, worth engineering]──▶ GRADUATED  (terminal, triggers PDAE)
```

**Constraints**:
- `KILLED` / `MERGED` / `GRADUATED` are terminal states; they cannot revert to `ACTIVE` or `EXPLORING`
- A research track can have only one hypothesis. When exploring two hypotheses at once, you must split them into two research tracks
- A research track's `depends_on` can only reference infrastructure tracks with state=LOCKED

---

## 2. State machine (legal and illegal transitions)

### 2.1 Infrastructure track state transitions

| Current state | Allowed transitions | Forbidden transitions | Notes |
|----------|----------|----------|------|
| EXPLORING | LOCKED | Any other | Must pass all of PDAE M1-M3 |
| LOCKED | (none) | Any state | LOCKED is terminal; for changes, open a v2 |

**Illegal transitions**:
- `LOCKED → EXPLORING`: Forbidden. Any "unlock to modify" intent must be redirected to creating a v2 track
- `EXPLORING → any other name`: No other states exist

### 2.2 Research track state transitions

| Current state | Allowed transitions | Forbidden transitions | Notes |
|----------|----------|----------|------|
| EXPLORING | ACTIVE | KILLED, MERGED, GRADUATED | Requires a positive signal before going ACTIVE |
| ACTIVE | KILLED, MERGED, GRADUATED | EXPLORING | Move forward, do not revert |
| KILLED | (none) | Any state | Terminal |
| MERGED | (none) | Any state | Terminal |
| GRADUATED | (none) | Any state | Terminal; triggers a PDAE engineering project |

**Special cases**:
- If a misjudgment makes you want to "restore" a KILLED track: **not allowed** to modify the state field; instead create a new `research_{new ID}`, and explain in its `TRACK_LOG.md` which KILLED track it inherits from
- `EXPLORING → KILLED` skipping ACTIVE: not allowed. Even to kill it, it must enter ACTIVE to leave at least one experiment record, otherwise there is no evidence to review

---

## 3. Full definitions of the four phases

### 3.1 Phase 0 — Infrastructure Readiness

- **Goal**: Push all infrastructure tracks declared in `PRAE_INIT.md` to `LOCKED`
- **Entry prerequisite**: The project has completed initialization of `PRAE_INIT.md` and `track_registry.yaml`
- **Exit gate**: All tracks with `type=infrastructure` have `state=LOCKED`
- **AI roles**: Analyst (selection research) → Executor (PDAE M1-M3 implementation)
- **Typical artifacts**: Selection experiment records for each `infra_*` track, MODULE_SPEC.md, contracts.yaml
- **Multiple infrastructure tracks may advance in parallel**

### 3.2 Phase 1 — Algorithm Exploration

- **Goal**: Launch multiple research tracks in parallel and quickly accumulate signals
- **Entry prerequisite**: Phase 0 PHASE_GATE.md has received human approval
- **Exit gate**: ≥1 research track has `state=ACTIVE` and PHASE_GATE.md has received human approval
- **AI roles**: Primarily the Analyst (literature search, experiment design, result interpretation)
- **Typical artifacts**: The first batch of EXP records for each research track, summaries of positive signals

### 3.3 Phase 2 — Algorithm Validation

- **Goal**: Converge to the leading approach; eliminate or merge tracks
- **Entry prerequisite**: Phase 1 PHASE_GATE.md has received human approval
- **Exit gate**: All `ACTIVE` research tracks have a clear conclusion (KILLED / MERGED / GRADUATED) and PHASE_GATE.md has received human approval
- **AI roles**: Analyst (rigorous validation of experiment design and result interpretation) + Executor (start PDAE preparation for GRADUATED tracks)
- **Typical artifacts**: Validation experiment records, track conclusion decision table

### 3.4 Phase 3 — Conclusion

- **Goal**: Form the final conclusion; archive or graduate to PDAE
- **Entry prerequisite**: Phase 2 PHASE_GATE.md has received human approval
- **Exit gate**: Human decision (no automatic AI judgment)
- **AI roles**: Documentation cleanup; execute PDAE routing for GRADUATED tracks
- **Typical artifacts**: `CONCLUSION.md`, initialization materials for the PDAE engineering project

---

## 4. The four-layer gate system (authoritative table)

| # | Gate name | What it governs | Tool | Who triggers | Blocking |
|---|----------|--------|------|--------|----------|
| 1 | PRAE Phase Gate | Phase N → Phase N+1 transition decision | `tools/check_phase_gate.py` | AI-generated + human approval | Yes (blocks the next phase) |
| 2 | Research Gate | Minimum quality of a research track (experiment record, smoke test, parameter logging) | `tools/check_research_gate.py` | Automatic, before a research track commit | Yes (blocks the research track commit) |
| 3 | Contracts Gate | Infrastructure track boundary compliance (research code does not violate contracts) | `tools/check_contracts.py` (reused from PDAE, available) | Automatic, before any commit involving infrastructure calls | Yes |
| 4 | PDAE M1-M3 Gate | Engineering quality of infrastructure tracks and shared code | The full PDAE process (available) | Explicitly triggered | Yes (blocks `EXPLORING → LOCKED`) |

**Recommended invocation order**:
- Research track commit: Research Gate → Contracts Gate
- Infrastructure track LOCKED: PDAE M3 Gate → Contracts Gate
- Phase transition: Phase Gate (each track's own gates should already have passed before this)

**The 5 checks of the Research Gate**:
```
✓ TRACK_LOG.md has a record of this experiment (goal, method, result, conclusion)
✓ At least one smoke test (runs successfully, output format correct)
✓ Experiment parameters logged (random seed, hyperparameters, data time range)
✓ check_contracts passes (does not violate infrastructure contracts)
✓ Experiment scripts live under experiments/ (not imported by other code)
✗ Coverage not required
✗ Design review not required
```

See `PRAE_RESEARCH_GATE.md` for details.

---

## 5. Governance tiers of code directories

| Directory | Constraint level | Governed by | Allowed operations |
|------|----------|------|-----------|
| `src/infra_{name}_v{N}/` (LOCKED) | Strictest | PDAE + Contracts Gate | Read-only; changes require a v2 |
| `src/infra_{name}_v{N}/` (EXPLORING) | Strict | Selection experiments; must pass PDAE M1-M3 before LOCK | Modifiable, but the goal is to freeze it |
| `src/shared/` | Strict | PDAE M3 unit gate | Both additions and modifications go through PDAE M3 |
| `src/tracks/{track_id}/impl/` | Medium | Research Gate + Contracts Gate | Modifiable; must migrate to shared/ when imported a second time |
| `src/tracks/{track_id}/experiments/` | LOOSE | Research Gate only | Freely modified or deleted; **must not be imported by other code** |

**Key constraints**:
- Scripts under `experiments/` **cannot be imported by `impl/` or other tracks**. Violating this rule is blocked by the Contracts Gate / Research Gate
- The moment a function or module is **imported a second time**, it must be migrated into `shared/`, triggering PDAE M3
- Two research tracks **must not import each other directly**; they may only interact through `shared/` or through the public interfaces of infrastructure tracks

---

## 6. Summary of key constraints (hard rules)

The following rules are hard constraints of the PRAE methodology; violating them is considered a breach of governance:

1. **LOCKED immutability rule**: Once an infrastructure track is LOCKED, its `src/infra_{name}_v{N}/` directory is read-only
2. **v2 rule**: When infrastructure requirements change, **create a v2** track rather than unlocking v1
3. **Single source of truth rule**: Track state is authoritative in `track_registry.yaml`; when any other file conflicts, correct those files
4. **No cross-import between research tracks rule**: Shared code must go into `shared/`; `src/tracks/A/` importing `src/tracks/B/` is forbidden
5. **experiments/ non-importable rule**: Scripts under this directory are throwaway; importing them breaks reproducibility
6. **Terminal state irreversibility rule**: KILLED / MERGED / GRADUATED / LOCKED are all terminal states
7. **Human approval rule**: Every Phase Gate must receive human approval; the AI only generates recommendations and never advances a phase directly
8. **Hypothesis must be falsifiable rule**: Each research track's `hypothesis` must be a statement that evidence can falsify; it cannot be an open-ended phrasing like "explore X a bit"
9. **Dependencies must be LOCKED rule**: When a research track enters `ACTIVE`, all infrastructure tracks declared in `depends_on` must be in the `LOCKED` state. During initialization (Phase 0), declaring a dependency on a track that is not yet LOCKED is allowed, but that research track must not be activated (cannot move from EXPLORING to ACTIVE) until all its dependencies are LOCKED

---

## 7. The boundary with PDAE

PRAE governs **decisions**, PDAE governs **implementation**. There are only two handoff points:

| Handoff event | The PRAE side | The PDAE side |
|---------|-----------|-----------|
| Infrastructure track `EXPLORING → LOCKED` | Produces the MODULE_SPEC.md skeleton and the contracts.yaml draft | Runs through M1-M3 and produces a qualified implementation |
| Research track `ACTIVE → GRADUATED` | Freezes the track code, organizes the requirement input | Starts a new M1-M3 process from scratch or from the research code |

PRAE does not interfere with PDAE's internal process, and PDAE does not interfere with PRAE's phase progression.

---

## 8. Glossary (use consistently)

| Term | Meaning | Do not write as |
|------|------|----------|
| Track | An independent research or infrastructure work line | experiment group, branch |
| Phase | One of Phase 0/1/2/3 | milestone, quarter |
| Experiment / EXP | A reproducible run with a complete parameter record | a quick run, a try |
| Evidence | The part of experiment results that supports or falsifies the hypothesis | intuition, gut feeling |
| Graduate | A research track reaches engineering-ready conditions and starts PDAE | launch, deploy |
| Infrastructure | Non-algorithmic foundations such as data pipelines, simulators, databases | the underlying layer, the platform |
