"""Dotfile symlinking, git config, and private config.

Symlinks are created from the repo's dotfiles/ into $HOME. The repo can live
anywhere — paths are resolved from the repo location at run time.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime

from devenv.modules import Module

# ── Dotfile map ─────────────────────────────────────────────
# Key:   path under dotfiles/   Value: target path in $HOME (with leading dot)
DOTFILES: dict[str, str] = {
    "zshrc": ".zshrc",
    "inputrc": ".inputrc",
    "config/zellij/config.kdl": ".config/zellij/config.kdl",
    "config/ghostty/config": ".config/ghostty/config",
    "config/karabiner/karabiner.json": ".config/karabiner/karabiner.json",
}

# ── Private config template ─────────────────────────────────
_ZSHRC_PRIVATE_TEMPLATE = """\
# ~/.zshrc_private — machine-specific, NOT tracked in devenv-macos.
# Sourced at the very end of ~/.zshrc. Edit freely.

# ── Aliases ─────────────────────────────────────────────────
# alias work-vpn='...'

# ── Functions ───────────────────────────────────────────────
# portforward() { ssh -L $1:localhost:$1 user@host; }

# ── Environment variables / API keys ───────────────────────
# export SOME_API_KEY='...'

# ── Conda / Mamba ───────────────────────────────────────────
# Paste the output of `conda init zsh` here if you use conda.

# ── GNU coreutils (optional) ────────────────────────────────
# If you `brew install coreutils` and prefer GNU ls/grep with LS_COLORS:
# alias ls='gls --color=auto'
# alias grep='ggrep --color=auto'

# ── zellij auto-attach (optional) ───────────────────────────
# if command -v zellij >/dev/null 2>&1 && [[ -z "$ZELLIJ" ]]; then
#     zellij attach main -c
# fi
"""

# ── Git config settings (applied via `git config --global`) ─
_GIT_SETTINGS: dict[str, str] = {
    "init.defaultBranch": "main",
    "core.editor": "vim",
    "core.autocrlf": "input",
    "core.pager": "less -FRX",
    "pull.rebase": "true",
    "push.default": "current",
    "push.autoSetupRemote": "true",
    "fetch.prune": "true",
    "diff.colorMoved": "default",
    "merge.conflictstyle": "diff3",
}

_GIT_ALIASES: dict[str, str] = {
    "alias.lg": "log --oneline --graph --decorate -20",
    "alias.st": "status -sb",
    "alias.co": "checkout",
    "alias.br": "branch",
    "alias.cm": "commit",
    "alias.last": "log -1 HEAD --stat",
    "alias.unstage": "reset HEAD --",
}


class DotfilesModule(Module):
    name = "dotfiles"
    description = "Symlink dotfiles, apply git config, create private config"
    order = 30

    def run(self, ctx) -> None:
        self._link_dotfiles(ctx)
        self._apply_gitconfig(ctx)
        self._create_private_config(ctx)

    # ── symlinks ────────────────────────────────────────────

    def _link_dotfiles(self, ctx) -> None:
        for src_name, dst_rel in DOTFILES.items():
            src = ctx.dotfiles_dir / src_name
            dst = ctx.home_dir / dst_rel

            if not src.exists():
                ctx.warn(f"Source not found: {src} — skipping")
                continue

            try:
                if dst.is_symlink() and dst.resolve() == src.resolve():
                    ctx.ok(f"{dst} -> {src} (already linked)")
                    continue

                if dst.exists() or dst.is_symlink():
                    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    backup = dst.with_name(f"{dst.name}.devenv-backup.{stamp}")
                    ctx.warn(f"Backing up {dst} -> {backup}")
                    dst.rename(backup)

                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.symlink_to(src)
                ctx.ok(f"{dst} -> {src}")
            except OSError as exc:
                ctx.err(f"Failed to link {dst}: {exc}")
                continue

    # ── git config ──────────────────────────────────────────

    def _apply_gitconfig(self, ctx) -> None:
        if not ctx.has_command("git"):
            ctx.warn("git not found — skipping git config")
            return

        for key, val in {**_GIT_SETTINGS, **_GIT_ALIASES}.items():
            subprocess.run(["git", "config", "--global", key, val], check=False)

        # gh credential helper. Use the resolved absolute path so git works from
        # GUI apps that don't inherit Homebrew's PATH.
        gh_path = ctx.command_output("which", "gh") or "gh"
        for host in ("https://github.com", "https://gist.github.com"):
            key = f"credential.{host}.helper"
            subprocess.run(["git", "config", "--global", "--unset-all", key],
                           check=False, capture_output=True)
            subprocess.run(["git", "config", "--global", "--add", key, ""], check=False)
            subprocess.run(["git", "config", "--global", "--add", key,
                            f"!{gh_path} auth git-credential"], check=False)

        # Prompt for name/email if missing (interactive terminals only).
        for key, prompt in [
            ("user.name", "Git user name: "),
            ("user.email", "Git email: "),
        ]:
            r = subprocess.run(["git", "config", "--global", key],
                               capture_output=True, text=True)
            if r.returncode != 0 or not r.stdout.strip():
                if os.isatty(0):
                    val = input(f"\n{prompt}").strip()
                    if val:
                        subprocess.run(["git", "config", "--global", key, val], check=False)
                else:
                    ctx.warn(f"git {key} not set (non-interactive — set manually)")

        name = subprocess.run(["git", "config", "--global", "user.name"],
                              capture_output=True, text=True).stdout.strip()
        ctx.ok(f"Git config applied (user: {name or '<not set>'})")

    # ── private config ──────────────────────────────────────

    def _create_private_config(self, ctx) -> None:
        path = ctx.home_dir / ".zshrc_private"
        if path.exists():
            ctx.ok(f"{path} already exists — skipping")
            return
        path.write_text(_ZSHRC_PRIVATE_TEMPLATE)
        ctx.ok(f"Created {path} (edit with your private config)")
