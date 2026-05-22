# /prae-finalize

> **Purpose**: Record the project's final-state decision based on an approved `CONCLUSION.md`
> **Arguments**: none
> **Precondition**: the current phase is `phase_03_conclusion`, and a human has filled in the final-state decision in `CONCLUSION.md`

## Execution Steps

### 1. Verify `CONCLUSION.md`

```bash
python3 tools/check_conclusion.py --project-dir . --check-approved
```

If it does not pass, fill in the missing items first:
- `APPROVED: yes`
- `DECISION: ARCHIVED / GRADUATED_TO_PDAE`
- `APPROVER: <your name>`
- `APPROVED_AT: <YYYY-MM-DD>`

If the human decision is `DECISION: CONTINUE`, do not run this command; use `/prae-reopen` instead.

### 2. Record the Project's Final Decision

```bash
python3 tools/finalize_project.py --project-dir .
```

### 3. Interpret the Result

After a successful run, `track_registry.yaml` will record:
- `project_decision`
- `project_approver`
- `project_decided_at`
- `project_finalized_at`

If the decision is `ARCHIVED`, `archived_at` will also be appended.
