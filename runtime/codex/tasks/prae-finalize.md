# Task: prae-finalize

> Record the project's terminal-state decision based on an approved `CONCLUSION.md`
> Invocation: `prae finalize`
> Precondition: the current phase is `phase_03_conclusion`, and a human has filled in the terminal-state decision in `CONCLUSION.md`

## Steps

### 1. Validate `CONCLUSION.md`

```bash
python3 tools/check_conclusion.py --project-dir . --check-approved
```

If it does not pass, fill in the missing fields first:
- `APPROVED: yes`
- `DECISION: ARCHIVED / GRADUATED_TO_PDAE`
- `APPROVER: <your name>`
- `APPROVED_AT: <YYYY-MM-DD>`

If the human decision is `DECISION: CONTINUE`, do not run this task; use `prae reopen` instead.

### 2. Record the final decision

```bash
python3 tools/finalize_project.py --project-dir .
```

### 3. Result explanation

Depending on the value of `project_decision`, the implications are as follows:
- `ARCHIVED`: the PRAE project is wrapped up; no further PDAE routing
- `GRADUATED_TO_PDAE`: at least one track has graduated to PDAE; engineering work continues in the PDAE repository
