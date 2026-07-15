"""macOS keyboard layer: Ghostty App-Support symlink, macOS defaults, and the
one-time GUI permission checklist that can't be scripted.

The Karabiner keymap, Ghostty config, and zellij config are deployed by the
dotfiles module (symlinks). This module handles the macOS-side pieces around
them and prints what still needs a manual click.
"""

from __future__ import annotations

from devenv.modules import Module

# ── macOS defaults (domain, key, type, value) ───────────────
# Each is a per-user `defaults write`. Several only take full effect after a
# logout/login (noted to the user at the end).
_DEFAULTS = [
    # Globe/fn key does nothing at the macOS level, so Karabiner owns globe->Ctrl.
    ("com.apple.HIToolbox", "AppleFnUsageType", "-int", "0"),
    # Natural scrolling ON (the known-good baseline for the keymap).
    ("NSGlobalDomain", "com.apple.swipescrolldirection", "-bool", "true"),
    # Key repeat instead of the accent-picker popover (essential for vim/coding).
    ("NSGlobalDomain", "ApplePressAndHoldEnabled", "-bool", "false"),
    # Fast key repeat.
    ("NSGlobalDomain", "KeyRepeat", "-int", "2"),
    ("NSGlobalDomain", "InitialKeyRepeat", "-int", "15"),
]

_GHOSTTY_APP_SUPPORT = "Library/Application Support/com.mitchellh.ghostty/config"

_PERMISSION_CHECKLIST = """\
  Karabiner-Elements (the keymap won't work until all three are done):
    1. Open Karabiner-Elements → approve the driver / system-extension prompt.
    2. System Settings → Privacy & Security → Input Monitoring   → enable Karabiner.
    3. System Settings → Privacy & Security → Accessibility        → enable Karabiner.
  AltTab:
    - Grant Accessibility on first launch.
    - Controls → set the Hold shortcut to Command (so your Alt = Command opens it).
  Rectangle:
    - Grant Accessibility on first launch.
  Maccy (clipboard history):
    - Grant Accessibility if you want it to paste directly.
"""


class KeybindsModule(Module):
    name = "keybinds"
    description = "macOS defaults, Ghostty symlink, and the GUI-permission checklist"
    order = 40

    def run(self, ctx) -> None:
        self._link_ghostty_app_support(ctx)
        self._apply_macos_defaults(ctx)
        self._print_checklist(ctx)

    # Ghostty reads ~/.config/ghostty/config, but the App-Support path is the
    # historical default — symlink it to the canonical file so both agree.
    def _link_ghostty_app_support(self, ctx) -> None:
        canonical = ctx.home_dir / ".config/ghostty/config"
        app_support = ctx.home_dir / _GHOSTTY_APP_SUPPORT
        if not canonical.exists():
            ctx.warn("~/.config/ghostty/config missing — run the dotfiles module first")
            return
        try:
            if app_support.is_symlink() and app_support.resolve() == canonical.resolve():
                ctx.ok("Ghostty App-Support config already linked")
                return
            app_support.parent.mkdir(parents=True, exist_ok=True)
            if app_support.exists() or app_support.is_symlink():
                app_support.unlink()
            app_support.symlink_to(canonical)
            ctx.ok(f"Linked {app_support} -> {canonical}")
        except OSError as exc:
            ctx.warn(f"Could not link Ghostty App-Support config: {exc}")

    def _apply_macos_defaults(self, ctx) -> None:
        for domain, key, vtype, value in _DEFAULTS:
            ctx.run("defaults", "write", domain, key, vtype, value, check=False)
        ctx.ok("Applied macOS defaults (globe=Do Nothing, natural scroll, key repeat)")
        ctx.info("Some of these take effect after the next logout/login.")

    def _print_checklist(self, ctx) -> None:
        ctx.header("Manual, one-time GUI permissions (cannot be scripted)")
        print(_PERMISSION_CHECKLIST)
