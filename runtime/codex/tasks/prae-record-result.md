# Task: prae-record-result

> After an experiment is complete, invoke the official tool to sync the result into TRACK_LOG.md; if there is a state-change recommendation, it is also written into the pending-approval `Decision Log`
> Invocation: `prae record-result <track_id> <exp_id>`
> Arguments: `$1 = track_id`, `$2 = exp_id` (e.g. `EXP_003`)
> Prerequisites: the project has completed `prae init`, and the Result / Conclusion of `EXP_NNN.md` are filled in

## Steps

### 1. Parse arguments and check initialization

```bash
TRACK_ID="${1:?'Usage: prae record-result <track_id> <exp_id>'}"
EXP_ID="${2:?'Usage: prae record-result <track_id> <exp_id>'}"

[ -f "prae/track_registry.yaml" ] || {
  echo "prae/track_registry.yaml not found. The project may have only completed bootstrap."
  echo "Fill in prae/PRAE_INIT.md first, then run: prae init"
  exit 1
}
```

### 2. Invoke the official tool

```bash
python3 tools/record_result.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --exp-id "${EXP_ID}"
```

### 3. Read the state recommendation

```bash
PHASE=$(python3 -c "import yaml; r=yaml.safe_load(open('prae/track_registry.yaml')); print(r['current_phase'])")
EXP_MD="prae/phases/${PHASE}/tracks/${TRACK_ID}/experiments/${EXP_ID}.md"

python3 -c "
import re
with open('${EXP_MD}', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'Recommended state change[:：]\\s*(.+)', content)
if m:
    print(f'State-change recommendation: {m.group(1).strip()}')
    print('record_result.py has written this recommendation into the pending-approval Decision Log in TRACK_LOG.md')
    print('If the user explicitly agrees, continue with prae update-track-state ... to complete the formal state change')
else:
    print('No explicit state-change recommendation found; only the result was recorded this time.')
"
```

### 4. Only after the user explicitly approves, perform the formal state change

If the Conclusion of `EXP_NNN.md` gives a state recommendation, and the user has approved this change, run:

```bash
SUGGESTED_STATE=$(python3 -c "
import re
with open('${EXP_MD}', encoding='utf-8') as f:
    c = f.read()
m = re.search(r'Recommended state change[:：]\\s*(.+)', c)
text = m.group(1).strip() if m else ''
if '→' in text:
    print(text.split('→')[-1].strip())
elif '->' in text:
    print(text.split('->')[-1].strip())
")

[ -n "${SUGGESTED_STATE}" ] || exit 0

CMD=(
  python3 tools/update_track_state.py
  --project-dir .
  --track-id "${TRACK_ID}"
  --to-state "${SUGGESTED_STATE}"
  --approver "<human approver>"
  --reason "${EXP_ID} result approved by a human"
  --exp-id "${EXP_ID}"
)

# If the recommendation is MERGED, also append:
# CMD+=(--merged-into "<target track ID>")

"${CMD[@]}"
```
