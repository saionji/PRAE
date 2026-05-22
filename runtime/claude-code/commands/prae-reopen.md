# /prae-reopen

> **Purpose**: Based on an approved `DECISION: CONTINUE` in `CONCLUSION.md`, reopen the project to `phase_01_research`
> **Arguments**: none
> **Preconditions**: The current phase is `phase_03_conclusion`, and a human has filled in `APPROVED: yes` and `DECISION: CONTINUE` in `CONCLUSION.md`

## Execution Steps

### 1. Verify `CONCLUSION.md`

```bash
python3 tools/check_conclusion.py --project-dir . --check-approved
```

If it does not pass, complete the following first:
- `APPROVED: yes`
- `DECISION: CONTINUE`
- `APPROVER: <your name>`
- `APPROVED_AT: <YYYY-MM-DD>`

### 2. Reopen the project

```bash
python3 tools/reopen_project.py --project-dir .
```

### 3. Interpret the result

After a successful run:
- The `current_phase` in `track_registry.yaml` is switched back to `phase_01_research`
- The `current_cycle` in `track_registry.yaml` is incremented to the next cycle
- The old `phase_01/02/03` directories are archived as a whole to `prae/history/cycle_N/phases/`
- A new `phase_01_research/PHASE_BRIEF.md` is regenerated as the entry point for the next research cycle
