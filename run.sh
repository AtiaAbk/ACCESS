#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Locate virtualenv python
if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_EXEC="$SCRIPT_DIR/.venv/bin/python"
elif [ -x "$SCRIPT_DIR/ACCESS/.venv/bin/python" ]; then
    PYTHON_EXEC="$SCRIPT_DIR/ACCESS/.venv/bin/python"
elif [ -x "$SCRIPT_DIR/../ACCESS/.venv/bin/python" ]; then
    PYTHON_EXEC="$SCRIPT_DIR/../ACCESS/.venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

# Locate main.py
if [ -f "$SCRIPT_DIR/main.py" ]; then
    TARGET_DIR="$SCRIPT_DIR"
    MAIN_PY="$SCRIPT_DIR/main.py"
elif [ -f "$SCRIPT_DIR/ACCESS/main.py" ]; then
    TARGET_DIR="$SCRIPT_DIR/ACCESS"
    MAIN_PY="$SCRIPT_DIR/ACCESS/main.py"
else
    TARGET_DIR="$PWD"
    MAIN_PY="main.py"
fi

cd "$TARGET_DIR" || exit 1
exec "$PYTHON_EXEC" "$MAIN_PY" "$@"
