# Track Log: {{track_id}}

<!-- Template source: PRAE/runtime/abstract/TRACK_LOG.template.md -->
<!-- Spec reference: methodology/PRAE_ARTIFACTS.md §2.6 -->
<!-- Path rule: prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md (under prae/, not under src/) -->
<!-- Creator: AI Analyst; append an entry for every experiment and every state change, never delete history -->

**Track ID**: `{{track_id}}`
**Type**: infrastructure / research  <!-- delete whichever does not apply -->
**Current Phase**: phase_{{NN}}_{{name}}
**Research Cycle**: cycle_{{N}}
**Created**: {{YYYY-MM-DD}}

---

## Hypothesis (research tracks only)

{{One-sentence falsifiable hypothesis, kept consistent with the hypothesis field in track_registry.yaml}}

**Failure Criterion** (under what conditions to KILL this track):
{{An explicit, quantifiable termination condition}}

---

## Selection Goal (infrastructure tracks only)

{{What capability this infrastructure track must provide, and what counts as a successful selection}}

---

## State

**Current State**: EXPLORING  <!-- update as the state changes -->
**Depends On**:
- `{{depends_on_track_id}}` (if there is no dependency, write "none")

---

## Experiments

| EXP ID | Date | Purpose | Conclusion | Link |
|--------|------|---------|------------|------|
| EXP_001 | {{YYYY-MM-DD}} | {{what this experiment aims to answer}} | confirms / refutes / partially confirms | [EXP_001.md](experiments/EXP_001.md) |

---

## Evidence Summary

> Append a paragraph after each experiment, in the format: date + key finding + impact on the hypothesis. Never delete history.

- **{{YYYY-MM-DD}} EXP_001**: {{key value or conclusion, 1-2 sentences}}. {{Impact on the hypothesis: positive / negative / neutral signal}}.

---

## Decision Log

> Record state changes: when it changed, who recommended it, who approved it. Format: date + old state → new state + reason.

| Date | Change | Recommended by | Approved by | Reason |
|------|--------|----------------|-------------|--------|
| {{YYYY-MM-DD}} | Created (EXPLORING) | AI | — | Project started |
| {{YYYY-MM-DD}} | EXPLORING → ACTIVE | AI | {{approver}} | {{EXP_XXX shows a positive signal}} |
