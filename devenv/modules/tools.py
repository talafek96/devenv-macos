"""Development tools installed via their official installers (not Homebrew).

Currently uv (the Python package/project manager) and the Claude Code CLI.
Both ship canonical curl-based installers that self-update in place — the native
path, deliberately NOT `brew install`, so brew never pins or shadows them.
Idempotent: each self-updates on re-run. Skip with `./setup.sh --skip tools`.
"""

from __future__ import annotations

from devenv.modules import Module


class ToolsModule(Module):
    name = "tools"
    description = "Dev toolchain: uv (Python), Claude Code CLI (official installers)"
    order = 20

    def run(self, ctx) -> None:
        self._ensure_uv(ctx)
        self._ensure_claude_code(ctx)

    def _ensure_uv(self, ctx) -> None:
        if ctx.has_command("uv"):
            ctx.info("uv present — checking for updates...")
            ctx.run("uv", "self", "update", check=False)
            ctx.ok(f"uv up to date ({ctx.command_output('uv', '--version')})")
            return
        ctx.info("Installing uv (Astral installer)...")
        ctx.run("bash", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh")
        ctx.ok("uv installed")

    def _ensure_claude_code(self, ctx) -> None:
        if ctx.has_command("claude"):
            ctx.info("Claude Code present — running `claude update`...")
            ctx.run("claude", "update", check=False)
            ctx.ok(f"Claude Code up to date ({ctx.command_output('claude', '--version')})")
            return
        ctx.info("Installing Claude Code (official installer)...")
        ctx.run("bash", "-c", "curl -fsSL https://claude.ai/install.sh | bash")
        ctx.ok("Claude Code installed")
