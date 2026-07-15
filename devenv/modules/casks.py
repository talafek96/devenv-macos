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
    "karabiner-elements",   # keyboard remapper (installer prompts for your password)
    "alt-tab",              # Windows-style Alt-Tab switcher
    "rectangle",            # window snapping
    "maccy",                # clipboard history manager
    # Dev
    "claude-code",          # Claude Code CLI (cask — brew keeps it updated)
    # Personal / everyday
    "google-chrome",
    "whatsapp",
    "transmission",
    "vlc",
    "macdroid",             # Android <-> Mac file transfer
]


class CasksModule(Module):
    name = "casks"
    description = "Install/upgrade Homebrew casks (GUI apps)"
    order = 15

    def run(self, ctx) -> None:
        ctx.info(f"Installing {len(CASKS)} casks (skips any already present)...")
        ctx.info("(karabiner-elements will prompt for your password during install.)")
        ctx.run("brew", "install", "--cask", *CASKS, check=False)

        ctx.info("Upgrading any outdated casks (self-updating apps are left alone)...")
        ctx.run("brew", "upgrade", "--cask", *CASKS, check=False)

        installed = set(ctx.command_output("brew", "list", "--cask").split())
        missing = [c for c in CASKS if c not in installed]
        if missing:
            ctx.warn(f"Not installed (check names/availability): {', '.join(missing)}")
        ctx.ok(f"{len(CASKS) - len(missing)}/{len(CASKS)} casks present")
