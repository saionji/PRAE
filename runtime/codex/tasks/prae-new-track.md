# Task: prae-new-track

> Create the current-phase directory and an initial `TRACK_LOG.md` for a track already registered in `track_registry.yaml`
> Invocation: `prae new-track <track_id>`
> Parameters: `$1 = track_id`

## Steps

### 1. Parse arguments

```bash
TRACK_ID="${1:?'Usage: prae new-track <track_id>'}"
```

### 2. Call the official tool

```bash
python3 tools/new_track.py \
  --project-dir . \
  --track-id "${TRACK_ID}"
```
