# /prae-graduate

> **Purpose**: Hand off a GRADUATED research track to a PDAE engineering project
> **Arguments**: `<track_id>`
> **Preconditions**:
>   - Phase 2 → 3 gate has been approved (current_phase = phase_03_conclusion)
>   - The track's state = GRADUATED in track_registry.yaml
>   - PDAE is installed (${PDAE_HOME}/ is accessible)

## Important Notice

Before running, you **must confirm**:
1. The track's TRACK_LOG.md has a complete final-conclusion section
2. A human has explicitly agreed to GRADUATED for this track in the COMMENT of the Phase 2 → 3 PHASE_GATE

## Execution Steps

### 1. Create the engineering project in the PDAE repository

```bash
TRACK_ID="${1:?'Usage: /prae-graduate <track_id>'}"
ls ${PDAE_HOME}/PDAE_QUICKSTART.md \
  || { echo "Error: PDAE repository is not accessible"; exit 1; }

cd ${PDAE_HOME}

# Following the PDAE project-pack, create a PDAE engineering project for the research track
# Use the research code (src/tracks/{track_id}/) as the factual input to scout_m1
# Run the full PDAE M1-M3 flow
```

The specific steps follow PDAE_QUICKSTART.md and are not repeated here. Key inputs:
- The research hypothesis (the `hypothesis` field)
- The validated algorithm logic (the `EXP_NNN.py` implementation, the `contracts` boundary)
- The evidence summary (TRACK_LOG.md Evidence Summary)

Once done, record: `PDAE_PROJECT_PATH=<path after creation>`

### 2. Register the graduation record in the PRAE project

After the PDAE project has been created successfully, return to the PRAE project:

```bash
PDAE_PROJECT_PATH="${PDAE_PROJECT_PATH:?'PDAE project path is not set'}"

python3 tools/graduate_track.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --pdae-project-path "${PDAE_PROJECT_PATH}"
```

### 3. Refresh the project conclusion

```
python3 tools/generate_conclusion.py --project-dir .
```
