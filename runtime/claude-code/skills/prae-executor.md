---
name: prae-executor
description: Use when an infrastructure track is ready for engineering (EXPLORING→LOCKED) or when stable impl code needs extracting from experiments — activates Executor SOP and PDAE integration
---

# PRAE Executor SOP (Claude Code)

> Install path: `.claude/skills/prae-executor.md` (deployed automatically by prae-bootstrap)
> Spec reference: `methodology/PRAE_ROLES.md §3`, `runtime/abstract/EXECUTOR_ROLE.prompt.md`

This skill is the in-project Executor behavior entry the model reads — not an install-command entry.
If the project does not yet have `prae/track_registry.yaml`, the project may only have been bootstrapped; run `/prae-init` first, and do not treat this skill as a signal that the project is already fully initialized.

---

## Announce on activation

Write at the start of your reply:
```
[switch to Executor] working on track {track_id} ({reason})
```

---

## Standard flow A: infrastructure track engineering (EXPLORING → LOCKED)

### Preconditions

```bash
# Confirm the project has been initialized
ls prae/track_registry.yaml || {
  echo "track_registry.yaml not found. The project may only have been bootstrapped."
  echo "Complete /prae-init first, then enter the Executor flow."
  exit 1
}

# Confirm the selection is decided (TRACK_LOG.md has a selection conclusion)
grep -A5 "Decision Log" prae/phases/phase_00_infra/tracks/{track_id}/TRACK_LOG.md

# Confirm the PDAE tooling is available
ls ${PDAE_HOME}/tools/check_unit_gate.py
```

If `track_registry.yaml` does not exist, do not hand-create it; let the Analyst complete initialization first, then continue engineering.

### Step 1: Switch to the PDAE environment

```bash
cd ${PDAE_HOME}
source .venv/bin/activate
```

### Step 2: PDAE M1 — write MODULE_SPEC.md

Following the PDAE_QUICKSTART.md M1 flow, create under the PRAE project path:
```
src/infra_{name}_v1/MODULE_SPEC.md
```

After generating context with the PDAE materialize tool, the architect_m1 unit produces the MODULE_SPEC.

### Step 3: PDAE M2 — write contracts.yaml

Following the PDAE CONTRACTS_SPEC.md format, create under the PRAE project path:
```
src/infra_{name}_v1/contracts.yaml
```

Expose only the public interface the research tracks actually need (minimize the exposed surface).

### Step 4: PDAE M3 — implementation + unit gate

```bash
# Back to the PRAE project directory
cd /path/to/project

# Implement the code (src/infra_{name}_v1/)
# ...

# Run the unit gate
python3 ${PDAE_HOME}/tools/check_unit_gate.py \
  --unit reviewer_m3 --repo .

# Run the contracts check
python3 ${PDAE_HOME}/tools/check_contracts.py \
  --contracts src/infra_{name}_v1/contracts.yaml --src src/
```

### Step 5: LOCKED confirmation

After all checks pass:

```bash
python3 tools/lock_infra_track.py \
  --project-dir . \
  --track-id "{track_id}" \
  --approver "<human approver>" \
  --reason "PDAE M3 passed"
```

The formal tool synchronously updates `track_registry.yaml` and TRACK_LOG.md's `## Decision Log`.

---

## Standard flow B: impl/ code extraction

**Trigger**: the same logic is repeated across multiple EXPs, and the Analyst recommends extraction.

```bash
# Create the impl/ directory
mkdir -p src/tracks/{track_id}/impl/

# Extract functions from experiments/, tidy the interface
# Note: the original EXP_NNN.py stays unchanged (experiment scripts are not modified)
```

**If code in impl/ gets imported by a second track → trigger flow C.**

---

## Standard flow C: shared code migration (triggers PDAE M3)

**Trigger**: a module that is needed but not under `src/shared/`, or impl/ code referenced from a second place.

```bash
# 1. Create the shared module directory
mkdir -p src/shared/{module_name}/

# 2. Migrate the code, tidy the public interface
# 3. Write MODULE_SPEC.md (PDAE M3 format)
# 4. Run the PDAE M3 unit gate
python3 ${PDAE_HOME}/tools/check_unit_gate.py \
  --unit reviewer_m3 --repo .
# 5. Update all import paths
```

---

## Hard prohibitions

- Modifying the source of LOCKED infrastructure (requirement change → open v2)
- Writing experiment code (`experiments/`)
- Skipping PDAE M1 or M2 and going straight to M3
- Marking a track as LOCKED when contracts.yaml does not exist
