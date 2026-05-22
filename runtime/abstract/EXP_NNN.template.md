# EXP_{{NNN}}: {{experiment_title}}

<!-- Template source: PRAE/runtime/abstract/EXP_NNN.template.md -->
<!-- Spec reference: methodology/PRAE_ARTIFACTS.md §2.7 -->
<!-- Path rule: prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md -->
<!-- Corresponding code: src/tracks/{track_id}/experiments/EXP_NNN.py -->
<!-- Creator: AI Analyst; fill in Result and Conclusion after the experiment runs, then do not modify them further -->

**Experiment ID**: EXP_{{NNN}}
**Track ID**: `{{track_id}}`
**Date**: {{YYYY-MM-DD}}
**State**: In Progress / Completed  <!-- delete whichever does not apply -->

---

## Goal

{{One-sentence goal: the core question this experiment answers}}

---

## Method

- **Data Source**: `{{infra_track_id}}.{{api_function}}` (the public interface declared by the contract)
- **Target / Dataset**: {{Concrete dataset description, e.g. "CSI 300 constituents, list as of 2024-01-01"}}
- **Time Window**: {{YYYY-MM-DD}} to {{YYYY-MM-DD}}
- **Random Seed**: `seed={{N}}` (or "no randomness")
- **Key Hyperparameters**:
  - `{{param_name}}`: {{value}}
  - `{{param_name}}`: {{value}}
- **Control Group**: {{Control group setup, or "no control group"}}
- **Code Path**: `src/tracks/{{track_id}}/experiments/EXP_{{NNN}}.py`

---

## Preflight Check

> This is the experiment-variant "lightweight PDAE" step: write the minimal runnable check and the output contract clearly first, then start implementing.

**Minimal Smoke Check**: {{e.g. "the script must finish within 30s and print Sharpe, max drawdown, and sample count"}}

**Output Contract**: {{e.g. "stdout contains at least sharpe/max_drawdown; also writes results/EXP_{{NNN}}.json"}}

**Out of Scope This Time**: {{e.g. "do not abstract into impl/, do not optimize performance, do not handle multi-market generalization"}}

---

## Expected Signal

**Success Criterion** (confirms the hypothesis): {{e.g. "backtest Sharpe ≥ 1.0 and max drawdown ≤ 25%"}}

**Failure Criterion** (refutes the hypothesis): {{e.g. "Sharpe < 0 or max drawdown > 40%"}}

**Neutral Signal**: {{e.g. "Sharpe 0-1, keep optimizing"}}

---

## Result

> Fill this in after the experiment runs, then do not modify it further.

**Key Values**:
- {{metric name}}: {{value}}
- {{metric name}}: {{value}}

**Output Location**: `{{path to chart or data file, if any}}`

**Raw Output** (paste the key stdout / stderr):
```
{{paste the experiment's key output}}
```

---

## Conclusion

**Conclusion**: confirms / refutes / partially confirms the hypothesis

**Rationale**: {{1-3 sentences explaining why you reached the above conclusion}}

**Recommended Impact on Track State**:
- Recommended state change: {{EXPLORING → ACTIVE / keep EXPLORING / ACTIVE → KILLED / etc.}} (or "no change")
- Next-step recommendation: {{direction for the next experiment, or terminate the track}}
