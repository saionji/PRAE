# /prae-add-track

> **Purpose**: Formally register a new track in `track_registry.yaml`; registration only — does not create the current-phase directory
> **Arguments**: `<track_id> --type <research|infrastructure> [--hypothesis <text>] [--depends-on infra_a infra_b ...] [--description <text>] [--src <path>]`
> **Precondition**: the project has completed `/prae-init`

## Execution Steps

### 1. Parse Arguments

```bash
TRACK_ID="${1:?'Usage: /prae-add-track <track_id> --type <research|infrastructure> [...]'}"
shift

TRACK_TYPE=""
HYPOTHESIS=""
DESCRIPTION=""
SRC=""
DEPENDS_ON=()

while [ $# -gt 0 ]; do
  case "$1" in
    --type)
      TRACK_TYPE="${2:-}"
      shift 2
      ;;
    --hypothesis)
      HYPOTHESIS="${2:-}"
      shift 2
      ;;
    --description)
      DESCRIPTION="${2:-}"
      shift 2
      ;;
    --src)
      SRC="${2:-}"
      shift 2
      ;;
    --depends-on)
      shift
      while [ $# -gt 0 ] && [[ ! "$1" =~ ^-- ]]; do
        DEPENDS_ON+=("$1")
        shift
      done
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

[ -n "${TRACK_TYPE}" ] || { echo "Error: missing --type <research|infrastructure>"; exit 1; }
```

### 2. Verify the Project Is Initialized

```bash
[ -f "prae/track_registry.yaml" ] || {
  echo "prae/track_registry.yaml not found. The project may have only completed bootstrap."
  echo "Fill in prae/PRAE_INIT.md first, then run /prae-init."
  exit 1
}
```

### 3. Invoke the Official Tool

```bash
CMD=(
  python3 tools/add_track.py
  --project-dir .
  --track-id "${TRACK_ID}"
  --type "${TRACK_TYPE}"
)

[ -n "${HYPOTHESIS}" ] && CMD+=(--hypothesis "${HYPOTHESIS}")
[ -n "${DESCRIPTION}" ] && CMD+=(--description "${DESCRIPTION}")
[ -n "${SRC}" ] && CMD+=(--src "${SRC}")
if [ ${#DEPENDS_ON[@]} -gt 0 ]; then
  CMD+=(--depends-on "${DEPENDS_ON[@]}")
fi

"${CMD[@]}"
```

### 4. Follow-Up Actions

After a successful registration:
- Only `track_registry.yaml` is updated
- No `TRACK_LOG.md` or directory is created automatically
- To actually activate the track in the current phase, run `/prae-new-track <track_id>` afterward
