#!/usr/bin/env bash
# devenv-macos bootstrap — one command on a fresh, out-of-the-box MacBook.
# Usage: bash <(curl -fsSL <raw-url-to-this-file>)
#
# Installs Homebrew (which also installs the Xcode Command Line Tools, so you
# get git), installs + authenticates gh, clones this repo at the latest release
# tag, then hands off to setup.sh.
set -euo pipefail

REPO="talafek96/devenv-macos"
# Where to clone. Location-agnostic: override with DEVENV_MACOS_DIR=/path to
# put it anywhere. The setup itself works from wherever the repo lives.
DEST="${DEVENV_MACOS_DIR:-$HOME/devenv-macos}"

# ── 1. Homebrew (also pulls in the Xcode Command Line Tools = git, etc.) ──
if ! command -v brew >/dev/null 2>&1; then
  echo "==> Installing Homebrew (you'll be asked for your password once)..."
  # NONINTERACTIVE skips the "press RETURN" prompt; the installer still asks
  # for sudo once and auto-installs the Command Line Tools.
  NONINTERACTIVE=1 /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Put brew on PATH for the rest of this script (Apple Silicon vs Intel).
if [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -x /usr/local/bin/brew ]; then
  eval "$(/usr/local/bin/brew shellenv)"
fi

# ── 2. gh (GitHub CLI) + auth ────────────────────────────────
command -v gh >/dev/null 2>&1 || brew install gh
gh auth status >/dev/null 2>&1 || gh auth login </dev/tty

# ── 3. Clone (or update) at the latest release tag ───────────
mkdir -p "$(dirname "$DEST")"   # ensure the parent dir exists on a fresh machine
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" fetch --tags --force --quiet
else
  gh repo clone "$REPO" "$DEST" -- --quiet
fi
TAG=$(git -C "$DEST" tag -l 'v*' | sort -V | tail -1)
[ -n "$TAG" ] && git -C "$DEST" checkout "$TAG" --quiet

# ── 4. Hand off to the real setup ────────────────────────────
exec "$DEST/setup.sh"
