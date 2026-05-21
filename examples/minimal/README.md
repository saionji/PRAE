# Minimal Example

The smallest possible PRAE project, used as a learning reference and exercised by the integration test suite.

## Where the live example lives

The canonical minimal project layout is at:

```
tests/fixtures/fake_project/
```

It is intentionally bare-bones (1 infrastructure track + 1 research track) and is verified by every CI run, so it stays in sync with the live tooling. Treat that fixture as the authoritative shape of a PRAE-managed project.

## Bootstrap a real project from scratch

```bash
# 1. Make a new project directory
mkdir my-research && cd my-research
touch .claude   # marker file so the bootstrap detects this as a Claude Code project
                # (use `touch .codex` for a Codex-driven project instead)

# 2. Bootstrap PRAE into it
python3 ${PRAE_HOME}/tools/prae_bootstrap.py --target . --client claude-code

# 3. Edit prae/PRAE_INIT.md with your research question and track plan

# 4. Generate the registry + Phase 0 artifacts
python3 ${PRAE_HOME}/tools/init_project.py --name my-research --output-dir .

# 5. From here on, all state changes go through tools/ — see the main README quick-start
```

For the full step-by-step walkthrough, see the main repository [README](../../README.md).

## Inspecting the fixture

```bash
# What does the fixture look like?
ls tests/fixtures/fake_project/
cat tests/fixtures/fake_project/prae/PRAE_INIT.md
cat tests/fixtures/fake_project/prae/track_registry.yaml
```

The fixture covers a single project (`infra_data_v1` + `research_strategy_momentum`) and shows the exact files PRAE generates and tracks.
