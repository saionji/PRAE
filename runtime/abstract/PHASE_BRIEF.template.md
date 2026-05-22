# Phase {{NN}}_{{name}} Brief

<!-- Template source: PRAE/runtime/abstract/PHASE_BRIEF.template.md -->
<!-- Spec reference: methodology/PRAE_ARTIFACTS.md §2.4 -->
<!-- Creator: AI Analyst, created immediately after the previous phase's PHASE_GATE is approved -->

**Phase**: phase_{{NN}}_{{name}}
**Research Cycle**: cycle_{{N}}
**Created**: {{YYYY-MM-DD}}
**Creator**: AI (Analyst role)

---

## Phase Goal

{{1-3 sentences describing what this phase must achieve, e.g. "complete the selection and engineering of all infrastructure tracks, building the foundation for the research period"}}

---

## Success Criteria

> When all of the following conditions are met, the AI may generate PHASE_GATE.md to request human approval to enter the next phase.

- [ ] {{Success condition 1, quantifiable or explicitly checkable}}
- [ ] {{Success condition 2}}
- [ ] {{Success condition N}}

---

## Tracks Present in This Phase

| Track ID | Type | Initial State | Target State for Phase | Notes |
|----------|------|----------------|------------------------|-------|
| `{{track_id}}` | infrastructure / research | EXPLORING | LOCKED / ACTIVE | {{optional}} |

---

## Key Time Milestones (Optional)

| Milestone | Target Date | Description |
|-----------|-------------|-------------|
| {{milestone name}} | {{YYYY-MM-DD}} | {{optional description}} |

---

## Related Files

- `prae/track_registry.yaml` — the master table of track states
- `prae/phases/phase_{{NN}}_{{name}}/PHASE_GATE.md` — generated when this phase ends (not yet created)
- `prae/PRAE_INIT.md` — the project initialization document (problem statement and component classification)
