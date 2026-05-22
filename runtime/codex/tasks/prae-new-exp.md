# Task: prae-new-exp

> Create a new experiment for a given track (EXP_NNN.md record + EXP_NNN.py skeleton)
> Invocation: `prae new-exp <track_id> [--title <experiment_title>]` or `prae new-exp <track_id> [experiment_title]`
> Parameters: `$1 = track_id`; the title can be passed as the second positional argument, or as `--title <experiment_title>`
> Precondition: the project has completed `prae init`, and the track has been created via `prae new-track <track_id>`

## Steps

### 1. Parse arguments

```bash
TRACK_ID="${1:?'Usage: prae new-exp <track_id> [--title <experiment_title>]'}"
shift || true
TITLE="experiment"
if [ "${1:-}" = "--title" ]; then
  TITLE="${2:-experiment}"
elif [ -n "${1:-}" ]; then
  TITLE="${1}"
fi
```

### 2. Call the official tool

```bash
python3 tools/new_exp.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --title "${TITLE}"
```
