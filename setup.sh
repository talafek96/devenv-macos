#!/usr/bin/env bash
# Thin bootstrap: ensure brew is on PATH + python3 exists, then hand off to Python.
# All real logic lives in setup.py and devenv/.
set -euo pipefail
DEVENV_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure Homebrew exists and is on PATH. On a fresh machine it isn't installed
# yet, so install it here too (same as bootstrap.sh) rather than bailing out;
# otherwise it's usually just missing from PATH in a shell that never sourced it.
if ! command -v brew >/dev/null 2>&1; then
  if [ ! -x /opt/homebrew/bin/brew ] && [ ! -x /usr/local/bin/brew ]; then
    echo "==> Homebrew not found — installing it (you'll be asked for your password once)..."
    # NONINTERACTIVE skips the "press RETURN" prompt; the installer still asks
    # for sudo once and auto-installs the Command Line Tools.
    NONINTERACTIVE=1 /bin/bash -c \
      "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
  if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)"
  else
    echo "ERROR: Homebrew install failed — install it manually from https://brew.sh and re-run." >&2
    exit 1
  fi
fi

# macOS ships python3 via the Command Line Tools (installed with brew). Fall
# back to brew if somehow missing.
command -v python3 >/dev/null 2>&1 || brew install python

# Put ~/.local/bin on PATH for the whole run so tools installed there during
# setup (e.g. uv, and the native `claude` CLI) are immediately usable by later
# steps and their subprocesses.
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) export PATH="$HOME/.local/bin:$PATH" ;;
esac

exec python3 "$DEVENV_DIR/setup.py" "$@"
