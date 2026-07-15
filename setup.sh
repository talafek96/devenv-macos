#!/usr/bin/env bash
# Thin bootstrap: ensure brew is on PATH + python3 exists, then hand off to Python.
# All real logic lives in setup.py and devenv/.
set -euo pipefail
DEVENV_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure Homebrew is on PATH (in case this is run in a shell without it sourced).
if ! command -v brew >/dev/null 2>&1; then
  if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)"
  else
    echo "ERROR: Homebrew is not installed. Run bootstrap.sh first, or install brew." >&2
    exit 1
  fi
fi

# macOS ships python3 via the Command Line Tools (installed with brew). Fall
# back to brew if somehow missing.
command -v python3 >/dev/null 2>&1 || brew install python

exec python3 "$DEVENV_DIR/setup.py" "$@"
