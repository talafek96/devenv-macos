"""Default Claude Code agents, skills, and commands (opt-in).

Symlinks the assets under ``devenv/assets/claude/`` into ``~/.claude/`` so a
fresh machine gets the same agent setup, and ``git pull`` keeps it current.

**Opt-in** via ``DEVENV_CLAUDE_ASSETS=1``. It is off by default because
``~/.claude/`` is a directory Claude Code owns and that users customize by
hand — nobody's agent setup should change out from under them because they ran
an unrelated setup step.

To opt back out, set the flag to ``uninstall`` (or ``remove`` / ``unlink``)::

    DEVENV_CLAUDE_ASSETS=uninstall ./setup.sh --only claude

Unsetting the flag is deliberately *not* the same as uninstalling: it stops
managing the assets and leaves them in place, matching the Karabiner keymap
convention. Removal has to be asked for explicitly, so a missing env var can
never silently tear down an agent setup.

Each asset is linked individually rather than linking the parent directories,
so hand-written agents and skills living alongside these keep working
untouched. Uninstall is symmetric: it only removes symlinks that point into
this repo's assets, and never touches a real file or a link pointing anywhere
else.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from devenv.core import CLAUDE_ASSETS_ENV, UNINSTALL_VALUES
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
        mode = ctx.claude_assets_mode

        if mode == "off":
            ctx.info(
                f"Skipping Claude Code assets (opt-in — set {CLAUDE_ASSETS_ENV}=1 "
                "to link the default agents, skills, and commands into ~/.claude, "
                f"or {CLAUDE_ASSETS_ENV}={UNINSTALL_VALUES[0]} to remove them)"
            )
            return

        src_root = ctx.assets_dir / "claude"
        if not src_root.is_dir():
            ctx.warn(f"No Claude assets found at {src_root} — nothing to do")
            return

        if mode == "uninstall":
            self._uninstall(ctx, src_root)
            return

        self._install(ctx, src_root)

    # ── install ─────────────────────────────────────────────

    def _install(self, ctx, src_root: Path) -> None:
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
        ctx.info(f"To opt out later: {CLAUDE_ASSETS_ENV}={UNINSTALL_VALUES[0]} "
                 "./setup.sh --only claude")

    # ── uninstall ───────────────────────────────────────────

    def _uninstall(self, ctx, src_root: Path) -> None:
        """Remove only the symlinks that point into this repo's assets."""
        dst_root = ctx.home_dir / CLAUDE_HOME
        if not dst_root.is_dir():
            ctx.ok(f"{dst_root} does not exist — nothing to remove")
            return

        removed = kept = failed = 0

        for kind in ASSET_KINDS:
            src_dir = src_root / kind
            dst_dir = dst_root / kind
            if not src_dir.is_dir() or not dst_dir.is_dir():
                continue

            for src in sorted(src_dir.iterdir()):
                if src.name.startswith("."):
                    continue
                dst = dst_dir / src.name

                if not dst.is_symlink():
                    if dst.exists():
                        # A real file/dir sits where our link used to — someone
                        # replaced it by hand. Theirs now; leave it.
                        ctx.warn(f"{dst} is not a symlink — leaving it alone")
                        kept += 1
                    continue

                # Only remove links we own. resolve() on a dangling link still
                # yields the target path, so a broken link into the repo is
                # cleaned up too.
                if dst.resolve() != src.resolve():
                    ctx.warn(f"{dst} points elsewhere — leaving it alone")
                    kept += 1
                    continue

                try:
                    dst.unlink()
                    ctx.ok(f"Removed {dst}")
                    removed += 1
                except OSError as exc:
                    ctx.err(f"Failed to remove {dst}: {exc}")
                    failed += 1

        ctx.ok(f"Claude assets: {removed} removed, {kept} left alone, {failed} failed")
        if failed:
            ctx.warn("Some assets failed to unlink — see errors above")
        ctx.info("Backups from the original install (if any) remain as "
                 "*.devenv-backup.* — restore or delete them by hand")
        ctx.info(f"To re-install: {CLAUDE_ASSETS_ENV}=1 ./setup.sh --only claude")

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
