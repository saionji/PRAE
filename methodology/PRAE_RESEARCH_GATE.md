# PRAE Research Gate

> **Purpose**: Detailed rules and remediation guide for the minimum quality gate of research tracks
> **Audience**: LLM (you)
> **Status**: Active (PRAE v1.0)
> **Last updated**: 2026-04-20

---

## 1. Why the Research Gate exists

Research code and engineering code differ fundamentally:
- Engineering code aims for "correctness"; research code aims for "reproducibility and interpretability"
- Engineering code requires coverage and review; research code requires only records, parameters, and a smoke test
- Engineering code tolerates no contract violations; research code absolutely tolerates no leakage into infrastructure

The Research Gate is the **minimum baseline**. It does not pursue engineering quality; it only requires:
- Traceable evidence (complete experiment records)
- The ability to run through once (smoke test)
- No infrastructure contamination (no contract violations)
- No breakage of reproducibility (nothing under `experiments/` is imported)

**Tool**: `tools/check_research_gate.py`.

**Recommended coding order**: For experiment code, adopt a "lightweight PDAE" process rather than the full PDAE M1-M3:
1. First write `Goal / Method`
2. First write `Preflight Check` (minimal smoke check + output contract)
3. First write `Expected Signal`
4. Then implement `EXP_NNN.py`
5. After running, fill in `Result / Conclusion` based on the acceptance outcome

The goal of this is to reduce rework, not to turn experiment scripts into engineered code.

---

## 2. The five rules in detail

### Rule 1: TRACK_LOG.md has a record of this experiment

**Requirement**: After every experiment run, you must add an entry to the "Known evidence" or "Experiment list" section of the corresponding track's `TRACK_LOG.md`, containing at least:

- The current project cycle: `**Research cycle**: cycle_N`, which must match `track_registry.yaml.current_cycle`
- Goal (what this experiment is meant to answer)
- Method (brief description, not the complete steps)
- Result (key numbers or conclusions)
- Conclusion (supports / refutes / partially supports the hypothesis)
- Link to the full `EXP_NNN.md`

**Why**: `TRACK_LOG.md` is the track-level narrative, letting a person see within 5 minutes what this track has done and where it stands. Not updating it is equivalent to never having done the work.

**Passing example**:
```markdown
## Known evidence

- EXP_003 (2026-04-25): Tested a pure momentum factor on A-share daily data, backtest Sharpe 1.2, but turnover 400%.
  Conclusion: signal is effective but cost is too high. → [EXP_003.md](experiments/EXP_003.md)
- EXP_004 (2026-04-28): After applying a 5-day smoothing to the signal, Sharpe dropped to 0.9, turnover dropped to 120%.
  Conclusion: smoothing reduces signal strength but still retains a positive return. → [EXP_004.md](experiments/EXP_004.md)
```

**Violating example**:
```markdown
## Known evidence

- Ran some momentum experiments, looks okay.
```
(Missing goal, method, and numerical conclusion; cannot be traced to a specific experiment)

**Remediation**: Go back to `TRACK_LOG.md` and complete an entry for each experiment following the structure of the passing example, and correct `**Research cycle**: cycle_N`. If the original experiment parameters have been lost, clearly mark in the entry "parameters not recorded, needs re-run".

---

### Rule 2: At least one smoke test (runs through, output format correct)

**Requirement**: Under each research track's `src/tracks/{track_id}/experiments/`, there must exist at least one script (usually `EXP_001.py` or the corresponding experiment entry point) that satisfies:

- Runs through in a clean environment without errors
- Produces a result a human can inspect (numbers, charts, tables, JSON all acceptable)
- If there is randomness, the output is reproducible (see Rule 3)

**Why**: This prevents a track that "only has a paper plan and no executable experiment" from sneaking in and occupying resources. A research track must have actually run at least once.

