# /prae-bootstrap

> **Purpose**: Deploy the PRAE framework files (skills, commands, templates) into a research project
> **When to Use**: the first time you install PRAE in a new research project
> **Arguments**: none (auto-detects the environment)

This is the **project installation entry point**, not the model-context entry point.
When the model builds context inside a project, it should first read `CLAUDE.md` / `AGENTS.md`; project-state initialization is done later by `/prae-init`.

## Execution Steps

### 1. Detect the Client Platform

```bash
# Claude Code: a .claude/ directory or CLAUDE.md exists
# Codex: AGENTS.md exists
# Neither: ask the user

if [ -d ".claude" ] || [ -f "CLAUDE.md" ]; then
  CLIENT="claude-code"
elif [ -f "AGENTS.md" ]; then
  CLIENT="codex"
else
  echo "No Claude Code or Codex environment detected"
  echo "Please choose: (1) Claude Code  (2) Codex"
  # Wait for user input
fi
```

### 2. Invoke the Bootstrap Script

```bash
PRAE_ROOT="${PRAE_HOME}"   # PRAE repository path (configured at install time)
TARGET_DIR="$(pwd)"

python3 "${PRAE_ROOT}/tools/prae_bootstrap.py" \
  --target "${TARGET_DIR}" \
  --client "${CLIENT}"
```

The script will:
- Copy the minimal `project-pack/` skeleton into the target project (e.g. `prae/PRAE_INIT.md`)
- Copy `runtime/${CLIENT}/` into `.claude/` or `AGENTS.md`
- Copy the `runtime/abstract/` templates into `prae/templates/`
- Not create `prae/track_registry.yaml` or Phase 0 artifacts; these are generated later by `/prae-init`

### 3. Check Whether PDAE Is Installed

```bash
ls ${PDAE_HOME}/tools/check_contracts.py 2>/dev/null \
  && echo "PDAE detected" || echo "PDAE not detected"
```

If PDAE is not detected, prompt the user:
```
PRAE requires PDAE when an infrastructure track graduates.
If you would like to install PDAE at the same time, tell me and I will guide you through the deployment.
```

### 4. Post-Install Verification

```bash
# Verify the key files exist
ls .claude/skills/prae-guard.md .claude/skills/prae-analyst.md .claude/skills/prae-executor.md
ls .claude/agents/prae-literature-review.md
ls .claude/commands/prae-init.md
ls prae/templates/
ls prae/PRAE_INIT.md
```

### 5. Output the Installation Summary

```
✓ PRAE has been deployed to {TARGET_DIR}

Installed files:
  .claude/skills/    prae-guard.md  prae-analyst.md  prae-executor.md
  .claude/agents/    prae-literature-review.md  prae-evidence-analyst.md  prae-phase-advisor.md
  .claude/commands/  prae-init.md  prae-add-track.md  prae-new-track.md  prae-new-exp.md  ...
  prae/templates/    8 abstract templates
  prae/PRAE_INIT.md  minimal pre-initialization skeleton

Next steps:
  1. Open prae/PRAE_INIT.md and fill in the problem statement and the track classification table
  2. Run /prae-init to generate track_registry.yaml and the Phase 0 artifacts
```
