# Task: prae-init

> Initialize a PRAE research project (read PRAE_INIT.md → generate track_registry.yaml → create Phase 0 artifacts)
> Invocation: `prae init` or `codex exec --task path/to/prae-init.md`
> Prerequisites: `prae bootstrap` has been run, and prae/PRAE_INIT.md is fully filled in

This is the **project-state initialization entry task**.
It is not responsible for installing PRAE into the project; that step is `prae bootstrap`. It is also not the model-context entry; model context should first be built from the project's `AGENTS.md` / `CLAUDE.md`.

## Steps

### 1. Verify PRAE_INIT.md

```bash
[ -f "prae/PRAE_INIT.md" ] || { echo "Error: prae/PRAE_INIT.md does not exist, run prae bootstrap first"; exit 1; }

python3 -c "
with open('prae/PRAE_INIT.md') as f:
    content = f.read()
issues = []
if '{{the core problem the research project tries to solve}}' in content:
    issues.append('Problem Statement not filled in')
if '{{track_id}}' in content or content.count('infra_') == 0:
    issues.append('Infrastructure tracks not filled in')
if issues:
    print('PRAE_INIT.md is incomplete:')
    for i in issues: print(f'  - {i}')
    exit(1)
print('PRAE_INIT.md validation passed')
"
```

### 2. Invoke the initialization tool

```bash
PROJECT_NAME="${1:-$(basename $(pwd))}"

python3 tools/init_project.py \
  --name "${PROJECT_NAME}" \
  --output-dir .
```

If the tool is unavailable, restore it first, then re-run:

```bash
if [ ! -f "tools/init_project.py" ]; then
  echo "tools/init_project.py is missing"
  echo "Re-run prae bootstrap first, or copy tools/init_project.py from the PRAE repository into this project's tools/"
  exit 1
fi

python3 tools/init_project.py \
  --name "${PROJECT_NAME}" \
  --output-dir .
```

### 3. Check the initialization result

```bash
python3 -c "
import yaml, os
r = yaml.safe_load(open('prae/track_registry.yaml'))
assert r['current_phase'] == 'phase_00_infra'
assert 'current_cycle' in r
assert os.path.exists('prae/phases/phase_00_infra/PHASE_BRIEF.md')
for t in r['tracks']:
    if t['type'] == 'infrastructure':
        log_path = f'prae/phases/phase_00_infra/tracks/{t[\"id\"]}/TRACK_LOG.md'
        assert os.path.exists(log_path), log_path
        content = open(log_path, encoding='utf-8').read()
        assert '{{' not in content, f'{t[\"id\"]} TRACK_LOG.md still contains template placeholders'
        print(f'  {t[\"id\"]}: Phase 0 TRACK_LOG.md generated')
"
```

### 4. Print the summary

```bash
echo ""
echo "PRAE project initialization complete"
python3 -c "
import yaml
r = yaml.safe_load(open('prae/track_registry.yaml'))
print(f'  Project: {r[\"project\"]}')
print(f'  Current phase: {r[\"current_phase\"]}')
print(f'  Current cycle: cycle_{r[\"current_cycle\"]}')
print(f'  Track count: {len(r[\"tracks\"])}')
"
echo ""
echo "Next step:"
echo "  Run prae new-track <infra_track_id> to begin infrastructure selection"
```
