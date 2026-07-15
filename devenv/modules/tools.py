"""Development toolchain installed via native installers (not Homebrew).

uv and rustup are installed via their official installers (the canonical path
on macOS). Node.js is installed via fnm (a Homebrew formula from the packages
module). Each installer is idempotent and self-updates on re-run.

Skip the whole toolchain with `./setup.sh --skip tools`.
"""

from __future__ import annotations

import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from devenv.modules import Module


def install_uv(ctx) -> None:
    """uv — Python package/project manager (Astral native installer)."""
    if ctx.has_command("uv"):
        ctx.info("uv present — checking for updates...")
        ctx.run("uv", "self", "update", check=False)
        ctx.ok(f"uv up to date ({ctx.command_output('uv', '--version')})")
        return
    ctx.info("Installing uv...")
    ctx.run("bash", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh")
    ctx.ok("uv installed")


def install_rust(ctx) -> None:
    """Rust via rustup."""
    if ctx.has_command("rustup"):
        ctx.info("rustup present — updating toolchains...")
        ctx.run("rustup", "update", check=False)
        ctx.ok(f"Rust up to date ({ctx.command_output('rustc', '--version')})")
        return
    ctx.info("Installing Rust via rustup...")
    ctx.run(
        "bash", "-c",
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path",
    )
    ctx.ok("Rust installed")


def install_node_lts(ctx) -> None:
    """Node.js LTS via fnm (fnm comes from the packages module)."""
    if not ctx.has_command("fnm"):
        ctx.warn("fnm not found — skipping Node.js (ensure the packages module ran)")
        return
    ctx.info("Installing/updating Node.js LTS via fnm...")
    ctx.run("fnm", "install", "--lts", check=False)
    ctx.run("fnm", "default", "lts-latest", check=False)
    ctx.ok("Node.js LTS ready (via fnm)")


# Independent installers — run concurrently.
PARALLEL_TOOLS = [install_uv, install_rust]
# Serial: needs fnm from the packages module already on PATH.
SERIAL_TOOLS = [install_node_lts]


class ToolsModule(Module):
    name = "tools"
    description = "Dev toolchain: uv (Python), Rust (rustup), Node.js LTS (fnm)"
    order = 20

    def run(self, ctx) -> None:
        from devenv.core import _ParallelCtx

        lock = threading.Lock()
        ctx.info(f"Installing/updating {len(PARALLEL_TOOLS)} tools in parallel...")
        with ThreadPoolExecutor(max_workers=len(PARALLEL_TOOLS)) as pool:
            futures = {}
            for fn in PARALLEL_TOOLS:
                futures[pool.submit(fn, _ParallelCtx(ctx, lock))] = fn
            for future in as_completed(futures):
                fn = futures[future]
                try:
                    future.result()
                except Exception as exc:  # noqa: BLE001
                    ctx.warn(f"{fn.__doc__ or fn.__name__} failed: {exc}")

        for fn in SERIAL_TOOLS:
            try:
                fn(ctx)
            except subprocess.CalledProcessError as exc:
                ctx.warn(f"{fn.__doc__ or fn.__name__} failed: {exc}")
