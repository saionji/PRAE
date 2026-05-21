#!/usr/bin/env bash
# Bootstrap PRAE development environment.
# Works without a pre-existing venv or system pip.
set -e

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv"

# Prefer virtualenv.pyz if pip/venv broken (common on stripped systems)
if [ ! -d "$VENV_DIR" ]; then
    if "$PYTHON" -m venv --help >/dev/null 2>&1; then
        "$PYTHON" -m venv "$VENV_DIR"
    elif [ -f "$HOME/.local/bin/virtualenv.pyz" ]; then
        "$PYTHON" "$HOME/.local/bin/virtualenv.pyz" "$VENV_DIR"
    else
        echo "ERROR: no venv or virtualenv.pyz found. Install virtualenv first." >&2
        exit 1
    fi
fi

"$VENV_DIR/bin/pip" install --quiet pyyaml pytest pytest-cov

echo ""
echo "PRAE environment ready."
echo "Activate with: source $VENV_DIR/bin/activate"
echo "Run tests with: $VENV_DIR/bin/pytest"
