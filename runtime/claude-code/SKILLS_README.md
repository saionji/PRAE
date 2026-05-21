# PRAE Skills for Claude Code

This directory ships three Claude Code skills that make PRAE projects work well with Claude Code's slash commands and agent flows.

| Skill | When to use | What it enforces |
|---|---|---|
| **`prae-guard`** | At the start of any session inside a PRAE-managed project | Behavioral contracts: don't bypass gates, don't hand-edit `track_registry.yaml`, don't lock infra without contracts/spec |
| **`prae-analyst`** | When a research track is in `EXPLORING` or `ACTIVE` state | Analyst SOP: experiment design, evidence interpretation, phase-gate generation |
| **`prae-executor`** | When an infrastructure track is approaching `LOCKED`, or stable impl needs extraction | Executor SOP + PDAE integration |

## Two ways to install

### Option A: full PRAE bootstrap (recommended for new projects)

This deploys the skills along with the full PRAE tool layout. From your project root:

```bash
# Requires PRAE_HOME pointing to a clone of this repo.
python3 ${PRAE_HOME}/tools/prae_bootstrap.py --target . --client claude-code
```

The bootstrap creates `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, deploys the 27 CLI tools to `tools/`, and writes a `prae/PRAE_INIT.md` template you fill in next.

### Option B: skills only (if you don't need the rest of PRAE)

If you only want the methodology guardrails in your Claude Code session — for instance, your project doesn't actually run experiments, you just like the role discipline — copy the three skill files directly:

```bash
mkdir -p .claude/skills
cp ${PRAE_HOME}/runtime/claude-code/skills/prae-guard.md     .claude/skills/
cp ${PRAE_HOME}/runtime/claude-code/skills/prae-analyst.md   .claude/skills/
cp ${PRAE_HOME}/runtime/claude-code/skills/prae-executor.md  .claude/skills/
```

Without the rest of the PRAE infrastructure (`prae/`, `tools/`, `runtime/abstract/`), the skills will still load — but the analyst skill, in particular, expects to be able to read `prae/track_registry.yaml` and `prae/PRAE_INIT.md`. If those are missing, the skills know to suggest running `/prae-bootstrap` rather than pretending the project is initialized.

## Verifying installation

After either install path:

```bash
# Listing should show the three .md files
ls .claude/skills/

# Claude Code recognizes them via the frontmatter `name:` field
head -3 .claude/skills/prae-guard.md
```

Inside Claude Code, the skills are auto-discovered by the runtime; no further command is needed.

## Slash commands shipped alongside

`prae-bootstrap` deploys these via `.claude/commands/`. They're separate from the skills:

```
/prae-bootstrap         /prae-add-track       /prae-init
/prae-new-track         /prae-new-exp         /prae-record-result
/prae-lock-infra        /prae-update-track-state
/prae-advance-phase     /prae-graduate        /prae-finalize
/prae-reopen
```

If you used Option B (skills only) and want commands too:

```bash
mkdir -p .claude/commands
cp ${PRAE_HOME}/runtime/claude-code/commands/*.md .claude/commands/
```

## Codex CLI users

For Codex CLI the equivalent layout lives in `runtime/codex/` — `prompts/` for role prompts, `tasks/` for slash-command-equivalents, `bin/prae` as a wrapper CLI. See `runtime/codex/bin/README.md`.

## Source-of-truth

The role contracts the skills enforce are spelled out in `methodology/PRAE_ROLES.md` and `methodology/PRAE_CORE_MODEL.md`. The skills are intentionally thin pointers to those documents — if you want to understand *why* a skill says what it says, read the methodology first.
