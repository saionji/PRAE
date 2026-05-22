# Task: prae-advance-phase

> Check the phase gate conditions; on the first call generate PHASE_GATE.md, and once approved advance the phase directly
> Invocation: `prae advance-phase`
> Important: if the current phase already has a PHASE_GATE.md with `APPROVED: yes`, do not regenerate the gate — just verify and advance
> Prerequisites: the project has completed `prae init`

## Steps

### 1. Read the current phase information

```bash
[ -f "prae/track_registry.yaml" ] || {
  echo "prae/track_registry.yaml not found. The project may have only completed bootstrap."
  echo "Fill in prae/PRAE_INIT.md first, then run: prae init"
  exit 1
}

python3 -c "
import yaml
r = yaml.safe_load(open('prae/track_registry.yaml'))
override = r.get('current_phase_override')
if override:
    print(f'Detected current_phase_override={override}; normal phase advancement is paused, resolve the exception and remove the override first')
    exit(1)
phase_map = {
    'phase_00_infra': 'phase_01_research',
    'phase_01_research': 'phase_02_validation',
    'phase_02_validation': 'phase_03_conclusion',
}
curr = r['current_phase']
tgt = phase_map.get(curr)
if not tgt:
    print(f'Already at the final phase {curr}, no advancement needed')
    exit(0)
print(f'current={curr}')
print(f'target={tgt}')
for t in r['tracks']:
    print(f'  {t[\"id\"]} [{t[\"type\"]}] state={t[\"state\"]}')
"
```

### 2. If the current phase already has a PHASE_GATE.md with APPROVED: yes, advance directly

```bash
python3 tools/check_phase_gate.py --project-dir . --check-approved && \
python3 tools/advance_phase.py --project-dir .
```

If both the check and the advancement above pass, stop here; do not regenerate `PHASE_GATE.md`.

If `--check-approved` fails, the current gate is not yet approved or not yet generated — continue with the generation flow below.

### 3. Generate the PHASE_GATE.md draft

```bash
python3 tools/generate_phase_gate.py --project-dir .
```

Read these items from the output:
- `path`
- `recommendation`
- `failed_conditions`

Then open the generated `PHASE_GATE.md` and confirm that the checkbox states in Section 2 match the tool output.

### 4. Verify the generated result

```bash
python3 tools/check_phase_gate.py --project-dir .
```

### 5. Wait for human approval (you must stop here)

```
PHASE_GATE.md has been generated, with its contents populated according to the current actual gate results.

In the file at the path shown in the output, fill in Section 6:
  APPROVED: yes     ← agree to advance
  APPROVED: no      ← rejected, needs improvement
  APPROVER: your name
  APPROVED_AT: today's date

Once filled in, call again:
  prae advance-phase
or run directly:
  python3 tools/check_phase_gate.py --project-dir . --check-approved
  python3 tools/advance_phase.py --project-dir .

When `prae advance-phase` is called again, it should first check for an approved gate and advance directly; do not regenerate `PHASE_GATE.md`.
```

**Note: stop here, do not automatically update current_phase.**

### 6. Follow-up actions after approval (execute once a human confirms APPROVED: yes)

```bash
python3 tools/advance_phase.py --project-dir .
```
