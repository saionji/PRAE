# /prae-record-result

> **Purpose**: After an experiment finishes, invoke the formal tool to sync the results into `TRACK_LOG.md`; if there is a state-change recommendation, it is also written into a pending-approval `Decision Log`
> **Arguments**: `<track_id> <exp_id>` (for example: `research_strategy_momentum EXP_003`)
> **Preconditions**: The project has completed `/prae-init`, and the Result and Conclusion of `EXP_NNN.md` have been filled in

## Execution Steps

### 1. Parse arguments and check initialization

```bash
TRACK_ID="${1:?'Usage: /prae-record-result <track_id> <exp_id>'}"
EXP_ID="${2:?'Usage: /prae-record-result <track_id> <exp_id>'}"

[ -f "prae/track_registry.yaml" ] || {
  echo "prae/track_registry.yaml not found. The project may have only completed bootstrap."
  echo "Fill in prae/PRAE_INIT.md first, then run /prae-init."
  exit 1
}
```

### 2. Invoke the formal tool

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
    print(f'State change recommendation: {m.group(1).strip()}')
    print('record_result.py has written this recommendation into the pending-approval Decision Log in TRACK_LOG.md')
    print('If you agree with this recommendation, I will proceed to invoke /prae-update-track-state,')
    print('so the formal tool updates track_registry.yaml and the Decision Log in TRACK_LOG.md.')
else:
    print('No explicit state-change recommendation found; only the result record was completed this time.')
"
```

### 4. Only after the user confirms, invoke the formal state tool

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

python3 tools/update_track_state.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --to-state "${SUGGESTED_STATE}" \
  --approver "<human approver>" \
  --reason "${EXP_ID} result has been approved by a human" \
  --exp-id "${EXP_ID}"
```
