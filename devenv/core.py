"""Core utilities: Context, logging, command execution (macOS / Homebrew)."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from shutil import which


class _Colors:
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    BOLD = "\033[1m"
    NC = "\033[0m"


C = _Colors


class Context:
    """Shared state and helpers passed to every module."""

    def __init__(self, devenv_dir: Path, home_dir: Path | None = None) -> None:
        self.devenv_dir = devenv_dir
        self.home_dir = home_dir or Path.home()
        self.dotfiles_dir = devenv_dir / "dotfiles"
        self._brew_prefix: str | None = None

    # ── Homebrew ────────────────────────────────────────────

    @property
    def brew_prefix(self) -> str:
        if self._brew_prefix is None:
            self._brew_prefix = self.command_output("brew", "--prefix") or "/opt/homebrew"
        return self._brew_prefix

    # ── sudo (rarely needed on macOS; kept for the odd `defaults` call) ──

    @property
    def has_sudo(self) -> bool:
        if os.geteuid() == 0:
            return True
        try:
            r = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=5)
            return r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    # ── command execution ───────────────────────────────────

    def run(
        self,
        *args: str | Path,
        check: bool = True,
        capture: bool = False,
        env: dict[str, str] | None = None,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        cmd = [str(a) for a in args]
        merged_env = {**os.environ, **(env or {})}
        if capture:
            return subprocess.run(
                cmd, capture_output=True, text=True, check=check, env=merged_env, **kwargs
            )
        return subprocess.run(cmd, check=check, env=merged_env, **kwargs)

    def sudo(self, *args: str | Path, **kwargs) -> subprocess.CompletedProcess:
        if os.geteuid() == 0:
            return self.run(*args, **kwargs)
        return self.run("sudo", *args, **kwargs)

    def has_command(self, name: str) -> bool:
        return which(name) is not None

    def command_output(self, *args: str) -> str:
        """Run a command and return its stdout, stripped ('' on failure)."""
        try:
            r = self.run(*args, capture=True, check=False)
        except FileNotFoundError:
            return ""
        return r.stdout.strip() if r.returncode == 0 else ""

    # ── logging ─────────────────────────────────────────────

    def info(self, msg: str) -> None:
        print(f"{C.BLUE}[INFO]{C.NC}  {msg}")

    def ok(self, msg: str) -> None:
        print(f"{C.GREEN}[OK]{C.NC}    {msg}")

    def warn(self, msg: str) -> None:
        print(f"{C.YELLOW}[WARN]{C.NC}  {msg}")

    def err(self, msg: str) -> None:
        print(f"{C.RED}[ERR]{C.NC}   {msg}", file=sys.stderr)

    def header(self, msg: str) -> None:
        print(f"\n{C.BOLD}━━━ {msg} ━━━{C.NC}")

    def banner(self, lines: list[str]) -> None:
        print(f"{C.BOLD}")
        for line in lines:
            print(line)
        print(f"{C.NC}")


class _ParallelCtx:
    """Thin Context wrapper for parallel execution.

    Subprocess stdout is suppressed so concurrent installs don't interleave;
    log methods are serialized with a lock. Everything else delegates.
    """

    def __init__(self, ctx: Context, lock: threading.Lock) -> None:
        self._ctx = ctx
        self._lock = lock

    def run(
        self,
        *args: str | Path,
        check: bool = True,
        capture: bool = False,
        env: dict[str, str] | None = None,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        cmd = [str(a) for a in args]
        merged_env = {**os.environ, **(env or {})}
        if capture:
            return subprocess.run(
                cmd, capture_output=True, text=True, check=check, env=merged_env, **kwargs
            )
        return subprocess.run(
            cmd, check=check, env=merged_env,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, **kwargs,
        )

    def info(self, msg: str) -> None:
        with self._lock:
            self._ctx.info(msg)

    def ok(self, msg: str) -> None:
        with self._lock:
            self._ctx.ok(msg)

    def warn(self, msg: str) -> None:
        with self._lock:
            self._ctx.warn(msg)

    def err(self, msg: str) -> None:
        with self._lock:
            self._ctx.err(msg)

    def __getattr__(self, name):
        return getattr(self._ctx, name)
