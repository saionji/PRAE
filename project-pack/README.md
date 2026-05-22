# project-pack — PRAE Deployment Bundle

This directory contains the file skeleton needed to deploy the PRAE framework into a concrete research project.

## Entry Points

- `CLAUDE.md` / `AGENTS.md`: model context entry point
- `prae bootstrap`: project installation entry point
- `prae init`: project state initialization entry point

## Automatic Deployment (Recommended)

Run automatically by `prae_bootstrap.py`:

```bash
python3 /path/to/PRAE/tools/prae_bootstrap.py \
  --target /path/to/your/research/project \
  --client claude-code   # or codex
```

## Manual Deployment

1. Copy the `prae/` directory to the root of your research project
2. Copy `tools/` to the research project's `tools/` (optional — you can also use the tools in the PRAE root directory)
3. Initialize `CLAUDE.md` (Claude Code) or `AGENTS.md` (Codex) with the contents of `AI_CONTEXT.template.md`
4. Fill in the research question and component classification following `prae/PRAE_INIT.md`
5. Run `prae init` (or `python3 tools/init_project.py ...`) to generate `track_registry.yaml` and the Phase 0 artifacts

## Directory Structure

```
project-pack/
├── README.md               ← this file
├── AI_CONTEXT.template.md  ← CLAUDE.md / AGENTS.md skeleton
├── prae/
│   ├── PRAE_INIT.md        ← problem statement and component classification template
└── tools/                  ← gate script mirror (synced from the root tools/)
```
