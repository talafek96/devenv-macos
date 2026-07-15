"""CLI: argument parsing and command dispatch."""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

from devenv.core import Context, C
from devenv.modules import Module, discover_modules


def _resolve_devenv_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def _run_modules(ctx: Context, modules: list[Module], args: argparse.Namespace) -> list[str]:
    """Run modules, return list of failed module names."""
    skip = set((args.skip or "").split(",")) - {""}
    only = set((args.only or "").split(",")) - {""}

    failed: list[str] = []
    for mod in modules:
        if mod.name in skip:
            ctx.info(f"Skipping {mod.name} (--skip)")
            continue
        if only and mod.name not in only:
            continue
        if not mod.enabled_by_default:
            continue

        ctx.header(f"{mod.name}: {mod.description}")
        try:
            mod.run(ctx)
        except subprocess.CalledProcessError as exc:
            ctx.err(f"Module {mod.name} failed: {exc}")
            ctx.warn("Continuing with remaining modules...")
            failed.append(mod.name)
        except Exception as exc:  # noqa: BLE001 — keep going, report at end
            ctx.err(f"Module {mod.name} crashed: {exc}")
            ctx.warn("Continuing with remaining modules...")
            failed.append(mod.name)

    return failed


# ── setup command ───────────────────────────────────────────

def cmd_setup(args: argparse.Namespace) -> None:
    devenv_dir = _resolve_devenv_dir()
    ctx = Context(devenv_dir)

    ctx.banner([
        "╔═══════════════════════════════════════╗",
        "║        devenv-macos setup             ║",
        "║  macOS Development Environment Setup   ║",
        "╚═══════════════════════════════════════╝",
    ])

    # Pre-flight
    ctx.header("Pre-flight checks")
    if platform.system() != "Darwin":
        ctx.err(f"This is the macOS devenv — detected {platform.system()}, not Darwin.")
        sys.exit(1)
    if not (devenv_dir / ".git").is_dir():
        ctx.err("Not a git repository. Clone the repo, then run ./setup.sh from inside it.")
        sys.exit(1)
    if not ctx.has_command("brew"):
        ctx.err("Homebrew not found on PATH. Run bootstrap.sh first.")
        sys.exit(1)

    mac_ver = platform.mac_ver()[0]
    ctx.info(f"Detected: macOS {mac_ver} ({platform.machine()}), brew at {ctx.brew_prefix}")
    ctx.ok("Pre-flight checks passed")

    modules = discover_modules()
    failed = _run_modules(ctx, modules, args)

    # Summary
    if failed:
        ctx.banner([
            "╔═══════════════════════════════════════╗",
            "║     Setup finished with errors        ║",
            "╚═══════════════════════════════════════╝",
        ])
        ctx.err(f"Failed modules: {', '.join(failed)}")
        ctx.info("Fix the issues and re-run — the setup is idempotent.")
    else:
        ctx.banner([
            "╔═══════════════════════════════════════╗",
            "║           Setup complete!             ║",
            "╚═══════════════════════════════════════╝",
        ])
    ctx.info(f"Dotfiles symlinked from {ctx.dotfiles_dir}/")
    ctx.info("Private shell config:  ~/.zshrc_private (not tracked)")
    ctx.info("Apply the shell now:   exec zsh")
    print()
    ctx.info("Some keyboard features need one-time GUI permission grants —")
    ctx.info("see the checklist printed by the 'keybinds' module above.")
    print()
    ctx.info(f"To update later: cd {devenv_dir} && git pull && ./setup.sh")

    if failed:
        sys.exit(1)


# ── list command ────────────────────────────────────────────

def cmd_list(_args: argparse.Namespace) -> None:
    modules = discover_modules()
    print(f"\n{C.BOLD}Available modules (in run order):{C.NC}\n")
    for mod in modules:
        tag = "" if mod.enabled_by_default else f" {C.YELLOW}[opt-in]{C.NC}"
        print(f"  {C.GREEN}{mod.name:<12s}{C.NC} {mod.description}{tag}")
    print()


# ── main ────────────────────────────────────────────────────

def _add_setup_flags(parser: argparse.ArgumentParser) -> None:
    modules = discover_modules()
    names = ", ".join(m.name for m in modules)
    parser.add_argument("--skip", metavar="MODULES",
                        help=f"Comma-separated modules to skip ({names})")
    parser.add_argument("--only", metavar="MODULES",
                        help=f"Comma-separated modules to run exclusively ({names})")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="devenv-macos",
        description="macOS development environment bootstrap",
        epilog="examples:\n"
               "  ./setup.sh                         # full setup (all modules)\n"
               "  ./setup.sh --only casks,dotfiles   # just GUI apps + symlink dotfiles\n"
               "  ./setup.sh --skip tools            # everything except the dev toolchain\n"
               "  ./setup.sh list                    # show available modules\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_setup_flags(parser)

    sub = parser.add_subparsers(dest="command")
    p_setup = sub.add_parser("setup", help="Run environment setup (default)")
    _add_setup_flags(p_setup)
    sub.add_parser("list", help="List available modules")

    args = parser.parse_args()

    if args.command is None or args.command == "setup":
        cmd_setup(args)
    elif args.command == "list":
        cmd_list(args)
