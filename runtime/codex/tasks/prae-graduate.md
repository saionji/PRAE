# Task: prae-graduate

> Hand off a GRADUATED research track to a PDAE engineering project
> Invocation: `prae graduate <track_id>`
> Precondition: Phase 3 has started, track state=GRADUATED, PDAE is installed

## Steps

### 1. Create the engineering project in the PDAE repository

```bash
TRACK_ID="${1:?'Usage: prae graduate <track_id>'}"

ls ${PDAE_HOME}/PDAE_QUICKSTART.md &>/dev/null || {
  echo "Error: PDAE repository is not accessible (${PDAE_HOME})"
  exit 1
}

cd ${PDAE_HOME}
source .venv/bin/activate

# See the "New Project" section of PDAE_QUICKSTART.md
# Use the research code in src/tracks/${TRACK_ID}/ as the factual input for scout_m1
# Run the PDAE M1-M3 flow to obtain the final project path
```

Record the PDAE project path: `PDAE_PROJECT_PATH=<path after creation>`

### 2. Return to the PRAE project and register the graduation record

```bash
PDAE_PROJECT_PATH="${PDAE_PROJECT_PATH:?'Please set the PDAE_PROJECT_PATH environment variable'}"

python3 tools/graduate_track.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --pdae-project-path "${PDAE_PROJECT_PATH}"
```

### 3. Refresh the project conclusion (if needed)

```bash
python3 tools/generate_conclusion.py --project-dir .
```