**Passing example**:
```python
# src/tracks/research_strategy_momentum/experiments/EXP_001.py
import pandas as pd
from src.infra_data_v1.api import load_daily_bars

def main():
    bars = load_daily_bars(symbol="AAPL", start="2020-01-01", end="2020-12-31")
    momentum = bars["close"].pct_change(20)
    print(f"Mean momentum: {momentum.mean():.4f}")
    print(f"Std momentum: {momentum.std():.4f}")

if __name__ == "__main__":
    main()
```

**Violating example**: `TRACK_LOG.md` only states "plan to compare momentum and reversal", but the `experiments/` directory is empty.

**Remediation**: Write at least one minimal runnable script, run it once, and save the output. This is not asking you to do a full experiment — only to prove that "this track is executable".

---

### Rule 3: Experiment parameters and minimal checks are recorded (random seed, hyperparameters, data time range, Preflight)

**Requirement**: The `## Method` section of each `EXP_NNN.md` must list:

- Random seed (`seed=42`, or an explicit declaration of "no randomness")
- All key hyperparameters (learning rate, window length, threshold, model size, etc.)
- Data source and time range ("A-share daily, 2020-01-01 to 2023-12-31")
- Control group setup (if any)

And the `## Preflight Check` section must list:
- The minimal smoke check (at least running through and producing what output)
- The output contract (minimum requirements for stdout / files / charts)

**Why**: Without this information, the experiment is not reproducible. When re-run later, if the result differs, you cannot tell whether the code was modified or the parameters drifted.

**Passing example**:
```markdown
## Method

- Data source: infra_data_v1.load_daily_bars
- Universe: CSI 300 constituent stocks (the list as of 2024-01-01)
- Time window: 2018-01-01 to 2023-12-31
- Random seed: seed=42 (used for sklearn cross-validation)
- Momentum window: 20 days
- Holding period: 5 days
- Turnover cost: 3bps/single side
- Control group: fully random stock selection (seed=42, the same seed)
```

**Violating example**:
```markdown
## Method

Tested a momentum strategy on the past year of data, picked a recent 20-day window.
```
(Missing seed, no specific dates, no data source stated, no control group declared)

**Remediation**: Go back to the original code and complete the parameters and `Preflight Check`. If no seed was set at the time, mark "runs before 2026-04-25 did not set a random seed, results are for reference only, needs re-run".

---

### Rule 4: check_contracts passes (no infrastructure contract violation)

**Requirement**: Before submitting, run:
```bash
python3 tools/check_contracts.py \
  --contracts src/infra_data_v1/contracts.yaml --src src/
```
Return code 0, no violations.

**Why**: If a research track directly imports an infrastructure track's internal symbols, it will:
- Break the infrastructure's encapsulation boundary
- Make the infrastructure unable to safely upgrade to v2
- Contaminate the maintainability of the entire project

All research code may only access infrastructure capabilities through the infrastructure's **public contract**.

**Passing example**:
```python
# src/tracks/research_strategy_momentum/impl/signal.py
from src.infra_data_v1.api import load_daily_bars  # public interface, declared in contracts.yaml
```

**Violating example**:
```python
# src/tracks/research_strategy_momentum/impl/signal.py
from src.infra_data_v1.internal._cache import _read_parquet  # private internal symbol
```
`check_contracts.py` will report an error: `violation: src.infra_data_v1.internal._cache is not exported`.

**Remediation**:
- Replace with a public interface allowed by contracts.yaml
- If the public interface is insufficient, communicate with the infrastructure maintainer and extend the public contract under v2 rules (modifying v1 is forbidden)

---

### Rule 5: Experiment scripts stay under experiments/ (not imported by other code)

**Requirement**: Any `.py` file under `src/tracks/{track_id}/experiments/` **must not be** imported by other code. They are "throwaway" scripts; once the result is recorded, they should no longer be reused.

**Why**:
- `experiments/` scripts often hardcode parameters without interface abstraction
- Reusing them causes important implementation to hide inside experiment scripts, unable to enter the gating system
- Reproducibility depends on "the environment at the time this script was run"; once imported, upstream changes will silently affect downstream

