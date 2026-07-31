"""Homebrew casks (GUI apps).

To add an app: append to CASKS. To remove one: delete the line.
Idempotent: install skips what's present, upgrade bumps outdated.

Note on updates: apps that update themselves (Chrome, VLC, WhatsApp, …) are
deliberately NOT force-upgraded here — brew leaves `auto_updates true` casks
alone unless `--greedy` is passed, which would needlessly re-download them.
They keep themselves current on their own.
"""

from devenv.modules import Module

# ── Cask list ───────────────────────────────────────────────
CASKS = [
    # Core Windows-feel / terminal setup
    "ghostty",              # GPU terminal
    "alt-tab",              # Windows-style Alt-Tab switcher
    "rectangle",            # window snapping
    "maccy",                # clipboard history manager
    # Dev
    "claude-code",          # Claude Code CLI (cask — brew keeps it updated)
    "visual-studio-code",   # VS Code editor (cask installs the `code` CLI too)
    # Personal / everyday
    "google-chrome",
    "whatsapp",
    "transmission",
    "vlc",
    "macdroid",             # Android <-> Mac file transfer
]

# Opt-in only (DEVENV_KARABINER=1): the keyboard remapper behind the
# Windows-feel keymap. Its installer prompts for your password.
_KARABINER_CASK = "karabiner-elements"


class CasksModule(Module):
    name = "casks"
    description = "Install/upgrade Homebrew casks (GUI apps)"
    order = 15

    def run(self, ctx) -> None:
        casks = list(CASKS)
        if ctx.karabiner_enabled:
            casks.append(_KARABINER_CASK)
            ctx.info("Karabiner keymap enabled (DEVENV_KARABINER) — including "
                     "karabiner-elements; it prompts for your password.")
        else:
            ctx.info("Karabiner keymap disabled — skipping karabiner-elements "
                     "(set DEVENV_KARABINER=1 to include it).")

        ctx.info(f"Installing {len(casks)} casks (skips any already present)...")
        ctx.run("brew", "install", "--cask", *casks, check=False)

        ctx.info("Upgrading any outdated casks (self-updating apps are left alone)...")
        ctx.run("brew", "upgrade", "--cask", *casks, check=False)

        installed = set(ctx.command_output("brew", "list", "--cask").split())
        missing = [c for c in casks if c not in installed]
        if missing:
            ctx.warn(f"Not installed (check names/availability): {', '.join(missing)}")
        ctx.ok(f"{len(casks) - len(missing)}/{len(casks)} casks present")
