# /prae-new-track

> **Purpose**: Create the directory and an initial `TRACK_LOG.md` for a track already registered in the current phase
> **Arguments**: `<track_id>`

## Execution Steps

### 1. Parse arguments

```bash
TRACK_ID="${1:?'Usage: /prae-new-track <track_id>'}"
```

### 2. Invoke the formal tool

```bash
python3 tools/new_track.py \
  --project-dir . \
  --track-id "${TRACK_ID}"
```
