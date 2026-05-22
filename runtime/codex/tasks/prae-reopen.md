# Task: prae-reopen

> Reopen the project to `phase_01_research` based on an approved `DECISION: CONTINUE` in `CONCLUSION.md`
> Invocation: `prae reopen`
> Precondition: the current phase is `phase_03_conclusion`, and a human has written `APPROVED: yes` and `DECISION: CONTINUE` in `CONCLUSION.md`

## Steps

### 1. Validate `CONCLUSION.md`

```bash
python3 tools/check_conclusion.py --project-dir . --check-approved
```

If it does not pass, fill in the missing fields first:
- `APPROVED: yes`
- `DECISION: CONTINUE`
- `APPROVER: <your name>`
- `APPROVED_AT: <YYYY-MM-DD>`

### 2. Reopen the project

```bash
python3 tools/reopen_project.py --project-dir .
```

### 3. Result explanation

After a successful run:
- `current_phase` in `track_registry.yaml` switches back to `phase_01_research`
- `current_cycle` in `track_registry.yaml` is incremented to the next cycle
- The old `phase_01/02/03` directories are archived as a whole into `prae/history/cycle_N/phases/`
- A new `prae/phases/phase_01_research/PHASE_BRIEF.md` is generated as the entry point for the next research cycle
