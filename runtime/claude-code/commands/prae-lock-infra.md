# /prae-lock-infra

> **Purpose**: After human approval, formally update an infrastructure track from `EXPLORING` to `LOCKED`
> **Arguments**: `<track_id> --approver <name> --reason <reason> [--contracts <path>] [--module-spec <path>] [--approved-at YYYY-MM-DD]`
> **Preconditions**: The project has completed `/prae-init`, is currently in `phase_00_infra`, and the corresponding infrastructure track has completed the PDAE M3 / Contracts Gate

## Execution Steps

### 1. Parse arguments

```bash
TRACK_ID="${1:?'Usage: /prae-lock-infra <track_id> --approver <name> --reason <reason>'}"
shift

APPROVER=""
REASON=""
ADVISOR="AI"
LOCKED_AT=""
CONTRACTS=""
MODULE_SPEC=""

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
    --approved-at|--locked-at)
      LOCKED_AT="${2:-}"
      shift 2
      ;;
    --contracts)
      CONTRACTS="${2:-}"
      shift 2
      ;;
    --module-spec)
      MODULE_SPEC="${2:-}"
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

### 2. Verify the project is initialized

```bash
[ -f "prae/track_registry.yaml" ] || {
  echo "prae/track_registry.yaml not found. The project may have only completed bootstrap."
  echo "Fill in prae/PRAE_INIT.md first, then run /prae-init."
  exit 1
}
```

### 3. Invoke the formal tool

```bash
CMD=(
  python3 tools/lock_infra_track.py
  --project-dir .
  --track-id "${TRACK_ID}"
  --approver "${APPROVER}"
  --reason "${REASON}"
  --advisor "${ADVISOR}"
)

[ -n "${LOCKED_AT}" ] && CMD+=(--locked-at "${LOCKED_AT}")
[ -n "${CONTRACTS}" ] && CMD+=(--contracts "${CONTRACTS}")
[ -n "${MODULE_SPEC}" ] && CMD+=(--module-spec "${MODULE_SPEC}")

"${CMD[@]}"
```

### 4. What success means

On success, the following are all completed:
- The infrastructure track's `state=LOCKED` is updated in `track_registry.yaml`
- `locked_at` is written automatically
- The `contracts` / `module_spec` paths are registered automatically
- A `Decision Log` entry is appended to the current phase's `TRACK_LOG.md`

If the output fails, check these first:
- `The current phase allows locking infrastructure tracks`
- `The infrastructure-track state transition is legal`
- `The contracts file exists`
- `The MODULE_SPEC file exists`
- `The Contracts Gate passes`
