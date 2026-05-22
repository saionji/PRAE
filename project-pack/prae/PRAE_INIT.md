# PRAE Project Initialization Document

<!-- Template source: PRAE/runtime/abstract/PRAE_INIT.template.md -->
<!-- Spec reference: methodology/PRAE_ARTIFACTS.md §2.2 -->
<!-- This file is drafted by the AI Analyst and takes effect after human confirmation; in principle it is filled in only once -->

---

## Problem Statement

> **Research Question** (one sentence): {{the core problem the research project tries to solve}}

**Background**:
{{2-4 sentences explaining why this problem is worth researching and what the limitations of existing solutions are}}

**Success Criteria**:
{{quantifiable success criteria, e.g. "Sharpe ratio ≥ 1.5 on historical data, maximum drawdown ≤ 20%"}}

**Failure Criterion**:
{{the condition that triggers an overall KILL, e.g. "no track reaches the success criteria after Phase 2 ends"}}

---

## Component Classification → Infrastructure Tracks

> **Infrastructure Track** = a foundational capability that multiple research tracks depend on; it must be engineered (through PDAE M1-M3) before research tracks can use it stably.

| Track ID | Description | External Systems Depended On | Notes |
|---------|------|---------------|------|
| `infra_{{name}}_v1` | {{what capability this infrastructure provides}} | {{external data sources, APIs, etc.}} | {{optional notes}} |

<!-- Naming rule: infra_{name}_v{N}, example: infra_data_v1, infra_sim_v1 -->
<!-- If there is no infrastructure track for now, fill in "none", but explain how research tracks obtain data -->

---

## Component Classification → Research Tracks

> **Research Track** = an algorithmic approach or hypothesis aimed at the core research question; it can be KILLED or MERGED when evidence is insufficient.

| Track ID | Hypothesis (one sentence) | Infrastructure Depended On | Initial Priority |
|---------|--------------|---------------|------------|
| `research_{{topic}}_{{variant}}` | {{what this track tries to verify}} | `infra_{{name}}_v1` | High/Medium/Low |

<!-- Naming rule: research_{topic}_{variant}, example: research_strategy_momentum -->
<!-- The hypothesis must be falsifiable: you can clearly state under what conditions this approach is abandoned -->

---

## Phase 0 Success Criteria

> Criterion for Phase 0 to end: all of the following infrastructure tracks have reached the LOCKED state.

| Infrastructure Track ID | LOCKED Criterion | Current State |
|----------------|----------------|---------|
| `infra_{{name}}_v1` | {{under what conditions this infrastructure is considered ready for use}} | EXPLORING |

---

## CHANGE_LOG

<!-- If you find that the component classification needs adjustment along the way, append a record here without deleting the original content -->

| Date | Change | Reason |
|------|---------|------|
| {{YYYY-MM-DD}} | Initialization | Project startup |
