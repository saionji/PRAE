# /prae-advance-phase

> **Purpose**: Check the current phase's gate conditions; the first invocation generates PHASE_GATE.md, and once approved it advances directly
> **Arguments**: none (reads track_registry.yaml to determine the target phase automatically)
> **Precondition**: the project has completed /prae-init, and you believe the current phase's goal has been met, or the user asks to check whether advancing is possible

## Important Note

If the current phase already has a `PHASE_GATE.md` with `APPROVED: yes`, this command should verify and advance directly — do not regenerate the gate.
Only enter the "generate and wait for approval" path when the current gate has not yet been generated or not yet approved.

## Execution Steps

### 1. Read the Current State

```bash
[ -f "prae/track_registry.yaml" ] || {
  echo "prae/track_registry.yaml not found. The project may have only completed bootstrap."
  echo "Fill in prae/PRAE_INIT.md first, then run /prae-init."
  exit 1
}

python3 -c "
import yaml
r = yaml.safe_load(open('prae/track_registry.yaml'))
override = r.get('current_phase_override')
if override:
    print(f'Detected current_phase_override={override}; regular phase advancement is suspended. Handle the exception first and remove the override.')
    exit(1)
current = r['current_phase']
phase_map = {
    'phase_00_infra': 'phase_01_research',
    'phase_01_research': 'phase_02_validation',
    'phase_02_validation': 'phase_03_conclusion',
}
target = phase_map.get(current, None)
if target is None:
    print(f'Already at the final phase: {current}; nothing to advance.')
    exit(0)
print(f'current={current}')
print(f'target={target}')
"
```

### 2. If the Current Phase Already Has a PHASE_GATE.md with APPROVED: yes, Advance Directly

```bash
python3 tools/check_phase_gate.py --project-dir . --check-approved && \
python3 tools/advance_phase.py --project-dir .
```

If the commands above succeed, stop here; do not regenerate `PHASE_GATE.md`.
If `--check-approved` fails, the gate has not yet been approved or generated — continue with the generation flow below.

### 3. Generate the PHASE_GATE.md Draft

```bash
python3 tools/generate_phase_gate.py --project-dir .
```

### 4. Present the Check Results

Read the tool's JSON output and present it to the user:

```
Phase gate analysis complete

Current Phase: {current_phase}
Target Phase: {target_phase}

Gate Conditions:
  [x] Condition 1 (met)
  [ ] Condition 2 (not met)

Recommended Action: advance / do not advance yet
Rationale: ...

PHASE_GATE.md has been created: {path}

---
In section 6 of PHASE_GATE.md, please fill in:
  APPROVED: yes  (advance)  or  APPROVED: no  (reject)
  APPROVER: {your name}
  APPROVED_AT: {date}
  COMMENT: {optional note}

Once filled in, tell me "approved" and I will execute the follow-up actions.
```

Then run once:

```bash
python3 tools/check_phase_gate.py --project-dir .
```

Confirm that the generated document is consistent with the current gate state.

### 5. Wait for the Approval Signal

After the user fills in `APPROVED: yes` in PHASE_GATE.md and notifies you, invoke again:

```bash
/prae-advance-phase
```

Or run directly:

```bash
python3 tools/check_phase_gate.py --project-dir . --check-approved
```

When `/prae-advance-phase` is invoked again, it should check the approved gate first and advance directly; do not regenerate `PHASE_GATE.md`.

### 6. Follow-Up Actions After Approval

Once `APPROVED: yes` is detected, execute per the corresponding section of `methodology/PRAE_PHASE_GATES.md`:

```bash
python3 tools/advance_phase.py --project-dir .
```
