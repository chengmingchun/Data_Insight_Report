#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

VENV_PY=".venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
    echo "[setup] Creating Python virtual environment..."
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
    else
        echo "[error] Python 3.11 or newer was not found. Install Python and try again." >&2
        exit 1
    fi
    "$PYTHON_BIN" -m venv .venv
fi

if ! "$VENV_PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "[error] This project requires Python 3.11 or newer." >&2
    exit 1
fi

if ! "$VENV_PY" -c 'import streamlit, pandas, plotly, jinja2, pydantic, pydantic_settings, openai' >/dev/null 2>&1; then
    echo "[setup] Installing project dependencies..."
    "$VENV_PY" -m pip install -r requirements.txt
fi

echo "[start] Opening AI Data Insight Report at http://localhost:8501"
export PYTHONUTF8=1
exec "$VENV_PY" -m streamlit run app.py "$@"
