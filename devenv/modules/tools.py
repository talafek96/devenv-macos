"""Development tools installed via their official installers (not Homebrew).

Currently just uv — the Python package/project manager. The Astral installer is
the canonical macOS path (do not `brew install uv`). Idempotent: self-updates on
re-run. Skip with `./setup.sh --skip tools`.
"""

from __future__ import annotations

from devenv.modules import Module


class ToolsModule(Module):
    name = "tools"
    description = "Dev toolchain: uv (Python package/project manager)"
    order = 20

    def run(self, ctx) -> None:
        if ctx.has_command("uv"):
            ctx.info("uv present — checking for updates...")
            ctx.run("uv", "self", "update", check=False)
            ctx.ok(f"uv up to date ({ctx.command_output('uv', '--version')})")
            return
        ctx.info("Installing uv (Astral installer)...")
        ctx.run("bash", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh")
        ctx.ok("uv installed")