**How the tool checks**: `check_research_gate.py` scans all Python files, checking whether any import statement points from a non-experiments/ file to experiments/.

**Passing example**:
```
src/tracks/research_strategy_momentum/
├── experiments/
│   ├── EXP_001.py      # runs standalone, not imported
│   ├── EXP_002.py      # runs standalone
│   └── EXP_001.md
└── impl/
    └── signal.py       # being imported by EXP_003.py is fine (reverse import)
```

**Violating example**:
```python
# src/tracks/research_strategy_momentum/impl/signal.py
from ..experiments.EXP_002 import calc_momentum  # forbidden
```

**Remediation**:
- Move the function that needs to be reused from `experiments/EXP_002.py` into `impl/`
- If the moved function also needs to be used by another track: move it further into `src/shared/`, which triggers PDAE M3 (see PRAE_ROLES.md Executor SOP C)

---

## 3. What the Research Gate does not check

The following items are explicitly declared **not checked**; do not waste time on them in research tracks:

| Not checked | Reason |
|--------|------|
| Test coverage | Research code only needs to be readable and re-runnable; engineering coverage is not required |
| Design review | Research does not do full M1/M2-style reviews; before an experiment, only a lightweight `Goal/Method/Preflight/Expected Signal` freeze is done |
| Code style (lint / format) | Optional, non-blocking; recommended but not used as a gate |
| Docstrings | Parameter records go in `EXP_NNN.md`, not in docstrings |
| Performance benchmarks | During the research period, only "runs to completion" matters; performance optimization is left to the graduation period |

---

## 4. Tool invocation

### 4.1 Local invocation

```bash
# Run the Research Gate on a single research track
python3 tools/check_research_gate.py \
  --track-id research_strategy_momentum \
  --project-dir .
```

Return codes:
- `0`: passed
- `1`: violates any of rules 1-5 (error details printed to stderr)
- `2`: tool error (track_id does not exist, etc.)

### 4.2 Manual checklist before the tool is in place

You (the AI) can check yourself against the checklist below:

```
[ ] Rule 1: TRACK_LOG.md has a complete entry for this experiment (goal/method/result/conclusion/link)
[ ] Rule 2: at least one script under experiments/ runs through, with a record of the most recent run
[ ] Rule 3: the latest EXP_NNN.md Method section fully lists seed/hyperparameters/data range
[ ] Rule 4: python3 check_contracts.py returns 0
[ ] Rule 5: no import from impl/ or other tracks points to experiments/
```

Only when all items are checked can it be considered as having passed the Research Gate.

### 4.3 CI invocation

The CI of a research project should run `check_research_gate.py` on the involved tracks for every PR. A failure blocks the merge.

---

## 5. Handling procedure after a violation

When a violation is found, handle it as follows:

1. **Do not merge or continue advancing** the current track
2. Identify the specific rule violated (which of 1-5)
3. Follow the "Remediation" paragraph of the corresponding rule in this document
4. Re-run the Research Gate
5. Continue once it passes

**Common pitfall**: trying to bypass the Research Gate (for example, treating the rules as suggestions). This causes the subsequent Phase Gate review to fail, because PHASE_GATE.md needs to list "every ACTIVE track passes the Research Gate" as a necessary condition.

---

## 6. Key rules recap

1. The Research Gate is the minimum baseline for research tracks, not an engineering quality check
2. None of the five rules can be omitted
3. Scripts under `experiments/` are never imported by other code
4. The infrastructure contract is checked independently by `check_contracts.py` and is a component of the Gate
5. In an environment without automated tooling, self-check against the manual checklist in §4.2
6. **The Research Gate applies only to tracks in the ACTIVE state**: an EXPLORING track cannot skip ACTIVE and go straight to KILLED; at least one experiment (which triggers the Research Gate check) is a precondition for entering KILLED
