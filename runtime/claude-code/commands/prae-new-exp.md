# /prae-new-exp

> **Purpose**: Create a new experiment for a given track, creating an `EXP_NNN.md` record and an `EXP_NNN.py` code file
> **Arguments**: `<track_id> [--title <experiment_title>]` or `<track_id> [experiment_title]`
> **Preconditions**: The project has completed `/prae-init`, and the track already exists (created via `/prae-new-track`)

## Execution Steps

### 1. Parse arguments

```bash
TRACK_ID="${1:?'Usage: /prae-new-exp <track_id> [--title <experiment_title>]'}"
shift || true
TITLE="experiment"
if [ "${1:-}" = "--title" ]; then
  TITLE="${2:-experiment}"
elif [ -n "${1:-}" ]; then
  TITLE="${1}"
fi
```

### 2. Invoke the formal tool

```bash
python3 tools/new_exp.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --title "${TITLE}"
```
