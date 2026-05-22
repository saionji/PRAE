# Task: prae-update-track-state

> Formally update a research track's state after human approval, and sync both `track_registry.yaml` and `TRACK_LOG.md`
> Invocation: `prae update-track-state <track_id> <ACTIVE|KILLED|MERGED|GRADUATED> --approver <name> --reason <reason> [--exp-id EXP_001] [--merged-into <track_id>] [--summary <text>] [--approved-at YYYY-MM-DD]`
> Prerequisites: the project has completed `prae init`, and the user has explicitly approved this state change

## Steps

### 1. Parse arguments

```bash
TRACK_ID="${1:?'Usage: prae update-track-state <track_id> <to_state> --approver <name> --reason <reason>'}"
TO_STATE="${2:?'Usage: prae update-track-state <track_id> <to_state> --approver <name> --reason <reason>'}"
shift 2

APPROVER=""
REASON=""
ADVISOR="AI"
APPROVED_AT=""
EXP_ID=""
MERGED_INTO=""
SUMMARY=""

while [ $# -gt 0 ]; do
  case "$1" in
    --approver)
      APPROVER="${2:-}"
      shift 2
      ;;
    --reason)
      REASON="${2:-}"
      shift 2
      ;;
    --advisor)
      ADVISOR="${2:-AI}"
      shift 2
      ;;
    --approved-at)
      APPROVED_AT="${2:-}"
      shift 2
      ;;
    --exp-id)
      EXP_ID="${2:-}"
      shift 2
      ;;
    --merged-into)
      MERGED_INTO="${2:-}"
      shift 2
      ;;
    --summary)
      SUMMARY="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

[ -n "${APPROVER}" ] || { echo "Error: missing --approver"; exit 1; }
[ -n "${REASON}" ] || { echo "Error: missing --reason"; exit 1; }
```

### 2. Verify the project has been initialized

```bash
[ -f "prae/track_registry.yaml" ] || {
  echo "prae/track_registry.yaml not found. The project may have only completed bootstrap."
  echo "Fill in prae/PRAE_INIT.md first, then run: prae init"
  exit 1
}
```

### 3. Invoke the official tool

```bash
CMD=(
  python3 tools/update_track_state.py
  --project-dir .
  --track-id "${TRACK_ID}"
  --to-state "${TO_STATE}"
  --approver "${APPROVER}"
  --reason "${REASON}"
  --advisor "${ADVISOR}"
)

[ -n "${APPROVED_AT}" ] && CMD+=(--approved-at "${APPROVED_AT}")
[ -n "${EXP_ID}" ] && CMD+=(--exp-id "${EXP_ID}")
[ -n "${MERGED_INTO}" ] && CMD+=(--merged-into "${MERGED_INTO}")
[ -n "${SUMMARY}" ] && CMD+=(--summary "${SUMMARY}")

"${CMD[@]}"
```

### 4. Interpreting the result

On success:
- `track_registry.yaml` updates `state`
- A terminal state automatically fills in `concluded_at`
- `MERGED` automatically fills in `merged_into`
- The current phase's `TRACK_LOG.md` updates `**Current State**` and appends a `Decision Log` entry

On failure, look first at these items in the output:
- `state transition is legal`
- `the infrastructure track depended on is already LOCKED`
- `Research Gate / ...`
- `MERGED target track is legal`
