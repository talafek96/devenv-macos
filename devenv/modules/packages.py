"""Homebrew formulae (CLI tools).

To add a package: append to FORMULAE. To remove one: delete the line.
Idempotent: `brew install` skips what's present; `brew upgrade` bumps what's
outdated. Safe to re-run.
"""

from devenv.modules import Module

# ── Formula list ────────────────────────────────────────────
FORMULAE = [
    # Core (already on this machine)
    "gh",         # GitHub CLI
    "zellij",     # terminal multiplexer
    "duti",       # set default apps for file types / URL schemes
    # QoL CLI tools (added by devenv-macos)
    "fzf",        # fuzzy finder — powers Ctrl-R / Ctrl-T / Alt-C in .zshrc
    "ripgrep",    # fast recursive grep (rg)
    "fd",         # fast, friendly find
    "bat",        # cat with syntax highlighting + git integration
    "eza",        # modern ls (icons, git status)
    "jq",         # JSON processor
    "tree",       # directory tree view
]


class PackagesModule(Module):
    name = "packages"
    description = "Install/upgrade Homebrew formulae (CLI tools)"
    order = 10

    def run(self, ctx) -> None:
        ctx.info("Updating Homebrew metadata...")
        ctx.run("brew", "update", check=False)

        ctx.info(f"Installing {len(FORMULAE)} formulae (skips any already present)...")
        ctx.run("brew", "install", *FORMULAE, check=False)

        ctx.info("Upgrading any outdated formulae...")
        ctx.run("brew", "upgrade", *FORMULAE, check=False)

        # Report what actually landed
        installed = set(ctx.command_output("brew", "list", "--formula").split())
        missing = [f for f in FORMULAE if f.split("/")[-1] not in installed]
        if missing:
            ctx.warn(f"Not installed (check names/availability): {', '.join(missing)}")
        ctx.ok(f"{len(FORMULAE) - len(missing)}/{len(FORMULAE)} formulae present")
