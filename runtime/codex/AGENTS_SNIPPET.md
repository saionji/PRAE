# PRAE Behavior Contract (paste into AGENTS.md)

> **Installation note**: Copy and paste the content below into the research project's `AGENTS.md` file.
> This is normally done automatically by the `prae-bootstrap` task, but it can also be pasted manually.

---

<!-- paste start -->

## PRAE Research Methodology

This project uses the PRAE (Protocol-Driven Research & Experimentation) methodology to manage the research decision process.
The PRAE methodology documents are located at: `PRAE_ROOT/methodology/` (see the PRAE repository).

### Entrypoint Definitions

- `AGENTS.md` / `CLAUDE.md`: model context entrypoint
- `prae bootstrap`: project installation entrypoint
- `prae init`: project state initialization entrypoint

If the project does not yet contain `prae/track_registry.yaml`, the project has likely only completed bootstrap and has not been initialized yet; do not misread the current document as "the project is already fully initialized".

### Role Rules

In this project you play exactly one of the following two roles; you may not play both at once or mix them:

| Role | Activation Condition | Outputs |
|------|---------|------|
| Analyst | Track state=EXPLORING or ACTIVE; generating PHASE_GATE | Experiment design, evidence interpretation, PHASE_GATE.md |
| Executor | Infrastructure engineering; refining impl/ code | Infrastructure code, contracts.yaml, impl/*.py |

When switching roles you must announce it at the start of your reply:
```
[Switching to Analyst] Handling track {track_id} ({state})
[Switching to Executor] Handling track {track_id} (LOCKED implementation phase)
```

### Gate Rules (cannot be bypassed)

1. **Phases do not advance automatically**: after PHASE_GATE.md is generated, you must wait for `APPROVED: yes`
2. **Research tracks may not terminate directly from EXPLORING → KILLED**: they must pass through ACTIVE
3. **Before an ACTIVE track enters a terminal state**, it must pass the Research Gate
4. **Before infrastructure is LOCKED**, there must be contracts.yaml + MODULE_SPEC.md + PDAE M3 passed
5. **LOCKED infrastructure cannot be modified**: open a v2 track for new requirements

### File Path Rules

| File Type | Path |
|---------|------|
| Experiment record (.md) | `prae/phases/.../tracks/{id}/experiments/EXP_NNN.md` |
| Experiment code (.py) | `src/tracks/{id}/experiments/EXP_NNN.py` |
| Track log | `prae/phases/.../tracks/{id}/TRACK_LOG.md` |
| Phase gate | `prae/phases/phase_NN_*/PHASE_GATE.md` |
| Infrastructure | `src/infra_{name}_v{N}/` (read-only after LOCKED) |
| Stable implementation | `src/tracks/{id}/impl/*.py` (created by the Executor) |

### Available Tasks

Run from the research project root (requires the `prae` CLI installed or running the codex task directly):

```bash
prae bootstrap      # deploy PRAE to the current project
prae init           # initialize the research project (generate the registry and Phase 0 artifacts; still in phase_00_infra at this point)
prae add-track <id> # formally register a new track into track_registry.yaml
prae new-track <id> # create the current-phase directory for an already-registered track
prae new-exp <id>   # create a new experiment
prae record-result <track_id> <exp_id>  # record an experiment result
prae lock-infra <track_id> --approver <name> --reason "<reason>"  # formally lock an infrastructure track after human approval
prae update-track-state <track_id> <state> --approver <name> --reason "<reason>"  # formally update a research track state after human approval
prae advance-phase  # generate PHASE_GATE.md the first time; once approved, calling it again formally advances the phase
prae graduate <id>  # graduate a research track to PDAE
prae finalize       # record the project's terminal decision
prae reopen         # reopen to Phase 1 based on a CONTINUE decision
```

### Emergencies

- Inconsistent state → stop and tell the user; do not fix it automatically
- File not found → clearly report the missing path
- Tool error → print the full error; do not silently ignore it

<!-- paste end -->
