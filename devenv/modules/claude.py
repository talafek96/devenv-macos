"""Default Claude Code agents, skills, and commands (opt-in).

Symlinks the assets under ``devenv/assets/claude/`` into ``~/.claude/`` so a
fresh machine gets the same agent setup, and ``git pull`` keeps it current.

**Opt-in** via ``DEVENV_CLAUDE_ASSETS=1``. It is off by default because
``~/.claude/`` is a directory Claude Code owns and that users customize by
hand — nobody's agent setup should change out from under them because they ran
an unrelated setup step.

Each asset is linked individually rather than linking the parent directories,
so hand-written agents and skills living alongside these keep working
untouched.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from devenv.core import CLAUDE_ASSETS_ENV
from devenv.modules import Module

# Where Claude Code looks for user-scoped assets.
CLAUDE_HOME = ".claude"

# Asset kind -> subdirectory under both assets/claude/ and ~/.claude/.
# Agents are single .md files; skills are directories; commands are .md files.
ASSET_KINDS: tuple[str, ...] = ("agents", "skills", "commands")


class ClaudeAssetsModule(Module):
    name = "claude"
    description = "Link default Claude Code agents/skills/commands into ~/.claude (opt-in)"
    order = 35  # after dotfiles (30), so ~/.claude ordering is predictable

    def run(self, ctx) -> None:
        if not ctx.claude_assets_enabled:
            ctx.info(
                f"Skipping Claude Code assets (opt-in — set {CLAUDE_ASSETS_ENV}=1 "
                "to link the default agents, skills, and commands into ~/.claude)"
            )
            return

        src_root = ctx.assets_dir / "claude"
        if not src_root.is_dir():
            ctx.warn(f"No Claude assets found at {src_root} — nothing to link")
            return

        dst_root = ctx.home_dir / CLAUDE_HOME
        linked = skipped = failed = 0

        for kind in ASSET_KINDS:
            src_dir = src_root / kind
            if not src_dir.is_dir():
                continue

            dst_dir = dst_root / kind
            dst_dir.mkdir(parents=True, exist_ok=True)

            for src in sorted(src_dir.iterdir()):
                if src.name.startswith("."):
                    continue
                result = self._link(ctx, src, dst_dir / src.name)
                if result is True:
                    linked += 1
                elif result is None:
                    skipped += 1
                else:
                    failed += 1

        ctx.ok(f"Claude assets: {linked} linked, {skipped} already current, {failed} failed")
        if failed:
            ctx.warn("Some assets failed to link — see errors above")
        ctx.info(f"Assets are symlinks into {src_root} — 'git pull' updates them in place")

    # ── linking ─────────────────────────────────────────────

    def _link(self, ctx, src: Path, dst: Path) -> bool | None:
        """Symlink src -> dst. True if linked, None if already current, False on error."""
        try:
            if dst.is_symlink() and dst.resolve() == src.resolve():
                return None

            if dst.exists() or dst.is_symlink():
                # Never clobber a hand-written agent or skill — back it up first,
                # same convention as the dotfiles module.
                stamp = datetime.now().strftime("%Y%m%d%H%M%S")
                backup = dst.with_name(f"{dst.name}.devenv-backup.{stamp}")
                ctx.warn(f"Backing up {dst} -> {backup}")
                dst.rename(backup)

            dst.symlink_to(src)
            ctx.ok(f"{dst} -> {src}")
            return True
        except OSError as exc:
            ctx.err(f"Failed to link {dst}: {exc}")
            return False
