# Claude Start Prompt

Send the entire block below directly to a Claude session:

```text
This is a PRAE environment. First read LLM_ENTRYPOINT.md in the repository root, and build your context strictly following the file reading order it specifies.
Standard entry-point definitions:
- `LLM_ENTRYPOINT.md`: model context entry point
- `/prae-bootstrap`: project installation entry point
- `/prae-init`: project state initialization entry point

First determine whether you are currently in:
1. The PRAE framework repository itself
2. A research project that uses PRAE

If you are in the PRAE framework repository:
- First read README.md
- Then read methodology/PRAE_QUICKSTART.md, methodology/PRAE_CORE_MODEL.md, methodology/PRAE_ROLES.md
- Then read only the tools/, runtime/, tests/ that are directly relevant to your current task

If you are in a research project that uses PRAE:
- First read CLAUDE.md or AGENTS.md
- Then read prae/PRAE_INIT.md, prae/track_registry.yaml, the current phase's PHASE_BRIEF.md, the target track's TRACK_LOG.md, and the most recent EXP_NNN.md
- If prae/track_registry.yaml does not exist, the project has likely only completed bootstrap and has not been initialized yet; first prompt me to run /prae-init, and do not assume the project is already initialized
- If current_phase=phase_00_infra, the project is still in the infrastructure lock period; first complete Phase 0, and do not directly create research-track experiments

Strictly follow these rules:
- Do not skip any gate
- Do not manually modify a research track's state
- Do not manually set an infrastructure track to LOCKED; you must use tools/lock_infra_track.py or /prae-lock-infra
- Research-track state changes must go through tools/update_track_state.py or /prae-update-track-state
- A research track cannot terminate directly from EXPLORING to KILLED
- An ACTIVE track must pass the Research Gate before entering a terminal state
- LOCKED infrastructure cannot be modified directly; open a v2 for new requirements
- Experiment coding follows the lightweight PDAE sequence: design first, define the Preflight Check first, then implement, then verify

After building your context, first produce 3 sections of output:
1. Which scenario you judge the current situation to be
2. Which key files you have already read
3. The most reasonable next action right now

If I ask you to execute directly, prefer the formal entry points already present in the project:
- Claude slash commands: /prae-bootstrap /prae-init /prae-add-track /prae-new-track /prae-new-exp /prae-record-result /prae-lock-infra /prae-update-track-state /prae-advance-phase /prae-graduate /prae-finalize /prae-reopen
- Formal tools: python3 tools/*.py

Unless I explicitly request it, do not skip the methodology documents and modify code directly.
```
