#!/usr/bin/env python3
"""devenv-macos — development environment bootstrap entry point."""
import sys
from pathlib import Path

# Ensure the devenv package is importable from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from devenv.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
