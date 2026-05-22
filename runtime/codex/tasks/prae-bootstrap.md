# Task: prae-bootstrap

> Deploy the PRAE framework into the current research project (Codex version)
> Invocation: `prae bootstrap` or `codex exec --task path/to/prae-bootstrap.md`

This is the **project-install entry task**, not the model-context entry.
Once the project install is complete, the model should first build context from the project's `AGENTS.md` / `CLAUDE.md`; project state initialization is done later by `prae init`.

## Steps

### 1. Detect the PRAE repository location

```bash
PRAE_ROOT=""
for p in ${PRAE_HOME} ~/prae ~/PRAE; do
  [ -f "$p/runtime/abstract/PRAE_INIT.template.md" ] && PRAE_ROOT="$p" && break
done
[ -z "$PRAE_ROOT" ] && echo "Error: PRAE repository not found, set the PRAE_ROOT environment variable and retry" && exit 1
echo "PRAE repository: $PRAE_ROOT"
```

### 2. Detect the client type

```bash
if [ -d ".claude" ] || [ -f "CLAUDE.md" ]; then
  CLIENT="claude-code"
elif [ -f "AGENTS.md" ]; then
  CLIENT="codex"
else
  echo "No .claude/ or AGENTS.md detected"
  echo "Create AGENTS.md (for a Codex project) or .claude/ (for a Claude Code project) and retry"
  exit 1
fi
echo "Client type: $CLIENT"
```

### 3. Run the bootstrap script

```bash
python3 "${PRAE_ROOT}/tools/prae_bootstrap.py" \
  --target "$(pwd)" \
  --client "${CLIENT}"
```

### 4. Check for PDAE

```bash
if ls ${PDAE_HOME}/tools/check_contracts.py &>/dev/null; then
  echo "PDAE detected"
else
  echo "Note: PDAE is not installed. Infrastructure-track engineering and contract checks depend on PDAE."
  echo "To install it, see the deployment instructions in the PDAE repository."
fi
```

### 6. Print the summary

```bash
echo ""
echo "PRAE deployment complete"
echo "Created: prae/templates/, prae/PRAE_INIT.md (template)"
echo ""
echo "Next steps:"
echo "  1. Fill in prae/PRAE_INIT.md (problem statement and component classification)"
echo "  2. Run: prae init (generates track_registry.yaml and Phase 0 artifacts)"
```
