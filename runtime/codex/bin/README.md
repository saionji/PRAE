# bin/prae — CLI Installation Notes

`prae` is the unified CLI entrypoint for the PRAE methodology (Codex version).
It triggers the corresponding Codex task via `prae <subcommand>`.

There are also three distinct "entrypoints" here:
- `LLM_ENTRYPOINT.md` / the in-project `AGENTS.md`: model context entrypoint
- `prae bootstrap`: project installation entrypoint
- `prae init`: project state initialization entrypoint

## Prerequisites

- The Codex CLI is installed and available (the `codex` command)
- The PRAE repository has been cloned locally

## Installation

### Method 1: Symlink into PATH (recommended)

```bash
# assuming the PRAE repository is at ${PRAE_HOME}
chmod +x ${PRAE_HOME}/runtime/codex/bin/prae
ln -sf ${PRAE_HOME}/runtime/codex/bin/prae ~/.local/bin/prae

# confirm that ~/.local/bin is in PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# verify
prae help
```

### Method 2: Run directly (no installation)

```bash
# in the research project directory
bash ${PRAE_HOME}/runtime/codex/bin/prae <subcommand>
```

### Method 3: alias (quick temporary option)

```bash
alias prae='${PRAE_HOME}/runtime/codex/bin/prae'
```

## Available Commands

```
prae bootstrap                     first use: deploy PRAE to the current project
prae init                          initialize the research project (generate the registry and Phase 0 artifacts from PRAE_INIT.md)
prae add-track <track_id>          formally register a new track into track_registry.yaml
prae new-track <track_id>          create the current-phase directory for an already-registered track
prae new-exp <track_id>            create a new experiment
prae record-result <id> <exp_id>   record an experiment result
prae lock-infra <id>               formally lock an infrastructure track to LOCKED after human approval
prae update-track-state <id> <state>  formally update a research track state after human approval
prae advance-phase                 generate the phase gate analysis the first time; once approved, formally advance the phase
prae graduate <track_id>           graduate a research track to PDAE
prae finalize                      record the project's terminal decision
prae reopen                        reopen to Phase 1 based on a CONTINUE decision
```

## How It Works

Each command maps to `runtime/codex/tasks/prae-{subcommand}.md`,
executed via `codex exec --task`. Codex reads the task file and performs the corresponding operation.

Startup sequence:
1. `prae bootstrap`: deploy the minimal skeleton, templates, tools, and Codex tasks
2. Fill in `prae/PRAE_INIT.md`
3. `prae init`: generate `prae/track_registry.yaml`, `prae/phases/phase_00_infra/PHASE_BRIEF.md`, and the infrastructure `TRACK_LOG.md`
4. Phase 0: run selection experiments for the infrastructure tracks; once PDAE M3 passes, use `prae lock-infra`
5. After all infrastructure tracks are `LOCKED`, run `prae advance-phase` to generate the gate; after human approval, run the same command again to enter Phase 1
6. Phase 1: for registered research tracks, run `prae new-track` and `prae new-exp`; for a brand-new hypothesis, run `prae add-track` first

## Updates

After the PRAE repository is updated, the CLI automatically uses the new task files; no reinstallation is needed.
